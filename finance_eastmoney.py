# -*- coding: utf-8 -*-
import random
import requests
import pandas as pd
import time
from random import choice
import datetime
import traceback
from sys import argv
import argparse

finance_zyzb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew'
finance_zcfzb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/zcfzbAjaxNew'
finance_lrb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/lrbAjaxNew'
finance_xjllb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/xjllbAjaxNew'
business_analysis_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax'
stock_url = 'http://push2.eastmoney.com/api/qt/stock/get'
# company_survey_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/CompanySurveyAjax'
company_survey_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax'

stock_relationship_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/StockRelationship/PageAjax'

org_holder_url = 'http://basic.10jqka.com.cn/basicapi/holder/stock/org_holder/detail'

USER_AGENT = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.112 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.3319.102 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2309.372 Safari/537.36',

    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 5.1; rv:31.0) Gecko/20100101 Firefox/31.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20120101 Firefox/29.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:25.0) Gecko/20100101 Firefox/29.0',

    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b11pre) Gecko/20110128 Firefox/4.0b11pre',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110131 Firefox/4.0b11pre',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110129 Firefox/4.0b11pre',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110128 Firefox/4.0b11pre',
    'Mozilla/5.0 (Windows NT 6.1; rv:2.0b11pre) Gecko/20110126 Firefox/4.0b11pre',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b10pre) Gecko/20110118 Firefox/4.0b10pre',

    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
]

headers = {
    'User-Agent': choice(USER_AGENT)
}

query_dates = '2022-03-31, 2021-12-31, 2021-09-30, 2021-06-30, 2021-03-31, 2020-12-31, 2020-09-30'
save_period = ['2021-09-30 00:00:00', '2021-06-30 00:00:00', '2021-03-31 00:00:00',
               '2020-12-31 00:00:00', '2020-09-30 00:00:00']


def get_code_prefix(code: str):
    if code.startswith('6') or code.startswith('5') or code.startswith('9'):
        prefix_code = 'SH'
    else:
        prefix_code = 'SZ'
    return prefix_code


def get_stock_relationship_data(code: str):
    prefix_code = get_code_prefix(code)
    payloads = {
        'code': '{}{}'.format(prefix_code, code)
    }
    res = requests.get(stock_relationship_url, params=payloads, headers=headers)
    ggpm = res.json().get('ggpm')
    code_pm = filter(lambda x: x['CORRE_SECURITY_CODE'] == code, ggpm)
    try:
        return ggpm.index(next(code_pm)) + 1
    except Exception as e:
        return 0


"""
CHZZL：存货周转率
XSJLL: 净利率
XSMLL: 毛利率
ROEJQ: 净资产收益率
XSJLL: 总资产收益率
ZCFZL: 资产负债率
TOTALOPERATEREVE: 营业总收入
"""


def save_main_data(code: str):
    """
        主要指标
    """
    payloads = {
        'code': code,
        'type': '0'
    }
    res = requests.get(finance_zyzb_url, params=payloads, headers=headers)

    result = pd.DataFrame(data=res.json().get('data'))
    result.set_index(['REPORT_DATE'])
    # result.to_csv('{}_ZYZB.csv'.format(code), encoding='utf-8')
    return result


"""
TOTAL_EQUITY: 流动负债合计
"""


def save_zcfzb_data(code: str):
    """
        资产负债表
    """
    payloads = {
        'companyType': 4,
        'reportDateType': 0,
        'reportType': 1,
        'dates': query_dates,
        'code': code,
    }
    res = requests.get(finance_zcfzb_url, params=payloads, headers=headers)
    result = pd.DataFrame(data=res.json().get('data'))
    # result.to_csv('{}_ZCFZB.csv'.format(code), encoding='utf-8')
    return result


"""
FE_INTEREST_EXPENSE：利息费用
FE_INTEREST_INCOME: 利息收入
CONTINUED_NETPROFIT: 净利润
"""


def save_lrb_data(code: str):
    """
        利润表
    """
    payloads = {
        'companyType': 4,
        'reportDateType': 0,
        'reportType': 1,
        'dates': query_dates,
        'code': code,
    }
    res = requests.get(finance_lrb_url, params=payloads, headers=headers)
    result = pd.DataFrame(data=res.json().get('data'))
    result.set_index(['REPORT_DATE'])
    # result.to_csv('{}_LRB.csv'.format(code), encoding='utf-8')
    return result


