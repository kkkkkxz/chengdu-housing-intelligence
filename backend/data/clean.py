import pandas as pd
import requests
import time
import json
from typing import Tuple, Optional
import logging
import os
import csv
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from pathlib import Path
import mimetypes
import sys
from typing import Optional, Tuple as TypeTuple


class AmapGeocoder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/geocode/geo"
        
    def get_coordinates(self, address: str, city: str = None) -> Tuple[Optional[float], Optional[float]]:
        """
        通过高德地图API获取地址的经纬度
        """
        params = {
            'key': self.api_key,
            'address': address,
            'output': 'json'
        }
        
        if city:
            params['city'] = city
            
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == '1' and data['geocodes']:
                location = data['geocodes'][0]['location']
                lng, lat = location.split(',')
                return float(lng), float(lat)
            else:
                logging.warning(f"地址解析失败: {address}, 城市: {city}, 响应: {data}")
                return None, None
                
        except Exception as e:
            logging.error(f"API请求失败: {address}, 错误: {str(e)}")
            return None, None


def process_property_data(input_file: str, output_file: str, api_key: str):
    """
    处理房产数据：先进行地址解析，然后进行数据清洗
    """
    print("开始处理房产数据...")
    
    # 读取原始CSV文件
    df = pd.read_csv(input_file)
    original_count = len(df)
    print(f"原始数据行数: {original_count}")
    
    # 第一步：进行地址解析获取经纬度
    print("开始地理编码（地址解析）...")
    geocoder = AmapGeocoder(api_key)
    
    # 添加经纬度列和状态列
    df['经度'] = None
    df['纬度'] = None
    df['地理编码状态'] = '未处理'
    
    # ============== 修复：增强空地址检测 ==============
    print("检查和处理地址字段...")
    
    # 处理缺失的地址或城市，确保转换为字符串类型
    df['地址'] = df['地址'].fillna('').astype(str)
    df['城市'] = df['城市'].fillna('').astype(str)
    
    # 记录清理前的数量
    before_address_clean = len(df)
    
    # 1. 删除真正为空的地址（空字符串或只包含空白字符）
    df = df[df['地址'].str.strip() != '']
    
    # 2. 删除地址为占位符的记录
    placeholder_keywords = [
        '暂无数据', '暂无', '待定', '未知', '无地址', 'null', 'none', '未填写',
        '无', '空', '没有', '不详', '未提供', '暂缺', 'not provided', 'unknown'
    ]
    
    # 创建一个布尔掩码，初始为False（表示保留所有行）
    mask = pd.Series(True, index=df.index)
    
    # 对于每个关键词，更新掩码（如果包含关键词则设为False）
    for keyword in placeholder_keywords:
        mask = mask & ~df['地址'].str.contains(keyword, case=False, na=False)
    
    # 应用掩码
    df = df[mask]
    
    # 3. 删除地址长度过短的记录（少于3个字符的地址可能是无效的）
    df = df[df['地址'].str.len() >= 3]
    
    # 4. 检查地址是否包含有效的汉字（至少包含2个汉字）
    def has_valid_chinese(text):
        if pd.isna(text) or text == '':
            return False
        chinese_count = sum(1 for char in str(text) if '\u4e00' <= char <= '\u9fff')
        return chinese_count >= 2
    
    df = df[df['地址'].apply(has_valid_chinese)]
    
    # 5. 检查地址是否包含数字和汉字组合（通常是有效的地址）
    def has_valid_address_pattern(text):
        text = str(text)
        has_digit = any(c.isdigit() for c in text)
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        return has_digit or has_chinese
    
    df = df[df['地址'].apply(has_valid_address_pattern)]
    
    print(f"清理无效地址前数据行数: {before_address_clean}")
    print(f"清理无效地址后数据行数: {len(df)}")
    print(f"删除了 {before_address_clean - len(df)} 条无效地址记录")
    # =================================================
    
    # 遍历每一行数据获取经纬度
    print("开始地址解析，获取经纬度...")
    processed_count = 0
    failed_addresses = []  # 记录解析失败的地址
    
    for index, row in df.iterrows():
        address = row['地址'].strip()
        city = row['城市'].strip()
        
        processed_count += 1
        if processed_count % 100 == 0:
            print(f"已处理 {processed_count}/{len(df)} 条数据...")
        
        # 获取经纬度
        lng, lat = geocoder.get_coordinates(address, city if city else None)
        
        if lng and lat:
            df.at[index, '经度'] = lng
            df.at[index, '纬度'] = lat
            df.at[index, '地理编码状态'] = '成功'
        else:
            df.at[index, '地理编码状态'] = '失败'
            failed_addresses.append(f"{city} - {address}")
        
        # 添加延时，避免API频率限制
        time.sleep(0.2)
    
    # 第二步：根据地址解析结果进行数据清洗
    print("\n开始数据清洗...")
    
    # 1. 删除地址解析失败的记录
    before_geo_count = len(df)
    df = df[df['地理编码状态'] == '成功']
    after_geo_count = len(df)
    print(f"地址解析结果: 成功 {after_geo_count} 条，失败 {before_geo_count - after_geo_count} 条")
    
    if failed_addresses:
        print(f"前10个解析失败的地址:")
        for addr in failed_addresses[:10]:
            print(f"  - {addr}")
    
    # 2. 删除重复项（基于链接）
    before_dedup_count = len(df)
    df = df.drop_duplicates(subset='链接')
    after_dedup_count = len(df)
    print(f"去重结果: 删除了 {before_dedup_count - after_dedup_count} 条重复记录")
    
    # 3. 删除重要字段缺失的行
    required_columns = ['地址', '城市', '价格', '面积']
    for col in required_columns:
        before_count = len(df)
        df = df.dropna(subset=[col])
        after_count = len(df)
        if after_count < before_count:
            print(f"删除缺失 {col} 的记录: {before_count - after_count} 条")
    
    # 4. 删除建筑类型为"暂无数据"的行
    before_count = len(df)
    if '建筑类型' in df.columns:
        df = df[~df['建筑类型'].astype(str).str.contains('暂无数据')]
        print(f"删除'暂无数据'的建筑类型: {before_count - len(df)} 条")
    
    # 5. 清理数据格式
    print("清理数据格式...")
    
    # 清理均价列
    if '均价' in df.columns:
        df['均价'] = df['均价'].astype(str).replace('元/平', '', regex=True)
        # 尝试转换为数值，转换失败的值设为NaN
        df['均价'] = pd.to_numeric(df['均价'], errors='coerce')
    
    # 清理价格列
    if '价格' in df.columns:
        df['价格'] = df['价格'].astype(str).replace('万', '', regex=True)
        df['价格'] = pd.to_numeric(df['价格'], errors='coerce')
        # 删除价格为0或负数的异常记录
        df = df[(df['价格'] > 0) & (df['价格'] < 100000)]  # 假设价格在0-10亿之间
    
    # 清理面积列
    if '面积' in df.columns:
        df['面积'] = df['面积'].astype(str).replace('平米', '', regex=True)
        df['面积'] = pd.to_numeric(df['面积'], errors='coerce')
        # 删除面积异常小的记录（小于10平米）
        df = df[df['面积'] >= 10]
    
    # 6. 添加带单位的列
    print("添加带单位的列...")
    if '价格' in df.columns:
        df['价格(万)'] = df['价格'].apply(lambda x: f"{x}万" if pd.notnull(x) else "")
    if '均价' in df.columns:
        df['均价(元/平)'] = df['均价'].apply(lambda x: f"{x}元/平" if pd.notnull(x) else "")
    if '面积' in df.columns:
        df['面积(平米)'] = df['面积'].apply(lambda x: f"{x}平米" if pd.notnull(x) else "")
    
    cleaned_count = len(df)
    print(f"\n清洗完成结果:")
    print(f"  原始数据: {original_count} 条")
    print(f"  最终数据: {cleaned_count} 条")
    print(f"  总共删除: {original_count - cleaned_count} 条记录")
    
    # 保存结果
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"数据处理完成，生成文件: {output_file}")
    
    return df


