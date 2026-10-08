import pandas as pd
import re
from typing import Tuple
from datetime import datetime
from sqlalchemy import create_engine, text
from pathlib import Path


def parse_price(value: str) -> float:
    if pd.isna(value):
        return 0.0
    s = str(value)
    s = s.replace(',', '').replace('万', '').replace('元/平', '').strip()
    try:
        return float(s)
    except Exception:
        # 提取数字
        m = re.search(r"\d+(?:\.\d+)?", s)
        return float(m.group()) if m else 0.0


def parse_area(value: str) -> float:
    if pd.isna(value):
        return 0.0
    s = str(value).replace('㎡', '').replace('平米', '').replace('平方米', '').replace(',', '').strip()
    try:
        return float(s)
    except Exception:
        m = re.search(r"\d+(?:\.\d+)?", s)
        return float(m.group()) if m else 0.0


def parse_house_type(value: str) -> Tuple[int, int]:
    """从形如 '2室2厅1厨1卫' 或 '3室2厅' 中解析出 (rooms, halls)"""
    if pd.isna(value):
        return 0, 0
    s = str(value)
    rm = re.search(r'(\d+)\s*室', s)
    hl = re.search(r'(\d+)\s*厅', s)
    rooms = int(rm.group(1)) if rm else 0
    halls = int(hl.group(1)) if hl else 0
    return rooms, halls