def save_xjllb_data(code: str):
    """
        现金流量表
    """
    payloads = {
        'companyType': 4,
        'reportDateType': 0,
        'reportType': 1,
        'dates': query_dates,
        'code': code,
    }
    res = requests.get(finance_xjllb_url, params=payloads, headers=headers)
    result = pd.DataFrame(data=res.json().get('data'))
    result.set_index(['REPORT_DATE'])
    # result.to_csv('{}_XJLLB.csv'.format(code), encoding='utf-8')
    return result


"""
MAINOP_TYPE: 分类：1（按行业分类）；2（按产品分类）；3（按地区分类）
RANK: 1（外币）；2（人民币）
MBI_RATIO：收入比例
"""


def save_business_analysis(code: str):
    payload_data = {
        'code': code
    }
    res = requests.get(business_analysis_url, params=payload_data, headers=headers)
    result = res.json().get('zygcfx')
    result = pd.DataFrame(data=result)
    result.set_index(['REPORT_DATE'])
    # result.to_csv('{}_BUSINESS_ANALYSIS.csv'.format(code), encoding='utf-8')
    return result


"""
f173: ROE
f188: 负债率
f187: 净利率
f102: 每股净资产
f277：总资产
f85: 流通股
f162: PE(动)
f56: 收益(三)
f167: 市净率
f183: 总营收
f184: 同比
f105: 净利润
f185: 同比(-)
f186: 毛利率
f188: 负债率
f84: 总股本
f116: 总值
f117: 流值
f190: 每股未分配利润
"""


def save_stock_info(code: str, sec_id: str):
    payloads = {
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'invt': 2,
        'fltt': 2,
        # 'fields': 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184, f185, f186, f187, f188, f189, f190, f191, f192, f107, f111, f86, f177, f78, f110, f262, f263, f264, f267, f268, f250, f251, f252, f253, f254, f255, f256, f257, f258, f266, f269, f270, f271, f273, f274, f275, f127, f199, f128, f193, f196, f194, f195, f197, f80, f280, f281, f282, f284, f285, f286, f287, f292',
        'fields': ','.join('f{}'.format(x) for x in range(1, 293)),
        'secid': sec_id,
        '_': int(time.time() * 1000)
    }
    res = requests.get(stock_url, params=payloads, headers=headers)
    result = pd.DataFrame(data=[res.json().get('data')])
    f84 = res.json().get('data', {}).get('f84')
    f85 = res.json().get('data', {}).get('f85')
    f277 = res.json().get('data', {}).get('f277')
    f116 = res.json().get('data', {}).get('f116')
    result.to_csv('{}_STOCK.csv'.format(code), encoding='utf-8')
    return result, [f84, f116, f85, f277]


def get_company_survey(code: str):
    payload_data = {
        'code': code
    }
    res = requests.post(company_survey_url, data=payload_data, headers=headers)
    # 资本资料
    jbzl = res.json().get('jbzl')
    return jbzl[0] if jbzl else {}


def get_security_code(code: str):
    if code.startswith('6') or code.startswith('5') or code.startswith('9'):
        prefix_code = 'SH'
        sec_id = '1'
    else:
        prefix_code = 'SZ'
        sec_id = '0'
    return prefix_code + code, sec_id + '.' + code


def save_stock_analysis_result(code, main_data, zcfzb_data, lrb_data, business_data, jbzl, extra_values):
    analysis_header = ['期间', '净利率', '毛利率', '市值（亿）', '市销率', '净资产收益率ROE', '资产负债率',
                       '国际销售占比', '流动负债', '利息费用', '净利润', '雇员', '库存周转率']
    all_values = [analysis_header]
    for period_id in save_period:
        #  净利率
        v1 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'XSJLL']
        # 毛利率
        v2 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'XSMLL']
        # 市值
        v3 = extra_values[1]

        # 营业总收入
        v4 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'TOTALOPERATEREVE']
        v4 = float(v3) / float(get_pandas_value(v4)) if v3 and v4.size > 0 else 0
        # 净资产收益率
        v5 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'ROEJQ']
        # 资产负债率
        v6 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'ZCFZL']
        # 国际销售占比
        v7 = business_data.loc[(business_data['REPORT_DATE'] == period_id) & (business_data['MAINOP_TYPE'] == '3') & (
                business_data['RANK'] == 2), 'MBI_RATIO']
        # 流动负债合计
        v8 = zcfzb_data.loc[zcfzb_data['REPORT_DATE'] == period_id, 'TOTAL_EQUITY']
        # 利息费用
        v9 = lrb_data.loc[lrb_data['REPORT_DATE'] == period_id, 'FE_INTEREST_EXPENSE']
        # 净利润
        v10 = lrb_data.loc[lrb_data['REPORT_DATE'] == period_id, 'CONTINUED_NETPROFIT']
        # 雇员
        v11 = jbzl.get('EMP_NUM')
        # 库存周转率
        v12 = main_data.loc[main_data['REPORT_DATE'] == period_id, 'CHZZL']
        tmp = [period_id, get_pandas_value(v1), get_pandas_value(v2), v3, v4, get_pandas_value(v5),
               get_pandas_value(v6), get_pandas_value(v7), get_pandas_value(v8), get_pandas_value(v9),
               get_pandas_value(v10),
               v11, get_pandas_value(v12)]
        all_values.append(tmp)
    print(all_values)
    result = pd.DataFrame(data=all_values)
    result.to_csv('{}.csv'.format(code), encoding='utf-8')