# ================================
# 图片下载相关函数
# ================================

def sanitize_city(name: str) -> str:
    if not name:
        return "unknown"
    # 保留中文、字母、数字、下划线、短横线
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in name)


def ext_from_url_or_ct(url: str, content_type: Optional[str]) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext and len(ext) <= 8:
        return ext
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(';')[0].strip())
        if ext:
            return ext
    return ".jpg"


def download_image(url: str, dest: Path, retries=3, timeout=10) -> TypeTuple[bool, str]:
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            if resp.status_code == 200:
                ct = resp.headers.get('Content-Type')
                ext = ext_from_url_or_ct(url, ct)
                # 如果 dest 没有扩展名，加入 ext
                if dest.suffix == "":
                    dest = dest.with_suffix(ext)
                with open(dest, 'wb') as f:
                    for chunk in resp.iter_content(1024 * 8):
                        if chunk:
                            f.write(chunk)
                return True, str(dest)
            else:
                last_exc = f'status:{resp.status_code}'
        except Exception as e:
            last_exc = str(e)
        time.sleep(0.5 * attempt)
    return False, last_exc or 'unknown'


def make_filename_from_url(url: str, idx: Optional[int] = None) -> str:
    h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]
    base = h
    if idx is not None:
        base = f"{h}_{idx}"
    # try to preserve original ext if present
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext and len(ext) <= 8:
        return base + ext
    return base + ".jpg"


