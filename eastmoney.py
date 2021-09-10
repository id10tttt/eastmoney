#!-*- coding: utf-8 -*-
import requests
import json
import random
import redis
from multiprocessing import Pool

# 上海证券市场
# - 6 上交所
# - 60 上海A股
# - 600 主板
# - 601 主板
# - 603 主板
# - 688 科创板
# - 500 上海封闭式基金
# - 900 上海B股

# 深圳证券市场
# - 0 深交所
# - 3 深交所
# - 00 深圳A股
# - 000 主板
# - 001 主板
# - 002 中小板
# - 200 深圳B股
# - 184 深圳封闭式基金
# - 300 创业板，创业板是在深圳市场交易的

bk0465_url_list = [
    'http://16.push2.eastmoney.com/api/qt/clist/get', 'http://55.push2.eastmoney.com/api/qt/clist/get'
]
COMPANY_SURVEY_URL = 'http://emweb.eastmoney.com/PC_HSF10/CompanySurvey/CompanySurveyAjax'
SHARE_HOLDER_URL = 'http://emweb.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax'


def get_redis_client(db):
    return redis.Redis(db=db)


# f2最新价 f3涨跌幅 f4涨跌额 f5成交量(手) f6成交额 f7振幅  f8换手率 f9市盈率(动态) f10 量比 f12 代码  f14 名称  f15最高价  f16最低  f17今开 f18昨收  f23 市净率
demo_data = {
    'f1': 2,
    'f2': 5.33,
    'f3': 0.76,
    'f4': 0.04,
    'f5': 24625,
    'f6': 13065349.0,
    'f7': 1.7,
    'f8': 0.19,
    'f9': 59.49,
    'f10': 1.39,
    'f11': 0.0,
    'f12': '000597',
    'f13': 0,
    'f14': '东北制药',
    'f15': 5.36,
    'f16': 5.27,
    'f17': 5.36,
    'f18': 5.29,
    'f20': 7184164502,
    'f21': 7057686454,
    'f22': -0.19,
    'f23': 1.74,
    'f24': 13.16,
    'f25': 5.34,
    'f45': 60384107.93,
    'f62': 1217162.0,
    'f115': 497.93,
    'f128': '-',
    'f140': '-',
    'f141': '-',
    'f136': '-',
    'f152': 2
}

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
}

bk0465_params = {
    'cb': '',
    'pn': 1,
    'pz': 20,
    'po': 1,
    'np': 1,
    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
    'fltt': 2,
    'invt': 2,
    'fid': 'f3',
    'fs': 'b:BK0465 f:!50',
    'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45',
    '_': '1631153683978'
}


def parse_list_data(parsed_result):
    redis_client = get_redis_client(0)
    list_data = parsed_result.get('data', {}).get('diff', {})
    for x in list_data:
        code = x.get('f12')
        if code.startswith('6') or code.startswith('5') or code.startswith('9'):
            prefix_code = 'SH'
        else:
            prefix_code = 'SZ'
        redis_client.set(prefix_code + code, json.dumps(x))
    redis_client.close()


def get_list_data(page_number):
    bk0465_params.update({
        'pn': page_number
    })
    res = requests.get(random.choice(bk0465_url_list), params=bk0465_params, headers=headers)
    parsed_result = json.loads(res.text)
    print(parsed_result.get('data', {}).get('diff', {}))
    parse_list_data(parsed_result)


def get_company_data(code):
    try:
        company_code = code.decode()
        redis_client_1 = get_redis_client(1)
        req_params = {
            'code': company_code
        }
        res = requests.get(COMPANY_SURVEY_URL, params=req_params, headers=headers)
        redis_client_1.set(company_code, json.dumps(res.json()))
        redis_client_1.close()
    except Exception as e:
        print('code: {}, exception: {}'.format(code, e))


def get_share_holder_data(code):
    try:
        company_code = code.decode()
        redis_client_1 = get_redis_client(2)
        req_params = {
            'code': company_code
        }
        res = requests.get(SHARE_HOLDER_URL, params=req_params, headers=headers)
        redis_client_1.set(company_code, json.dumps(res.json()))
        redis_client_1.close()
    except Exception as e:
        print('code: {}, exception: {}'.format(code, e))


if __name__ == '__main__':
    # with Pool(8) as p:
    #     p.map(get_list_data, range(1, 15))
    # p.close()

    redis_client_0 = get_redis_client(0)
    code_list = redis_client_0.keys('*')

    with Pool(8) as p:
        p.map(get_share_holder_data, code_list)
    p.close()