def search_period_stock_analysis_result(code, main_data, zcfzb_data, lrb_data, business_data, jbzl, extra_values,
                                        query_period, all_values):
    for search_period in query_period:
        #  净利率
        xsjll = main_data.loc[main_data['REPORT_DATE'] == search_period, 'XSJLL']
        # 毛利率
        xsmll = main_data.loc[main_data['REPORT_DATE'] == search_period, 'XSMLL']
        # 市值
        v3 = extra_values[1]
        # 总资产
        total_value = extra_values[3]
        f85 = extra_values[2]
        f84 = extra_values[0]
        # 营业总收入
        v4 = main_data.loc[main_data['REPORT_DATE'] == search_period, 'TOTALOPERATEREVE']
        v5 = float(v3) / float(get_pandas_value(v4)) if v3 and v4.size > 0 else 0
        # 净资产收益率
        roejq = main_data.loc[main_data['REPORT_DATE'] == search_period, 'ROEJQ']
        # 资产负债率
        zcfzl = main_data.loc[main_data['REPORT_DATE'] == search_period, 'ZCFZL']
        # 国际销售占比
        mbi_ratio = business_data.loc[
            (business_data['REPORT_DATE'] == search_period) & (business_data['MAINOP_TYPE'] == '3') & (
                    business_data['RANK'] == 2), 'MBI_RATIO']
        # 流动负债合计
        total_equity = zcfzb_data.loc[zcfzb_data['REPORT_DATE'] == search_period, 'TOTAL_EQUITY']
        # 利息费用
        fe_interest_expense = lrb_data.loc[lrb_data['REPORT_DATE'] == search_period, 'FE_INTEREST_EXPENSE']
        # 净利润
        continued_netprofit = lrb_data.loc[lrb_data['REPORT_DATE'] == search_period, 'CONTINUED_NETPROFIT']
        # 雇员
        v12 = jbzl.get('EMP_NUM')
        peg_result = get_east_money_peg_value(code)

        # PEG
        peg_car = peg_result.get('PEG_CAR')
        # 市净率
        pb_mrq = peg_result.get('PB_MRQ')
        # 市现率
        pcf_ocf_tim = peg_result.get('PCF_OCF_TTM')

        # 所属行业
        industry_csrc = jbzl.get('INDUSTRYCSRC1')

        # 行业排名
        hypm = get_stock_relationship_data(code)

        # 基金机构
        search_period_date = search_period.split(' 00:00:00')
        org_holder = get_org_holder(code, search_period_date[0])

        # 库存周转率
        chzzl = main_data.loc[main_data['REPORT_DATE'] == search_period, 'CHZZL']
        tmp = [str(code), search_period, get_pandas_value(xsjll), get_pandas_value(xsmll), v3, total_value, f85, f84,
               get_pandas_value(v4), v5,
               get_pandas_value(roejq), get_pandas_value(zcfzl), get_pandas_value(mbi_ratio),
               get_pandas_value(total_equity), get_pandas_value(fe_interest_expense),
               get_pandas_value(continued_netprofit), get_pandas_value(v12), get_pandas_value(chzzl),
               peg_car, pb_mrq, pcf_ocf_tim, industry_csrc, hypm, org_holder]
        all_values.append(tmp)
    return all_values


def get_pandas_value(parse_value):
    try:
        parse_value = parse_value.values
    except Exception as e:
        return parse_value
    if parse_value.size > 0:
        return parse_value[0]
    else:
        return parse_value


"""
PEG_CAR: PEG
PB_MRQ: 市净率
PCF_OCF_TTM: 市现率
"""