def process_row(row_idx, row, image_col, city_col, outdir: Path):
    try:
        city = sanitize_city(row.get(city_col, '') or '')
        images_field = (row.get(image_col, '') or '').strip()
        if not images_field:
            return None
        # 支持分号或逗号分割多个图片
        parts = [p.strip() for p in images_field.replace('\n', ',').replace(';', ',').split(',') if p.strip()]
        saved_paths = []
        city_dir = outdir / city
        city_dir.mkdir(parents=True, exist_ok=True)
        for i, url in enumerate(parts, start=1):
            try:
                fname = make_filename_from_url(url, i if len(parts) > 1 else None)
                dest = city_dir / fname
                if dest.exists() and dest.stat().st_size > 0:
                    saved_paths.append(str(dest))
                    continue
                ok, info = download_image(url, dest)
                if ok:
                    saved_paths.append(str(info))
                else:
                    saved_paths.append(f"ERROR:{info}")
            except Exception as e:
                saved_paths.append(f"ERROR:{e}")
        return ";".join(saved_paths)
    except Exception as e:
        return f"ROW_ERROR:{e}"


def download_images_from_csv(csv_path: str, outdir: str, workers: int = 8, limit: int = 0) -> str:
    """
    从CSV下载图片的主要函数，返回处理后的CSV文件路径
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print('CSV 文件不存在:', csv_path, file=sys.stderr)
        sys.exit(2)

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 读取 CSV
    df = pd.read_csv(csv_path)
    total_records = len(df)
    print(f"读取到 {total_records} 条记录")
    
    if limit and limit > 0 and limit < total_records:
        df = df.head(limit)
        total_records = limit
    
    # 查找图片列和城市列
    image_col = None
    city_col = None
    for col in df.columns:
        if '图片' in col or '图' in col or 'image' in col.lower():
            image_col = col
        if '城市' in col or 'city' in col.lower():
            city_col = col
    
    if not image_col:
        print('未能识别图片列（含关键字 图片/图/image）', file=sys.stderr)
        # 尝试查找其他可能的列名
        for col in df.columns:
            if '链接' in col and col != '链接':
                image_col = col
                print(f"使用列 '{image_col}' 作为图片列")
                break
    
    if not image_col:
        print('未找到图片列', file=sys.stderr)
        sys.exit(3)
        
    if not city_col:
        print('未能识别城市列（含关键字 城市/city），将使用 unknown', file=sys.stderr)
        city_col = '城市'  # 使用默认值

    # 准备行数据
    rows = df.to_dict('records')
    total = len(rows)

    print(f'准备下载 {total} 条记录的图片（并行 {workers}）到 {outdir}')

    results = [None] * total  # 预分配结果列表
    
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {}
        for idx, row in enumerate(rows):
            futures[ex.submit(process_row, idx, row, image_col, city_col, outdir)] = idx
        
        completed = 0
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                res = fut.result()
            except Exception as e:
                res = f'ERROR:{e}'
            results[idx] = res
            completed += 1
            
            if completed % 50 == 0 or completed == total:
                print(f'已处理 {completed}/{total}')

    # 将结果添加到DataFrame中
    df['本地图片路径'] = results
    
    # 保存处理后的CSV
    output_csv_path = csv_path.with_name(csv_path.stem + '_with_images' + csv_path.suffix)
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    
    print(f'完成。处理后的文件已保存到: {output_csv_path}')
    return str(output_csv_path)


def create_final_dataframe(processed_df: pd.DataFrame) -> pd.DataFrame:
    """
    创建最终数据框，进行过滤和列重排
    """
    print("创建最终数据框...")
    
    # 首先检查数据是否包含必要的列
    required_columns = ['经度', '纬度', '本地图片路径']
    for col in required_columns:
        if col not in processed_df.columns:
            print(f"警告: 缺少必要列 '{col}'")
    
    # 过滤条件：必须同时有经纬度和本地图片路径
    # 先标记需要过滤的行
    original_count = len(processed_df)
    
    # 标记无经纬度的行
    no_coordinates = processed_df['经度'].isna() | processed_df['纬度'].isna()
    
    # 标记无图片路径或图片路径包含ERROR的行
    no_images = (processed_df['本地图片路径'].isna()) | (processed_df['本地图片路径'].str.contains('ERROR', na=True))
    
    # 组合过滤条件：有经纬度 AND 有图片路径
    mask = (~no_coordinates) & (~no_images)
    
    # 应用过滤
    final_df = processed_df[mask].copy()
    filtered_count = original_count - len(final_df)
    
    print(f"过滤前数据条数: {original_count}")
    print(f"过滤后数据条数: {len(final_df)}")
    print(f"过滤掉 {filtered_count} 条记录")
    print(f"过滤原因统计:")
    print(f"  - 无经纬度: {no_coordinates.sum()} 条")
    print(f"  - 无图片或图片错误: {no_images.sum()} 条")
    print(f"  - 同时无经纬度和无图片: {(no_coordinates & no_images).sum()} 条")
    
    # 定义列顺序：原始列 + 带单位的列 + 新增列
    base_columns = [
        '城市', '标题', '价格(万)', '均价(元/平)', '链接', '关注人数', '标签',
        '户型', '面积(平米)', '朝向', '装修', '楼层', '建筑类型', 
        '地址', '图片链接', '区域'
    ]
    
    # 检查所有需要的列是否都存在
    for col in base_columns:
        if col not in final_df.columns:
            print(f"警告: 缺少列 '{col}'，尝试查找替代列")
            # 尝试查找替代列名
            for df_col in final_df.columns:
                if col in df_col or df_col in col:
                    print(f"  使用 '{df_col}' 替代 '{col}'")
                    # 这里我们不做重命名，只是提醒
    
    # 新增的列
    new_columns = ['经度', '纬度', '本地图片路径']
    
    # 先获取所有实际存在的列
    all_columns = list(final_df.columns)
    
    # 定义优先顺序：基础列 -> 数值列 -> 新增列 -> 其他列
    ordered_columns = []
    
    # 添加基础列（如果存在）
    for col in base_columns:
        if col in all_columns:
            ordered_columns.append(col)
    
    # 添加数值列（如果存在且不在已添加的列中）
    numeric_columns = ['价格', '均价', '面积']
    for col in numeric_columns:
        if col in all_columns and col not in ordered_columns:
            ordered_columns.append(col)
    
    # 添加新增列
    for col in new_columns:
        if col in all_columns:
            ordered_columns.append(col)
    
    # 添加其他列（如果有）
    for col in all_columns:
        if col not in ordered_columns:
            ordered_columns.append(col)
    
    # 重新排列列顺序
    final_df = final_df[ordered_columns]
    
    return final_df


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,  # 降低日志级别，减少输出
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('processing.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 高德地图API Key (请确保这是有效的)
    # 从环境变量读取高德地图密钥，避免将凭据写入源码。
    API_KEY = os.getenv('AMAP_API_KEY', '')
    if not API_KEY:
        raise RuntimeError('缺少 AMAP_API_KEY 环境变量，无法执行地理编码。')
    
    # 第一步：处理房产数据（先地址解析，再数据清洗）
    print("=" * 50)
    print("第一步：处理房产数据（地址解析 + 数据清洗）")
    print("=" * 50)
    try:
        processed_data = process_property_data('二手房.csv', 'processed_data.csv', API_KEY)
        print(f"第一步完成，生成了 {len(processed_data)} 条记录")
    except Exception as e:
        print(f"处理房产数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 第二步：下载图片并添加本地路径
    print("\n" + "=" * 50)
    print("第二步：下载图片")
    print("=" * 50)
    try:
        final_csv_path = download_images_from_csv(
            'processed_data.csv',
            'media/listings',  # 图片将按城市分别存储在这个目录下
            workers=8,
            limit=0  # 0表示处理所有记录
        )
    except Exception as e:
        print(f"下载图片时出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 第三步：读取处理后的数据，进行过滤和整理
    print("\n" + "=" * 50)
    print("第三步：生成最终文件")
    print("=" * 50)
    
    try:
        # 读取处理后的数据
        processed_df = pd.read_csv(final_csv_path)
        
        # 创建最终数据框（过滤和列重排）
        final_df = create_final_dataframe(processed_df)
        
        # 保存最终文件
        final_output_path = 'clean.csv'
        final_df.to_csv(final_output_path, index=False, encoding='utf-8-sig')
        
        # 统计信息
        print(f"\n所有处理完成！")
        print(f"最终文件已保存为: {final_output_path}")
        print(f"最终数据统计:")
        print(f"  总记录数: {len(final_df)}")
        print(f"  成功获取经纬度的记录数: {(final_df['经度'].notna() & final_df['纬度'].notna()).sum()}")
        print(f"  包含本地图片的记录数: {final_df['本地图片路径'].notna().sum()}")
        
        # 显示前几行数据预览
        print("\n数据预览 (前3行):")
        print(final_df.head(3).to_string(index=False))
        
        # 显示最终列顺序
        print("\n最终列顺序:")
        for i, col in enumerate(final_df.columns, 1):
            print(f"  {i:2d}. {col}")
            
    except Exception as e:
        print(f"生成最终文件时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
