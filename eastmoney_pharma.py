from selenium import webdriver
from time import sleep
import os.path
import requests
import re

'''爬取上证指数的所有股票信息，保存到本地文件/数据库'''

ELE_LIST = ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '最高价', '最低价', '今开',
            '昨收', '量比', '换手率', '市盈率', '市净率']

ELE_HEADER = ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额', '振幅', '最高价', '最低价', '今开',
              '昨收', '量比', '换手率', '市盈率', '市净率', '详情页面', '股市代码']
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
}


def extractor(xpath_text):
    '''根据xpath获取内容'''
    TCases = driver.find_element_by_xpath(xpath_text)
    return TCases.text


def extractor_url(xpath_text):
    '''根据xpath获取href'''
    TCases = driver.find_element_by_xpath(xpath_text)
    return TCases.get_property('href')


def export_to_file(stock_dict):
    '''导出股票数据'''
    file_name = '沪指股票数据-医药制造.csv'
    if os.path.isfile(file_name):
        with open(file_name, 'a', encoding='utf-8') as file:
            file.write(','.join(stock_dict.values()))
            file.write('\n')
    else:
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(','.join(x for x in ELE_HEADER))
            file.write('\n')
            file.write(','.join(stock_dict.values()))
            file.write('\n')


def extract_market_code(req_response):
    pattern = re.compile("marketCode = \'(.+?)\'")
    res = re.findall(pattern, req_response.text)
    return res[0] if res else ''


# url = 'http://quote.eastmoney.com/center/gridlist.html#sh_a_board'
url = 'http://quote.eastmoney.com/center/boardlist.html#boards-BK04651'
driver = webdriver.Chrome("/home/psc00000039/Downloads/east_money/chromedriver")
driver.get(url)
sleep(5)

for page_num in range(1, 15):
    try:
        for i in range(1, 21):
            detail_page_xpath = '/html/body/div[1]/div[2]/div[2]/div[5]/table/tbody/tr[{}]/td[2]/a'.format(i)
            detail_page_link = extractor_url(detail_page_xpath)
            market_code = extract_market_code(requests.get(detail_page_link, headers=HEADERS))
            stock_dict = {}
            number_list = ['2', '3', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18']
            for j, name in zip(number_list, ELE_LIST):
                # temp_xpath = "/html/body/div[@class='page-wrapper']/div[@id='page-body']/div[@id='body-main']/div[@id='table_wrapper']/div[@class='listview full']/table[@id='table_wrapper-table']/tbody/tr[@class='{}'][{}]/td[{}]".format(
                #     ele_type, i, j)
                temp_xpath = '/html/body/div[1]/div[2]/div[2]/div[5]/table/tbody/tr[{}]/td[{}]'.format(i, j)
                stock_dict[name] = extractor(temp_xpath)
            stock_dict['详情页面'] = detail_page_link
            stock_dict['股市代码'] = market_code
            print(list(stock_dict.values()))
            export_to_file(stock_dict)
        # 到下一页继续爬
        driver.find_element_by_xpath('/html/body/div[1]/div[2]/div[2]/div[5]/div/div/a[2]').click()
        sleep(1)
    except Exception as e:
        print('error: {}'.format(e))
        continue

driver.close()