def get_east_money_peg_value(stock_code):
    req_url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
    payload_data = {
        'callback': '',
        'reportName': 'RPT_VALUEANALYSIS_DET',
        'columns': 'ALL',
        'quoteColumns': '',
        'pageNumber': 1,
        'pageSize': 1,
        'sortColumns': 'TRADE_DATE',
        'sortTypes': -1,
        'source': 'WEB',
        'client': 'WEB',
        'filter': '(SECURITY_CODE="{}")'.format(stock_code),
        '_': 1651220068071
    }
    res = requests.get(req_url, params=payload_data, headers=headers)
    result_data = res.json().get('result', {}).get('data', [])
    if result_data:
        return result_data[0]
    else:
        return result_data


def get_peg_value(stock_code):
    iwencai_session = requests.session()
    # session_uuid = uuid4()
    # print(session_uuid)
    session_uuid = 'c45f6548a9ea70144afbfe0f89c2671c1650187454'
    iwencai_cookies = {
        'ta_random_userid': '4208v2n1yc',
        'WafStatus': '0',
        'PHPSESSID': '{}'.format(session_uuid),
        'cid': '{}1650187454'.format(session_uuid),
        'ComputerID': '{}1650187454'.format(session_uuid),
        'iwencaisearchquery': '{}'.format(stock_code),
        'v': 'A7VZH1ijOxM9Jl-vBrPI07_7wjpqMmlEM-ZNmDfacSx7Dtuk_4J5FMM2XWrE'
    }
    iwencai_headers = {
        'Connection': 'keep-alive',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://www.iwencai.com/stockpick/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent': choice(USER_AGENT)
    }

    payload_data = {
        'pid': 1555,
        'codes': '{}'.format(stock_code),
        'codeType': 'stock',
        'info': {
            "view": {
                "nolazy": 1, "parseArr": {
                    "_v": "new", "dateRange": [str(datetime.date.today()), str(datetime.date.today())], "staying": [],
                    "queryCompare": [], "comparesOfIndex": []
                },
                "asyncParams": {
                    "tid": 659
                }
            }
        }
    }
    base_url = 'http://www.iwencai.com'
    his_url = 'http://www.iwencai.com/diag/block-detail'
    res = iwencai_session.get(his_url, headers=iwencai_headers, params=payload_data, cookies=iwencai_cookies)
    res_data = res.json().get('data')
    # print('res_data: {}'.format(res_data))
    redirect_url = res.json().get('data').get('url')
    time.sleep(random.random())
    res = iwencai_session.get('{}{}'.format(base_url, redirect_url), headers=iwencai_headers, cookies=iwencai_cookies)
    result_data = res.json().get('data', {}).get('data', {})
    result_option = result_data.get('option', {})
    result_series = result_option.get('series')
    if len(result_series) > 0:
        peg_data = result_series[0].get('data')
        peg_x_axis = result_option.get('xAxis')[0]
        peg_data = peg_data[::-1][0]
        peg_x_axis = peg_x_axis[::-1][0]
    else:
        print('empty: {}'.format(result_data))
        peg_data = []
        peg_x_axis = []
    return peg_data, peg_x_axis


def get_default_period():
    search_today = datetime.date.today()
    search_month = search_today.month
    search_year = search_today.year
    search_year = int(search_year)
    search_month = int(search_month)
    search_period = []
    for x in range(search_year - 2, search_year):
        search_period += [f'{x}-03-31 00:00:00', f'{x}-06-30 00:00:00', f'{x}-09-30 00:00:00', f'{x}-12-31 00:00:00']
    if search_month < 3:
        search_period += [f'{search_year}-03-31 00:00:00']
    elif 3 <= search_month < 6:
        search_period += [f'{search_year}-03-31 00:00:00']
    elif 6 <= search_month < 9:
        search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00']
    elif 9 <= search_month < 12:
        search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                          f'{search_year}-09-30 00:00:00']
    return search_period


def get_transverse_data(code_list, analysis_header, query_period):
    """
    横向表格
    """
    all_values = [analysis_header]
    for code in code_list:
        try:
            security_code, sec_id = get_security_code(code)
            main_data = save_main_data(security_code)
            zcfzb_data = save_zcfzb_data(security_code)
            lrb_data = save_lrb_data(security_code)
            xjllb_data = save_xjllb_data(security_code)
            stock_data, extra_values = save_stock_info(security_code, sec_id)
            jbzl = get_company_survey(security_code)
            business_data = save_business_analysis(security_code)
            all_values = search_period_stock_analysis_result(
                code, main_data, zcfzb_data, lrb_data, business_data, jbzl, extra_values, query_period, all_values)
        except Exception as e:
            print(traceback.format_exc())
            continue
    result = pd.DataFrame(data=all_values)
    result.to_csv('查询结果.csv', encoding='utf-8')