def load_and_clean_csv(csv_path: Path) -> pd.DataFrame:
    print(f"正在读取文件: {csv_path}")
    
    # 读取 CSV（尝试 utf-8-sig，因为之前保存时用了这个编码）
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
    except Exception as e1:
        print(f"utf-8-sig 读取失败: {e1}，尝试 utf-8...")
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
        except Exception as e2:
            print(f"utf-8 读取失败: {e2}，尝试 gbk...")
            try:
                df = pd.read_csv(csv_path, encoding='gbk')
            except Exception as e3:
                print(f"所有编码尝试失败: {e3}")
                raise

    print(f"读取到 {len(df)} 条记录，{len(df.columns)} 列")
    
    # 显示列信息
    print("\n原始列信息:")
    for i, col in enumerate(df.columns, 1):
        sample = str(df[col].iloc[0]) if len(df) > 0 else "空"
        if len(sample) > 50:
            sample = sample[:50] + "..."
        print(f"  {i:2d}. {col} - 示例: {sample}")
    
    # 删除'地理编码状态'列
    if '地理编码状态' in df.columns:
        df = df.drop(columns=['地理编码状态'])
        print("\n已删除 '地理编码状态' 列")
    
    # 重命名列：中文列名 -> 英文列名
    column_mapping = {
        '城市': 'city',
        '标题': 'title', 
        '价格': 'price',
        '均价': 'avg_price',
        '链接': 'href',
        '关注人数': 'follow',
        '标签': 'tags',
        '户型': 'house_type',
        '面积': 'area',
        '朝向': 'orientation',
        '装修': 'decorate',
        '楼层': 'floor',
        '建筑类型': 'building_type',
        '地址': 'address',
        '图片链接': 'img_url',
        '区域': 'district',
        '价格(万)': 'price_with_unit',
        '面积(平米)': 'area_with_unit',
        '均价(元/平)': 'avg_price_with_unit',
        '经度': 'longitude',
        '纬度': 'latitude'
    }
    
    # 应用列名映射
    rename_dict = {}
    for cn_name, en_name in column_mapping.items():
        if cn_name in df.columns:
            rename_dict[cn_name] = en_name
            print(f"映射列: {cn_name} -> {en_name}")
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
    else:
        # 如果列名已经是英文，则不需要重命名
        print("列名已为英文，无需重命名")
    
    print(f"\n重命名后的列 ({len(df.columns)}列):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # 解析数值字段
    print("\n正在解析数值字段...")
    
    # 使用带单位的列解析总价
    if 'price_with_unit' in df.columns:
        df['total_price'] = df['price_with_unit'].apply(lambda x: parse_price(str(x)) if pd.notna(x) else 0.0)
    elif 'price' in df.columns:
        df['total_price'] = df['price'].apply(lambda x: parse_price(str(x)) if pd.notna(x) else 0.0)
    else:
        df['total_price'] = 0.0
    
    # 使用带单位的列解析均价
    if 'avg_price_with_unit' in df.columns:
        df['unit_price'] = df['avg_price_with_unit'].apply(lambda x: parse_price(str(x)) if pd.notna(x) else None)
    elif 'avg_price' in df.columns:
        df['unit_price'] = df['avg_price'].apply(lambda x: parse_price(str(x)) if pd.notna(x) else None)
    else:
        df['unit_price'] = None
    
    # 使用带单位的列解析面积
    if 'area_with_unit' in df.columns:
        df['area_parsed'] = df['area_with_unit'].apply(lambda x: parse_area(str(x)) if pd.notna(x) else 0.0)
    elif 'area' in df.columns:
        df['area_parsed'] = df['area'].apply(lambda x: parse_area(str(x)) if pd.notna(x) else 0.0)
    else:
        df['area_parsed'] = 0.0
    
    # 解析户型
    if 'house_type' in df.columns:
        rooms_halls = df['house_type'].fillna('').apply(parse_house_type)
        if len(rooms_halls) > 0:
            rooms, halls = zip(*rooms_halls)
        else:
            rooms, halls = ([0] * len(df), [0] * len(df))
        df['rooms'] = list(rooms)
        df['halls'] = list(halls)
    else:
        df['rooms'] = 0
        df['halls'] = 0
    
    # 解析关注人数
    if 'follow' in df.columns:
        df['followers'] = pd.to_numeric(df['follow'], errors='coerce').fillna(0).astype(int)
    else:
        df['followers'] = 0
    
    # 创建最终数据框，按照数据库表字段顺序
    print("\n正在创建最终数据框...")
    
    # 设置默认值函数
    def get_column(col_name, default=None):
        if col_name in df.columns:
            return df[col_name]
        else:
            return pd.Series([default] * len(df))
    
    # 创建最终数据框，对应数据库字段
    out = pd.DataFrame({
        'title': get_column('title', ''),
        'city': get_column('city', ''),
        'district': get_column('district', ''),
        'community': get_column('address', ''),  # 使用地址作为小区名
        'address': get_column('address', ''),
        'total_price': df['total_price'],
        'unit_price': df['unit_price'],
        'area': df['area_parsed'],
        'rooms': df['rooms'],
        'halls': df['halls'],
        'orientation': get_column('orientation', ''),
        'floor': get_column('floor', ''),
        'decorate': get_column('decorate', ''),
        'building_type': get_column('building_type', ''),
        'followers': df['followers'],
        'link': get_column('href', ''),
        'cover': get_column('img_url', ''),
        'tags': get_column('tags', ''),
        'longitude': pd.to_numeric(get_column('longitude'), errors='coerce'),
        'latitude': pd.to_numeric(get_column('latitude'), errors='coerce'),
        # 注意：clean.csv没有本地图片路径，所以这里设为空
        'local_image_path': pd.Series([None] * len(df)),
    })
    
    # 数据清洗和验证
    print("\n正在清洗和验证数据...")
    
    # 检查必需字段
    required_fields = ['city', 'address', 'longitude', 'latitude']
    for field in required_fields:
        missing = out[field].isna().sum()
        if missing > 0:
            print(f"警告: {field} 有 {missing} 个空值")
    
    # 删除重复记录（基于标题、城市和地址）
    before_dedup = len(out)
    out = out.drop_duplicates(subset=['title', 'city', 'address'])
    after_dedup = len(out)
    print(f"去重: {before_dedup} -> {after_dedup} 条记录")
    
    # 过滤掉无经纬度的记录
    before_filter = len(out)
    out = out[out['longitude'].notna() & out['latitude'].notna()]
    after_filter = len(out)
    print(f"过滤无经纬度记录: {before_filter} -> {after_filter} 条记录")
    
    # 过滤掉异常价格和面积的记录
    valid_price = (out['total_price'] > 0) & (out['total_price'] < 100000)  # 价格在0-10亿之间
    valid_area = (out['area'] > 10) & (out['area'] < 1000)  # 面积在10-1000平米之间
    out = out[valid_price & valid_area]
    print(f"过滤异常价格和面积: {after_filter} -> {len(out)} 条记录")
    
    # 添加时间戳
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    out['created_at'] = now_str
    out['updated_at'] = now_str
    
    print(f"\n最终数据框: {len(out)} 条记录, {len(out.columns)} 列")
    return out


def delete_existing_data(engine):
    """删除数据库中已有的数据（处理外键约束）"""
    try:
        with engine.connect() as conn:
            # 1. 禁用外键约束
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
            
            # 2. 删除 house 表数据
            result = conn.execute(text("DELETE FROM house"))
            conn.commit()
            
            # 3. 重置自增ID
            conn.execute(text("ALTER TABLE house AUTO_INCREMENT = 1"))
            conn.commit()
            
            # 4. 重新启用外键约束
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
            
            print(f"已删除 {result.rowcount} 条现有记录")
            return True
    except Exception as e:
        print(f"删除数据时出错: {e}")
        # 尝试重新启用外键约束
        try:
            with engine.connect() as conn:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                conn.commit()
        except:
            pass
        return False


def import_to_database(df, engine, table_name='house'):
    """将数据导入数据库"""
    try:
        print(f"\n正在导入数据到 {table_name} 表...")
        
        # 确保列的顺序与数据库表一致
        db_columns = [
            'title', 'city', 'district', 'community', 'address', 
            'total_price', 'unit_price', 'area', 'rooms', 'halls',
            'orientation', 'floor', 'decorate', 'building_type', 
            'followers', 'link', 'cover', 'tags', 'created_at', 
            'updated_at', 'longitude', 'latitude', 'local_image_path'
        ]
        
        # 检查数据框列
        print(f"数据框列 ({len(df.columns)}个): {', '.join(df.columns.tolist())}")
        
        # 确保数据框只包含数据库表中存在的列
        df_to_import = df[[col for col in db_columns if col in df.columns]].copy()
        
        # 检查是否有缺失的必需字段
        for col in db_columns:
            if col not in df_to_import.columns:
                print(f"警告: 数据库字段 '{col}' 不在数据框中")
                # 添加默认值
                if col in ['created_at', 'updated_at']:
                    df_to_import[col] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    df_to_import[col] = None
        
        # 导入数据
        df_to_import.to_sql(
            table_name, 
            engine, 
            if_exists='append', 
            index=False, 
            chunksize=500
        )
        
        print(f'导入完成: {len(df_to_import)} 条记录写入 {table_name} 表')
        return True
        
    except Exception as e:
        print(f"导入数据时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    # 数据库配置
    DB_URL = 'mysql+pymysql://root:876995@localhost:3306/second_house_analysis?charset=utf8mb4'
    
    # 输入文件路径
    csv_path = Path('data\\clean.csv')
    
    if not csv_path.exists():
        print(f"错误: 找不到文件 {csv_path}")
        print("请确保 clean.csv 文件在当前目录下")
        return
    
    # 1. 加载和清理CSV
    print("=" * 60)
    print("步骤1: 加载和清理CSV数据")
    print("=" * 60)
    
    try:
        df = load_and_clean_csv(csv_path)
    except Exception as e:
        print(f"加载CSV失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 保存清理后的CSV
    cleaned_csv_path = csv_path.with_name(csv_path.stem + '_cleaned' + csv_path.suffix)
    df.to_csv(cleaned_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n清理后的数据已保存到: {cleaned_csv_path}")
    
    # 显示数据预览
    print("\n数据预览 (前3行):")
    print(df.head(3).to_string(index=False, max_colwidth=30))
    
    print(f"\n最终列顺序 ({len(df.columns)}列):")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    # 2. 连接数据库
    print("\n" + "=" * 60)
    print("步骤2: 数据库操作")
    print("=" * 60)
    
    try:
        engine = create_engine(DB_URL)
        
        # 测试连接
        with engine.connect() as conn:
            print("数据库连接成功!")
        
        # 询问确认
        print("\n警告：这将删除数据库中 house 表的所有现有数据！")
        confirm = input("确定要继续吗？(输入 'yes' 确认): ").strip().lower()
        
        if confirm != 'yes':
            print("操作已取消。")
            return
        
        # 3. 删除现有数据
        print("\n正在删除现有数据...")
        if not delete_existing_data(engine):
            print("删除数据失败，操作已中止。")
            return
        
        # 4. 导入新数据
        print("\n正在导入数据...")
        if import_to_database(df, engine):
            print("\n" + "=" * 60)
            print("导入成功完成!")
            print("=" * 60)
            print(f"总共导入 {len(df)} 条记录到数据库")
            
            # 显示统计信息
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as count FROM house"))
                count = result.fetchone()[0]
                print(f"数据库中的总记录数: {count}")
                
                # 显示各城市记录数
                result = conn.execute(text("SELECT city, COUNT(*) as count FROM house GROUP BY city ORDER BY count DESC"))
                print("\n各城市记录分布:")
                for row in result:
                    print(f"  {row[0]}: {row[1]} 条")
        
        else:
            print("\n导入失败!")
            
    except Exception as e:
        print(f"数据库操作失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"\n数据已保存为CSV文件，可以手动导入数据库:")
        print(f"CSV文件路径: {cleaned_csv_path}")


if __name__ == '__main__':
    main()