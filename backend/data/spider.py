import csv
import random
import time
import os  # 导入 os 库
from lxml import etree
import requests
from concurrent.futures import ThreadPoolExecutor

headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15 Edg/142.0.0.0',
    'cookie': os.getenv('LIANJIA_COOKIE', ''),  # Optional local environment variable; never commit a login cookie.
}

def spider(k, v, page):
    url = f'https://cd.lianjia.com/ershoufang/{v}/pg{page}/'
    resp = requests.get(url, headers=headers).text
    tree = etree.HTML(resp)
    li_list = tree.xpath('//div[@id="content"]/div[1]/ul/li')
    print(li_list)

    # 检查文件是否存在，如果不存在则写入表头
    file_exists = os.path.exists('二手房.csv')

    with open('二手房.csv', 'a+', encoding='utf-8-sig', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # 如果文件不存在，则写入表头
        if not file_exists:
            writer.writerow(['城市', '标题', '价格', '均价', '链接', '关注人数', '标签',
                            '户型', '面积', '朝向', '装修', '楼层', '建筑类型',
                            '地址', '图片链接', '区域'])  # 表头

        try:
            for li in li_list:
                title = li.xpath('.//div[1]/div[1]/a/text()')[0]
                img_url = li.xpath('.//a/img[2]/@data-original')[0]
                avg_price = li.xpath('.//div[1]/div[6]/div[2]/span/text()')[0]
                #/div[1]/div[6]/div[2]/span
                address = li.xpath('.//div[1]/div[2]/div/a[1]/text()')[0]
                city = '成都市'
                infos = [i.strip() for i in li.xpath('.//div[@class="houseInfo"]/text()')[0].split('|')]
                [houseType, area, direct, decorate, level] = infos[:5]
                buildType = infos[-1]
                follow = li.xpath('.//div[@class="followInfo"]/text()')[0].split('/')[0].split('人')[0].strip()
                tag = '/'.join(li.xpath('.//div[@class="tag"]/span/text()'))
                price =  li.xpath('.//div[1]/div[6]/div[1]/span/text()')[0]+'万'
                #//*[@id="content"]/div[1]/ul/li[1]/div[1]/div[6]/div[1]/span
                href = li.xpath('.//div[@class="title"]/a/@href')[0]

                # 将所有数据组合成一行
                row = [city, title, price, avg_price, href, follow, tag, houseType, area, direct, decorate, level,
                    buildType, address, img_url, k]

                # 清理数据，确保没有多余的空格和换行符
                row = [i.replace(',', '').replace('\n', '').replace('\r', '').replace(' ', '').strip() for i in row]

                # 写入 CSV 文件
                writer.writerow(row)
                print(row)
            
        except Exception as e:
            print(f"Error processing page {page} of {k}: {e}")

citys = {
    '锦江': 'jinjiang',
    '青羊': 'qingyang',
    '武侯': 'wuhou',
    '高新': 'gaoxin',
    '成华': 'chenghua',
    '金牛': 'jinniu',
    '天府新区': 'tianfuxinqu',
    '高新西': 'gaoxinxi',
    '双流': 'shuangliu',
    '温江': 'wenjiang',
    '郫都区': 'pidouqu',
    '龙泉驿': 'longquanyi',
    '新都': 'xindou',
    '天府新区南区': 'tianfuxingunanqu',
    '青白江': 'qingbaijiang',
    '都江堰': 'doujiangyan',
    '彭州': 'pengzhou',
    '简阳': 'jianyang',
    '新津区': 'xinningqu',
    '崇州': 'chongzhou',
    '大邑': 'dayi',
    '金堂': 'jintang',
    '蒲江': 'pujiang',
    '邛崃': 'qionglai'
}

def main():
    with ThreadPoolExecutor(max_workers=5) as executor:  # 设置最大线程数
        for page in range(1, 101):
            for k, v in citys.items():
                print(f'{k},第{page}页爬取中...')
                time.sleep(random.randint(1, 5))  # 随机延时，避免请求过频繁
                executor.submit(spider, k, v, page)  # 提交任务到线程池

if __name__ == '__main__':
    main()