def get_portrait_data(code_list, analysis_header, query_period):
    """
    纵向表格
    """
    """
        横向表格
        """

    all_values = {}
    for code in code_list:
        code_values = [analysis_header]
        try:
            security_code, sec_id = get_security_code(code)
            main_data = save_main_data(security_code)
            zcfzb_data = save_zcfzb_data(security_code)
            lrb_data = save_lrb_data(security_code)
            xjllb_data = save_xjllb_data(security_code)
            stock_data, extra_values = save_stock_info(security_code, sec_id)
            jbzl = get_company_survey(security_code)
            business_data = save_business_analysis(security_code)
            code_values = search_period_stock_analysis_result(
                code, main_data, zcfzb_data, lrb_data, business_data, jbzl, extra_values, query_period, code_values)
            all_values[code] = code_values
        except Exception as e:
            print(traceback.format_exc())
            continue

    pd_writer = pd.ExcelWriter('查询结果.xlsx')
    for value_code in all_values.keys():
        tmp_df = pd.DataFrame(all_values[value_code])
        tmp_df_T = tmp_df.T
        tmp_df_T.to_excel(pd_writer, value_code)
    pd_writer.save()
    pd_writer.close()


def get_org_holder(code: str, date: str) -> str:
    """
    基金机构<数据来源-同花顺>
    """
    payload_data = {
        'code': code,
        'date': date,
        'page': 1,
        'size': 15,
        'type': 'all'
    }
    res = requests.get(org_holder_url, params=payload_data, headers=headers)

    result = res.json()
    status_code = result.get('status_code')
    if status_code == 0:
        result_data = res.json().get('data', {}).get('data', [])
        return '; \n'.join(
            '{org_name}, {rate}'.format(org_name=x.get('org_name'), rate=x.get('rate')) for x in result_data)
    else:
        return ''


def main_p(args):
    try:
        code_list = args.code
    except AttributeError as e:
        parser.print_help()
        code_list = ''

    if code_list:
        # default_period = '2021-09-30'
        # search_period = argv[2] if len(argv) > 2 else default_period
        # search_period = search_period + ' 00:00:00'
        query_period = get_default_period()
        # print(query_period)
        code_list = code_list.split(',')
        analysis_header = ['编码', '期间', '净利率', '毛利率', '市值（亿）', '总资产', '流通股', '总股本', '营业总收入',
                           '市销率', '净资产收益率ROE', '资产负债率', '国际销售占比', '流动负债', '利息费用', '净利润',
                           '雇员', '库存周转率', 'PEG', '市净率', '市现率', '所属行业', '行业排名', '基金机构']
        get_portrait_data(code_list, analysis_header, query_period)


def main_t(args):
    try:
        code_list = args.code
    except AttributeError as e:
        parser.print_help()
        code_list = ''

    if code_list:
        # default_period = '2021-09-30'
        # search_period = argv[2] if len(argv) > 2 else default_period
        # search_period = search_period + ' 00:00:00'
        query_period = get_default_period()
        # print(query_period)
        code_list = code_list.split(',')
        analysis_header = ['编码', '期间', '净利率', '毛利率', '市值（亿）', '总资产', '流通股', '总股本', '营业总收入',
                           '市销率', '净资产收益率ROE', '资产负债率', '国际销售占比', '流动负债', '利息费用', '净利润',
                           '雇员', '库存周转率', 'PEG', '市净率', '市现率', '所属行业', '行业排名', '基金机构']
        get_transverse_data(code_list, analysis_header, query_period)


def arguments_init():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help=u'示例： finance_eastmoney.py p -c 002223,002352')

    ret_t = subparser.add_parser('t', help=u'横向表格')
    ret_t.add_argument('-c', type=str, help=u'股票代码', dest='code', required=True)
    ret_t.set_defaults(func=main_t)

    ret_p = subparser.add_parser('p', help=u'纵向表格')
    ret_p.add_argument('-c', type=str, help=u'股票代码', dest='code', required=True)
    ret_p.set_defaults(func=main_p)
    return parser


if __name__ == '__main__':
    # org_holder = get_org_holder('002223', '2022-06-30')
    # print('org_holder: ', org_holder)
    parser = arguments_init()
    default_code = '002223,300136'
    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError as e:
        parser.print_help()
        parser.exit()
