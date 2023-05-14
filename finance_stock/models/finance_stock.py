# -*- coding: utf-8 -*-
from odoo import models, fields
import requests
import math
from random import choice
from odoo.tools import ormcache
from ..tools.iqka_data import get_10jqka_company_manager_info
from itertools import groupby
import json
import time
import datetime
from odoo.exceptions import UserError
import tushare as ts
import logging

_logger = logging.getLogger(__name__)

TS_TOKEN = '8e145e12e63d1191aa1b1833c030fcfb6fa24a3730154d02aab96036'

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

    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.70'
]

headers = {
    'User-Agent': choice(USER_AGENT)
}

STOCK_DICT = {
    'SSE': '上交所',
    'SZSE': '深交所',
    'OTHER': '其它'
}


class FinanceStockBasic(models.Model):
    _name = 'finance.stock.basic'
    _description = '股票代码列表'
    _inherit = 'finance.stock.mixin'
    _sql_constraints = [
        ('unique_symbol', 'unique(symbol)', '股票代码唯一')
    ]

    ts_code = fields.Char('TS代码')
    symbol = fields.Char('股票代码', required=True)
    name = fields.Char('股票名称')
    area = fields.Char('地域')
    industry = fields.Char('所属行业')
    fullname = fields.Char('股票全称')
    enname = fields.Char('英文全称')
    cnspell = fields.Char('拼音缩写')
    market = fields.Char('市场类型')
    exchange = fields.Selection([
        ('SSE', '上交所'),
        ('SZSE', '深交所'),
        ('OTHER', '其它')
    ], string='交易所代码')
    curr_type = fields.Char('交易货币')
    list_status = fields.Selection([
        ('L', '上市'),
        ('D', '退市'),
        ('P', '暂停上市'),
        ('O', '其它'),
    ], string='上市状态')
    list_date = fields.Char('上市日期')
    delist_date = fields.Char('退市日期')
    is_hs = fields.Selection([
        ('N', '否'),
        ('H', '沪股通'),
        ('S', '深股通')
    ], '是否沪深港通标')
    stock_company_id = fields.Many2one('finance.stock.company', string=u'基本信息')

    sync_state = fields.Boolean('同步状态', default=False)

    main_data_url = fields.Char('接口地址',
                                default='http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew')

    main_data_ids = fields.One2many('finance.stock.main.data', 'stock_id', string='主要指标')

    f56 = fields.Char('收益(三)')
    f84 = fields.Char('总股本')
    f85 = fields.Char('流通股')
    f102 = fields.Char('每股净资产')
    f105 = fields.Char('净利润')
    f116 = fields.Char('总值')
    f117 = fields.Char('流值')
    f162 = fields.Char('PE(动)')
    f167 = fields.Char('市净率')
    f173 = fields.Char('ROE')
    f183 = fields.Char('总营收')
    f184 = fields.Char('同比')
    f185 = fields.Char('同比(-)')
    f186 = fields.Char('毛利率')
    f187 = fields.Char('净利率')
    f188 = fields.Char('负债率')
    f190 = fields.Char('每股未分配利润')
    f277 = fields.Char('总资产')
    stock_json = fields.Char('STOCK JSON')

    peg_car = fields.Char('PEG')
    pb_mrq = fields.Char('市净率')
    pcf_ocf_tim = fields.Char('市现率')

    hypm = fields.Char('行业排名')

    zcfzb_ids = fields.One2many('finance.stock.zcfzb', 'stock_id', string='资产负债表明细行')
    report_ids = fields.One2many('finance.stock.report', 'stock_id', string='业绩报表')
    lrb_ids = fields.One2many('finance.stock.lrb', 'stock_id', string='利润表')
    xjllb_ids = fields.One2many('finance.stock.xjllb', 'stock_id', string='现金流量表')
    business_ids = fields.One2many('finance.stock.business', 'stock_id', string='主营构成分析')
    holder_ids = fields.One2many('finance.stock.holder', 'stock_id', string='基金机构')
    share_holder_ids = fields.One2many('finance.stock.share.holder', 'stock_id', string='流通股东')
    event_ids = fields.One2many('finance.company.event', 'stock_id', string='Event')
    operate_cs_ids = fields.One2many('operate.customer.supplier', 'stock_id', string='Supplier/Customer')

    plge_rat = fields.Char('质押比例')
    blt_hld_rat = fields.Char('合计持股比')
    blt_tshr_rat = fields.Char('合计占总股比')
    blt_plge_shr = fields.Char('合计质押股数')
    plge_shr = fields.Char('累计质押股总数')

    restricted_json = fields.Char('限售解禁')
    rls_tshr_rat = fields.Char('比例')
    shr_type = fields.Char('shrTyp')

    shr_red_json = fields.Char('股东减持JSON')
    shr_redu = fields.Char('股东减持')
    stat_dt = fields.Char('减持时间戳')
    stat_datetime = fields.Char('减持时间')
    redu_tshr_rat = fields.Char('减持比例')
    # nearest_unshr_red = fields.Char('股东减持')

    pred_typ_name = fields.Char('业绩名称')
    pred_big_typ = fields.Char('predBigTyp')
    end_dt = fields.Char('endDT')
    pred_cont = fields.Char('Pred Content')
    rpt_prd = fields.Char('报告期间')
    net_prof_pco = fields.Char('netProfPco')

    options_code = fields.Char('opinCode')
    options_rslt = fields.Char('会计师审计')

    gw = fields.Char('GW')
    gw_netast_rat = fields.Char('商誉')

    law_case = fields.Char('诉讼仲裁')
    mine_json = fields.Char('MINE SWEEP JSON')

    def update_fiscal_data(self):
        self.ensure_one()
        all_fiscal_ids = self.env['finance.fiscal.data'].search([('stock_id', '=', self.id)],
                                                                order='report_date asc')
        all_fiscal_ids.update_fiscal_data()

    @ormcache('exchange')
    def get_finance_basic_value(self, exchange):
        stock_data = self.env['finance.stock.basic'].sudo().search_read(
            domain=[('exchange', '=', exchange)],
            fields=['ts_code', 'symbol', 'name', 'exchange', 'id'],
            limit=100
        )
        group_by_result = {}
        for exchange_key, y in groupby(stock_data, key=lambda x: x.get('exchange')):
            if exchange_key in group_by_result.keys():
                group_by_result.get(exchange_key).append(list(y))
            else:
                group_by_result[exchange_key] = list(y)

        result = []
        for group_by_key in group_by_result:
            result.append({
                'exchange': STOCK_DICT.get(group_by_key, '其它'),
                'title': group_by_key,
                'badgeProps': {},
                'items': group_by_result.get(group_by_key)
            })
        return result

    def cron_fetch_mine_brief(self):
        res = self.env['finance.stock.basic'].search(['|', ('plge_rat', '=', False), ('pred_typ_name', '=', False)])
        for x in res:
            x.with_delay().get_mine_brief()

    def convert_timestamp_to_datetime(self, timestamp):
        try:
            dt = datetime.datetime.fromtimestamp(timestamp)
            return str(dt)
        except Exception as e:
            _logger.error('error: {}'.format(e))
            return timestamp

    def is_negative_result(self, result):
        """
        # TODO: 不清楚这儿的逻辑是啥，怎么判断ecode 是 0 还是 1 呢？
        :param result:
        :return:
        """
        if all([result.get('plge'), result.get('pred')]):
            return True
        return False

    def http_get_mine_brief_from_cmschina(self, mine_sweep_url, stock_id, headers, ecode=0, retries=5):
        payload_data = {
            'scode': stock_id.symbol,
            'ecode': '{}'.format(ecode)
        }
        res = requests.post(mine_sweep_url, data=json.dumps(payload_data), headers=headers)
        result = res.json().get('body')
        if not self.is_negative_result(result) and retries > 0:
            return self.http_get_mine_brief_from_cmschina(mine_sweep_url, stock_id, headers, ecode=ecode + 1,
                                                          retries=retries - 1)
        return result

    def get_mine_brief(self):
        """
        数据源： 招商财富APP
        """
        mine_sweep_url = 'https://zszx.cmschina.com/zszx/gg/minesweep/brief'
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/16D57 TdxIOS/1.00 iPhone11 cmschina/8.51 scheme/zhaoshangzq hxtheme/0',
            'Referer': 'https://zszx.cmschina.com/app/minesweep/',
            'Content-Type': 'application/json;charset=utf-8'
        }
        for stock_id in self:
            _logger.info('获取扫雷信息: {}'.format(stock_id.symbol))
            result = self.http_get_mine_brief_from_cmschina(mine_sweep_url, stock_id, headers)

            if not result:
                continue

            shr_red = result.get('shrRed', {})
            if not shr_red:
                shr_red = {}
            plge = result.get('plge', {})
            if not plge:
                plge = {}
            restricted = result.get('restricted', {})
            if not restricted:
                restricted = '暂无'
            pred = result.get('pred', {})
            if not pred:
                pred = {}
            opin = result.get('opin', {})
            if not opin:
                opin = {}
            gw = result.get('gw', {})
            if not gw:
                gw = {}
            law_case = result.get('lawCase', {})
            if not law_case:
                law_case = {}
            stock_id.write({
                'plge_rat': plge.get('plgeRat'),
                'blt_hld_rat': plge.get('plgeHldRat'),
                'blt_tshr_rat': plge.get('bltTshrRat'),
                'blt_plge_shr': plge.get('bltPlgeShr'),
                'plge_shr': plge.get('plgeShr'),
                'restricted_json': json.dumps(restricted),
                'rls_tshr_rat': restricted.get('rlsTshrRat') or 0,
                'shr_type': restricted.get('nearestUnrestricted', {}).get('shrTyp') or '暂无',
                'shr_red_json': json.dumps(shr_red),
                'shr_redu': shr_red.get('shrRedu'),
                'stat_dt': shr_red.get('statDt'),
                # 'stat_datetime': self.convert_timestamp_to_datetime(shr_red.get('statDt')),
                'redu_tshr_rat': shr_red.get('reduTshrRat'),
                'pred_typ_name': pred.get('predTypName'),
                'pred_big_typ': pred.get('predBigTyp'),
                'end_dt': pred.get('endDT'),
                'pred_cont': pred.get('predCont'),
                'rpt_prd': pred.get('rptPrd'),
                'net_prof_pco': pred.get('netProfPco'),
                'options_code': opin.get('opinCode'),
                'options_rslt': opin.get('opinRslt'),
                'gw': gw.get('gw'),
                'gw_netast_rat': gw.get('gwNetastRat'),
                'law_case': str(law_case.get('totalCase', 0)),
                'mine_json': json.dumps(result)
            })

    def cron_fetch_stock_event(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_stock_event()

    def get_stock_event(self, max_query_page=4):
        """
        BigNews<数据来源-东方财富>
        """
        self.ensure_one()
        big_news_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/CompanyBigNews/GetDSTX'
        all_event_ids = self.env['finance.company.event'].search([('stock_id', 'in', self.ids)])
        security_code, sec_id = self.get_security_code(self.symbol)
        all_data = []
        for event_page in range(1, max_query_page):
            payload_data = {
                'code': security_code.replace('.', ''),
                'type': 0,
                'pageIndex': event_page,
            }
            res = requests.get(big_news_url, params=payload_data, headers=headers)

            try:
                result = res.json()
            except Exception as e:
                _logger.error('获取数据出错: {}, {}'.format(e, res.text))
                continue
            dstx_data = result.get('dstx', {}).get('data', {})
            if not dstx_data:
                continue
            for event_type_data in dstx_data:
                for event_data in event_type_data:
                    try:
                        if all_event_ids.filtered(
                                lambda e: e.event_date == self.convert_str_to_datetime(
                                    event_data.get('NOTICE_DATE')) and
                                          e.name == event_data.get('LEVEL1_CONTENT')):
                            continue
                    except Exception as e:
                        _logger.error('发生错误: {}'.format(e))
                        continue
                    data = {
                        'stock_id': self.id,
                        'name': event_data.get('LEVEL1_CONTENT'),
                        'event_content_other': event_data.get('LEVEL2_CONTENT'),
                        'event_date': event_data.get('NOTICE_DATE'),
                        'event_type': event_data.get('EVENT_TYPE'),
                        'specific_event_type': event_data.get('SPECIFIC_EVENTTYPE'),
                        'origin_json': json.dumps(event_data)
                    }
                    all_data.append((0, 0, data))

        if all_data:
            self.write({
                'event_ids': all_data
            })

    def get_finance_stock_bonus_data(self):
        """
        分红
        """
        for stock_id in self:
            self.env['finance.stock.bonus'].get_bonus_data(stock_id)

    def get_finance_stock_share_holder_news(self):
        """
        高管持股变动
        """
        for stock_id in self:
            self.env['finance.stock.share.holder.news'].get_share_holder_news(stock_id)

    def cron_fetch_share_holder(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_stock_share_holder()

    def get_stock_share_holder(self):
        """
        流通股东<数据来源-东方财富>
        """
        self.ensure_one()
        share_holder_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageSDLTGD'
        all_period = self.get_default_period_date(default_year=2)
        security_code, sec_id = self.get_security_code(self.symbol)
        all_holder_ids = self.env['finance.stock.share.holder'].search([('stock_id', 'in', self.ids)])
        all_data = []
        exist_filter = []
        for period_date in all_period:
            _logger.info('获取流通股东信息: {}, {}'.format(security_code, period_date))

            payload_data = {
                'code': security_code,
                'date': period_date,
            }
            try:
                res = requests.get(share_holder_url, params=payload_data, headers=headers)
                result = res.json()
            except Exception as e:
                _logger.error('获取数据出错: {}, {}'.format(period_date, e))
                continue
            sdltgd_data = result.get('sdltgd', {})
            if not sdltgd_data:
                continue
            for sdltgd_value in sdltgd_data:
                holder_name = sdltgd_value.get('HOLDER_NAME')
                if all_holder_ids.filtered(lambda x: x.report_date == sdltgd_value.get('END_DATE') and
                                                     x.holder_name == holder_name):
                    continue
                current_filter = '{},{}'.format(holder_name, sdltgd_value.get('END_DATE'))
                if current_filter in exist_filter:
                    continue
                data = {
                    'secucode': self.ts_code,
                    'security_code': self.symbol,
                    'holder_name': holder_name,
                    'free_holder_number_ratio': sdltgd_value.get('FREE_HOLDNUM_RATIO'),
                    'holder_type': sdltgd_value.get('HOLDER_TYPE'),
                    'holder_rank': sdltgd_value.get('HOLDER_RANK'),
                    'hold_num': sdltgd_value.get('HOLD_NUM'),
                    'hold_num_change': sdltgd_value.get('HOLD_NUM_CHANGE'),
                    'share_type': sdltgd_value.get('SHARES_TYPE'),
                    'share_holder_json': json.dumps(sdltgd_value),
                    'stock_id': self.id,
                    'report_date': sdltgd_value.get('END_DATE')
                }
                all_data.append((0, 0, data))
                exist_filter.append(current_filter)
        if all_data:
            try:
                self.write({
                    'share_holder_ids': all_data
                })
            except Exception as e:
                _logger.error('出现错误,无法保存数据! {}, {}'.format(e, all_data))

    def cron_fetch_holder(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_org_holder()

    def get_org_holder(self):
        """
        基金机构<数据来源-同花顺>
        """
        org_holder_url = 'http://basic.10jqka.com.cn/basicapi/holder/stock/org_holder/detail'
        all_period = self.get_default_period_date()
        all_holder_ids = self.env['finance.stock.holder'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            _logger.info('获取基金机构信息: {}'.format(stock_id.symbol))
            all_data = []
            for period_id in all_period:

                search_period_date = period_id.split(' 00:00:00')
                payload_data = {
                    'code': stock_id.symbol,
                    'date': search_period_date[0],
                    'page': 1,
                    'size': 15,
                    'type': 'all'
                }

                try:
                    res = requests.get(org_holder_url, params=payload_data, headers=headers)
                    result = res.json()
                except Exception as e:
                    _logger.error('获取数据出错: {}, {}'.format(period_id, e))
                    continue
                status_code = result.get('status_code')
                if status_code != 0:
                    _logger.warning('没有获取到数据: {}, {}'.format(stock_id.symbol, search_period_date))
                    continue
                result_data = res.json().get('data', {}).get('data', [])
                if not result_data:
                    continue
                stock_holder_ids = all_holder_ids.filtered(lambda x: x.stock_id == stock_id)
                tmp_data = []
                for x in result_data:
                    org_name = x.get('org_name')
                    if stock_holder_ids.filtered(lambda x: x.ts_code == stock_id.ts_code and
                                                           x.report_date == period_id and
                                                           x.org_name == org_name):
                        continue
                    data = {
                        'ts_code': stock_id.ts_code,
                        'security_code': stock_id.symbol,
                        'org_name': x.get('org_name'),
                        'rate': x.get('rate'),
                        'report_date': period_id,
                        'holder_json': json.dumps(x)
                    }
                    _logger.info('基金机构: {}'.format(period_id))
                    tmp_data.append((0, 0, data))
                all_data += tmp_data
            if all_data:
                stock_id.write({
                    'holder_ids': all_data
                })

    def cron_fetch_relation(self):
        res = self.env['finance.stock.basic'].search(['|', ('hypm', '=', False), ('hypm', '=', 0)])
        for x in res:
            x.with_delay().get_stock_relationship_data()

    def get_stock_relationship_data(self):
        """
        行业排名
        """
        stock_relationship_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/StockRelationship/PageAjax'
        for stock_id in self:
            _logger.info('获取排名信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            payloads = {
                'code': security_code
            }
            res = requests.get(stock_relationship_url, params=payloads, headers=headers)
            ggpm = res.json().get('ggpm')
            if not ggpm:
                continue
            code_pm = filter(lambda x: x['CORRE_SECURITY_CODE'] == stock_id.symbol, ggpm)
            if not code_pm:
                continue
            try:
                hypm = ggpm.index(next(code_pm)) + 1
            except Exception as e:
                hypm = 0
            stock_id.write({
                'hypm': hypm
            })

    def cron_sync_stock_info(self):
        res = self.env['finance.stock.basic'].search([('f84', '=', False)])
        for x in res:
            x.with_delay().get_stock_info()

    def get_stock_info(self):
        """
        获取股票信息
        """
        stock_url = 'http://push2.eastmoney.com/api/qt/stock/get'
        for stock_id in self:
            _logger.info('获取股票信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            payloads = {
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'invt': 2,
                'fltt': 2,
                'fields': ','.join('f{}'.format(x) for x in range(1, 293)),
                'secid': sec_id,
                '_': int(time.time() * 1000)
            }
            res = requests.get(stock_url, params=payloads, headers=headers)
            result = res.json().get('data', {})
            if not result:
                continue
            stock_id.write({
                'f56': result.get('f56'),
                'f84': result.get('f84'),
                'f85': result.get('f85'),
                'f102': result.get('f102'),
                'f105': result.get('f105'),
                'f116': result.get('f116'),
                'f117': result.get('f117'),
                'f162': result.get('f162'),
                'f167': result.get('f167'),
                'f173': result.get('f173'),
                'f183': result.get('f183'),
                'f184': result.get('f184'),
                'f185': result.get('f185'),
                'f186': result.get('f186'),
                'f187': result.get('f187'),
                'f188': result.get('f188'),
                'f190': result.get('f190'),
                'f277': result.get('f277'),
                'stock_json': json.dumps(result)
            })

    def get_security_code(self, code):
        if code.startswith('6') or code.startswith('5') or code.startswith('9'):
            prefix_code = 'SH'
            sec_id = '1'
        else:
            prefix_code = 'SZ'
            sec_id = '0'
        return prefix_code + code, sec_id + '.' + code

    def get_update_stock_list(self):
        """
        获取所有股票信息
        """
        fields_list = [
            'ts_code', 'symbol', 'name', 'area', 'fullname',
            'enname', 'cnspell', 'market', 'exchange', 'curr_type', 'list_status', 'list_date', 'delist_date', 'is_hs'
        ]
        save_fields_list = [
            'ts_code', 'symbol', 'name', 'area', 'fullname',
            'enname', 'cnspell', 'market', 'curr_type', 'list_date', 'delist_date'
        ]
        ts_pro = ts.pro_api(TS_TOKEN)
        df = ts_pro.stock_basic(**{
            "ts_code": "",
            "name": "",
            "exchange": "",
            "market": "",
            "is_hs": "",
            "list_status": "",
            "limit": "",
            "offset": ""
        }, fields=fields_list)
        stock_list = df.values
        all_data = []
        all_stock = self.env['finance.stock.basic'].search([])
        for stock_data in stock_list:
            stock_symbol = stock_data[fields_list.index('symbol')]
            if all_stock.filtered(lambda x: x.symbol == stock_symbol):
                continue

            tmp_data = {fields_key: stock_data[fields_list.index(fields_key)] for fields_key in save_fields_list}

            list_status = stock_data[fields_list.index('list_status')]
            is_hs = stock_data[fields_list.index('is_hs')]
            exchange = stock_data[fields_list.index('exchange')]
            tmp_data.update({
                'list_status': list_status if list_status in ['L', 'D', 'P'] else 'O',
                'is_hs': is_hs if is_hs in ['N', 'S', 'H'] else 'N',
                'exchange': exchange if exchange in ['SSE', 'SZSE'] else 'OTHER'
            })
            all_data.append(tmp_data)
        self.create(all_data)

    def hook_process_link_basic_company(self):
        company_ids = self.env['finance.stock.company'].search([('ts_code', 'in', self.mapped('ts_code'))])
        for stock_id in self:
            company_id = company_ids.filtered(lambda x: x.ts_code == stock_id.ts_code)
            if company_id:
                _logger.info('link: {}'.format(stock_id.ts_code))
                stock_id.stock_company_id = company_id.id

    def cron_sync_company_data(self):
        res = self.env['finance.stock.basic'].search([('stock_company_id', '=', False)], limit=8)
        res.hook_process_link_basic_company()
        res.get_update_company_data()

    def get_update_company_data(self):
        """
        上市公司信息
        """
        fields_list = ["ts_code", "exchange", "chairman", "manager", "secretary",
                       "reg_capital", "setup_date", "province", "city", "website", "email",
                       "employees", "office", "ann_date", "business_scope", "main_business", "introduction"]
        save_fields_list = ["ts_code", "chairman", "manager", "secretary",
                            "reg_capital", "setup_date", "province", "city", "website", "email",
                            "employees", "office", "ann_date", "business_scope", "main_business", "introduction"]
        ts_pro = ts.pro_api(TS_TOKEN)
        company_ids = self.env['finance.stock.company'].search([('ts_code', 'in', self.mapped('ts_code'))])
        for stock_id in self:
            _logger.info('获取上市公司信息: {}'.format(stock_id.symbol))
            if company_ids.filtered(lambda x: x.ts_code == stock_id.ts_code):
                continue
            try:
                df = ts_pro.stock_company(**{
                    "ts_code": stock_id.ts_code,
                    "exchange": "",
                    "status": "",
                    "limit": "",
                    "offset": ""
                }, fields=fields_list)
            except Exception as e:
                raise UserError('异常: {}'.format(e))
            company_values = df.values
            company_obj = self.env['finance.stock.company']
            all_company = company_obj.search([])
            for company_data in company_values:
                company_ts_code = company_data[fields_list.index('ts_code')]
                if all_company.filtered(lambda x: x.ts_code == company_ts_code):
                    continue
                tmp_data = {
                    field_name: company_data[fields_list.index(field_name)] for field_name in save_fields_list
                }
                exchange = company_data[fields_list.index('exchange')]
                tmp_data.update({
                    'exchange': exchange if exchange in ['SSE', 'SZSE'] else 'OTHER',
                    'security_code': stock_id.symbol
                })
                res = company_obj.create(tmp_data)
                stock_id.write({
                    'stock_company_id': res.id
                })

    def parse_main_data(self, stock_main_id, main_res):
        secucode = main_res.get('SECUCODE')
        report_date = main_res.get('REPORT_DATE')
        if stock_main_id.filtered(lambda x: x.report_date == report_date):
            return {}
        res = {
            'chzzl': main_res.get('CHZZL'),
            'xsjll': main_res.get('XSJLL'),
            'xsmll': main_res.get('XSMLL'),
            'roejq': main_res.get('ROEJQ'),
            'zcfzl': main_res.get('ZCFZL'),
            'total_operate_reve': main_res.get('TOTALOPERATEREVE'),
            'secucode': main_res.get('SECUCODE'),
            'security_code': main_res.get('SECURITY_CODE'),
            'security_name_abbr': main_res.get('SECURITY_NAME_ABBR'),
            'org_code': main_res.get('ORG_CODE'),
            'org_type': main_res.get('ORG_TYPE'),
            'report_date': main_res.get('REPORT_DATE'),
            'report_type': main_res.get('REPORT_TYPE'),
            'report_date_name': main_res.get('REPORT_DATE_NAME'),
            'security_type_code': main_res.get('SECURITY_TYPE_CODE'),
            'notice_date': main_res.get('NOTICE_DATE'),
            'update_date': main_res.get('UPDATE_DATE'),
            'currency': main_res.get('CURRENCY'),
            'epsjb': main_res.get('EPSJB'),
            'epskcjb': main_res.get('EPSKCJB'),
            'epsxs': main_res.get('EPSXS'),
            'bps': main_res.get('BPS'),
            'mgzbgj': main_res.get('MGZBGJ'),
            'mgwfrplr': main_res.get('MGWFPLR'),
            'mgjyxjje': main_res.get('MGJYXJJE'),
            'mlr': main_res.get('MLR'),
            'parent_net_profit': main_res.get('PARENTNETPROFIT'),
            'kcfjcxsyjlr': main_res.get('KCFJCXSYJLR'),
            'totaloperaterevetz': main_res.get('TOTALOPERATEREVETZ'),
            'main_json': json.dumps(main_res)
        }
        _logger.info('主要指标: {}'.format(report_date))
        return res

    def cron_fetch_main_data(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_update_main_data()

    def get_update_main_data(self):
        """
        主要指标
        """
        all_main_ids = self.env['finance.stock.main.data'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            _logger.info('获取主要指标信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            payloads = {
                'code': security_code,
                'type': '0'
            }
            res = requests.get(stock_id.main_data_url, params=payloads, headers=headers)
            result = res.json().get('data')
            if not result:
                continue
            stock_main_id = all_main_ids.filtered(lambda x: x.stock_id == stock_id)
            main_data = []
            for main_res in result:
                data = self.parse_main_data(stock_main_id, main_res)
                if not data:
                    continue
                main_data.append((0, 0, data))
            stock_id.write({
                'main_data_ids': main_data
            })

    def fetch_zcfbz_data(self, query_dates, security_code, default_company_type=4, retry=False):
        finance_zcfzb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/zcfzbAjaxNew'
        payloads = {
            'companyType': default_company_type,
            'reportDateType': 0,
            'reportType': 1,
            'dates': query_dates,
            'code': security_code,
        }
        res = requests.get(finance_zcfzb_url, params=payloads, headers=headers)
        data = res.json().get('data')
        if not data and not retry:
            return self.fetch_zcfbz_data(query_dates, security_code, default_company_type=3, retry=True)
        return res

    def cron_fetch_zcfzb(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_zcfzb_data()

    def split_default_period_5(self, query_dates, split_count=5):
        date_split = []
        for loop_count in range(0, math.ceil(len(query_dates) / split_count)):
            try:
                current_date = query_dates[loop_count * 5: (loop_count + 1) * 5]
            except Exception as e:
                continue
            date_split.append(current_date)
        return date_split

    def get_diff_date(self, all_report_date, query_dates):
        all_date = [self.convert_datetime_to_date(x) for x in all_report_date if self.convert_datetime_to_date(x)]
        diff_date = set(query_dates) - set(all_date)
        if diff_date:
            return sorted(diff_date)
        return []

    def convert_str_to_datetime(self, datetime_str):
        try:
            date = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
            return date
        except Exception as e:
            return datetime_str

    def convert_datetime_to_date(self, date_datetime):
        try:
            return date_datetime.strftime('%Y-%m-%d')
        except Exception as e:
            return None

    def _get_zcfzb_data(self, query_dates):
        """
        资产负债表
        """

        for stock_id in self:

            _logger.info('获取资产负债表信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            stock_zcfzb = self.env['finance.stock.zcfzb'].search([('stock_id', '=', stock_id.id)])

            diff_date = self.get_diff_date(stock_zcfzb.mapped('report_date'), query_dates)
            if not diff_date:
                continue
            query_dates = ','.join(str(x) for x in diff_date)
            res = self.fetch_zcfbz_data(query_dates, security_code)

            data = res.json().get('data')
            if not data:
                continue
            all_data = []
            exist_period = []

            for line_data in data:
                secucode = line_data.get('SECUCODE')
                report_date = line_data.get('REPORT_DATE')
                if stock_zcfzb.filtered(lambda x: x.report_date == report_date):
                    continue
                if report_date in exist_period:
                    continue
                exist_period.append(report_date)
                tmp_data = {
                    'zcfbb_json': json.dumps(line_data),
                    'secucode': secucode,
                    'security_code': line_data.get('SECURITY_CODE'),
                    'security_name_abbr': line_data.get('SECURITY_NAME_ABBR'),
                    'org_code': line_data.get('ORG_CODE'),
                    'org_type': line_data.get('ORG_TYPE'),
                    'report_date': report_date,
                    'report_type': line_data.get('REPORT_TYPE'),
                    'report_date_name': line_data.get('REPORT_DATE_NAME'),
                    'security_type_code': line_data.get('SECURITY_TYPE_CODE'),
                    'notice_date': line_data.get('NOTICE_DATE'),
                    'update_date': line_data.get('UPDATE_DATE'),
                    'currency': line_data.get('CURRENCY'),
                    'total_assets': line_data.get('TOTAL_ASSETS'),
                    'total_current_assets': line_data.get('TOTAL_CURRENT_ASSETS'),
                    'total_current_liab': line_data.get('TOTAL_CURRENT_LIAB'),
                    'total_equity': line_data.get('TOTAL_EQUITY'),
                    'total_liab_equity': line_data.get('TOTAL_LIAB_EQUITY'),
                    'total_liablifties': line_data.get('TOTAL_LIABILITIES'),
                    'total_noncurrent_assets': line_data.get('TOTAL_NONCURRENT_ASSETS'),
                    'total_noncurrent_liab': line_data.get('TOTAL_NONCURRENT_LIAB'),
                    'total_other_payable': line_data.get('TOTAL_OTHER_PAYABLE'),
                    'total_other_rece': line_data.get('TOTAL_OTHER_RECE'),
                    'total_parent_equity': line_data.get('TOTAL_PARENT_EQUITY'),
                }
                _logger.info('资产负债表: {}'.format(report_date))
                all_data.append((0, 0, tmp_data))
            if all_data:
                stock_id.write({
                    'zcfzb_ids': all_data
                })

    def get_zcfzb_data(self):
        """
        资产负债表
        """

        query_dates = self.get_default_period_date()
        split_date = self.split_default_period_5(query_dates)
        for current_date in split_date:
            try:
                self._get_zcfzb_data(current_date)
            except Exception as e:
                _logger.error('资产负债表获取出错! {}'.format(e))
                continue

    def cron_fetch_rpt_lico_fn_cpd(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_rpt_lico_fn_cpd_data()

    def get_rpt_lico_fn_cpd_data(self):
        """
        业绩报表
        """
        rpt_lico_fn_cpd_url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
        all_rpt_ids = self.env['finance.stock.report'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            _logger.info('获取业绩报表信息: {}'.format(stock_id.symbol))
            payload_data = {
                'callback': '',
                'sortColumns': 'REPORTDATE',
                'sortTypes': -1,
                'pageSize': 50,
                'pageNumber': 1,
                'columns': 'ALL',
                'filter': '(SECURITY_CODE={})'.format(stock_id.symbol),
                'reportName': 'RPT_LICO_FN_CPD'
            }
            res = requests.get(rpt_lico_fn_cpd_url, params=payload_data, headers=headers)
            result = res.json().get('result', {}).get('data')
            all_data = []
            if not result:
                continue
            stock_all_rpt = all_rpt_ids.filtered(lambda x: x.stock_id == stock_id)
            exist_period = []
            for line_data in result:
                secucode = line_data.get('SECUCODE')
                report_date = line_data.get('REPORTDATE')
                if stock_all_rpt.filtered(lambda x: x.reportdate == report_date):
                    continue
                if report_date in exist_period:
                    continue
                exist_period.append(report_date)
                data = {
                    'basic_eps': line_data.get('BASIC_EPS'),
                    'bps': line_data.get('BASIC_EPS'),
                    'data_type': line_data.get('DATATYPE'),
                    'data_year': line_data.get('DATAYEAR'),
                    'date_mmdd': line_data.get('DATEMMDD'),
                    'deduct_basic_eps': line_data.get('DEDUCT_BASIC_EPS'),
                    'eitime': line_data.get('EITIME'),
                    'isnew': line_data.get('ISNEW'),
                    'mgjyxjje': line_data.get('MGJYXJJE'),
                    'notice_date': line_data.get('NOTICE_DATE'),
                    'org_code': line_data.get('ORG_CODE'),
                    'parent_netprofit': line_data.get('BASIC_EPS'),
                    'publishname': line_data.get('PUBLISHNAME'),
                    'qdate': line_data.get('QDATE'),
                    'reportdate': line_data.get('REPORTDATE'),
                    'secucode': line_data.get('SECUCODE'),
                    'security_code': line_data.get('SECURITY_CODE'),
                    'security_name_abbr': line_data.get('SECURITY_NAME_ABBR'),
                    'security_type': line_data.get('SECURITY_TYPE'),
                    'security_type_code': line_data.get('SECURITY_TYPE_CODE'),
                    'sjlhz': line_data.get('SJLHZ'),
                    'sjltz': line_data.get('SJLTZ'),
                    'total_operate_income': line_data.get('TOTAL_OPERATE_INCOME'),
                    'trade_market': line_data.get('TRADE_MARKET'),
                    'trade_market_code': line_data.get('TRADE_MARKET_CODE'),
                    'trade_market_zjg': line_data.get('TRADE_MARKET_ZJG'),
                    'weightavg_roe': line_data.get('BASIC_EPS'),
                    'yshz': line_data.get('YSHZ'),
                    'ystz': line_data.get('YSTZ'),
                    'report_json': json.dumps(line_data)
                }
                _logger.info('业绩报表: {}'.format(report_date))
                all_data.append((0, 0, data))
            stock_id.write({
                'report_ids': all_data
            })

    def fetch_lrb_data(self, query_dates, security_code, default_company_type=4, retry=False):
        finance_lrb_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/lrbAjaxNew'
        payloads = {
            'companyType': default_company_type,
            'reportDateType': 0,
            'reportType': 1,
            'dates': query_dates,
            'code': security_code,
        }
        res = requests.get(finance_lrb_url, params=payloads, headers=headers)
        try:
            data = res.json().get('data')
        except Exception as e:
            _logger.error('获取利润表出错: {}, {}'.format(e, res.text))
            data = False
        if not data and not retry:
            return self.fetch_lrb_data(query_dates, security_code, default_company_type=3, retry=True)
        return res

    def fetch_xjllb_data(self, query_dates, security_code, default_company_type=4, retry=False):
        finance_xjllb_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/xjllbAjaxNew'
        payloads = {
            'companyType': default_company_type,
            'reportDateType': 0,
            'reportType': 1,
            'dates': query_dates,
            'code': security_code,
        }
        res = requests.get(finance_xjllb_url, params=payloads, headers=headers)
        try:
            data = res.json().get('data')
        except Exception as e:
            _logger.error('获取现金流量表出错: {}, {}'.format(e, res.text))
            data = False
        if not data and not retry:
            return self.fetch_xjllb_data(query_dates, security_code, default_company_type=3, retry=True)
        return res

    def cron_fetch_lrb(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_lrb_data()

    def cron_fetch_xjllb(self):
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_xjllb_data()

    def get_xjllb_data(self):
        """
            现金流量表
        """
        query_dates = self.get_default_period_date()
        split_date = self.split_default_period_5(query_dates)
        for current_date in split_date:
            try:
                self._get_xjllb_data(current_date)
            except Exception as e:
                _logger.error('资产利润表获取出错! {}'.format(e))
                continue

    def _get_xjllb_data(self, query_dates):
        """
            现金流量表
        """
        all_xjllb = self.env['finance.stock.xjllb'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            stock_xjllb_id = all_xjllb.filtered(lambda x: x.stock_id == stock_id)
            _logger.info('获取现金流量表信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)

            diff_date = self.get_diff_date(stock_xjllb_id.mapped('report_date'), query_dates)
            if not diff_date:
                continue
            query_dates = ','.join(str(x) for x in diff_date)

            res = self.fetch_xjllb_data(query_dates, security_code)

            data = res.json().get('data')
            if not data:
                continue
            all_data = []
            exist_period = []
            for line_data in data:
                secucode = line_data.get('SECUCODE')
                report_date = line_data.get('REPORT_DATE')
                if stock_xjllb_id.filtered(lambda x: x.report_date == report_date):
                    continue
                if report_date in exist_period:
                    continue
                exist_period.append(report_date)
                _logger.info('获取现金流量表期间数据: {}'.format(report_date))
                data = {
                    'xjllb_json': json.dumps(line_data),
                    'secucode': secucode,
                    'security_code': line_data.get('SECURITY_CODE'),
                    'operate_in_flow': line_data.get('TOTAL_OPERATE_INFLOW'),
                    'operate_out_flow': line_data.get('TOTAL_OPERATE_OUTFLOW'),
                    'report_date': report_date,
                    'report_type': line_data.get('REPORT_TYPE'),
                }
                _logger.info('现金流量表: {}'.format(report_date))
                all_data.append((0, 0, data))
            stock_id.write({
                'xjllb_ids': all_data
            })

    def get_lrb_data(self):
        """
            利润表
        """
        query_dates = self.get_default_period_date()
        split_date = self.split_default_period_5(query_dates)
        for current_date in split_date:
            try:
                self._get_lrb_data(current_date)
            except Exception as e:
                _logger.error('资产利润表获取出错! {}'.format(e))
                continue

    def _get_lrb_data(self, query_dates):
        """
            利润表
        """
        all_lrb = self.env['finance.stock.lrb'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            stock_lrb_id = all_lrb.filtered(lambda x: x.stock_id.id == stock_id.id)

            diff_date = self.get_diff_date(stock_lrb_id.mapped('report_date'), query_dates)
            if not diff_date:
                continue
            query_dates = ','.join(str(x) for x in diff_date)

            _logger.info('获取利润表信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            res = self.fetch_lrb_data(query_dates, security_code)

            data = res.json().get('data')
            if not data:
                continue
            all_data = []
            exist_period = []
            for line_data in data:
                secucode = line_data.get('SECUCODE')
                report_date = line_data.get('REPORT_DATE')
                if stock_lrb_id.filtered(lambda x: x.report_date == report_date):
                    continue
                if report_date in exist_period:
                    continue
                exist_period.append(report_date)
                _logger.info('获取利润表期间数据: {}'.format(report_date))
                data = {
                    'lrb_json': json.dumps(line_data),
                    'secucode': secucode,
                    'security_code': line_data.get('SECURITY_CODE'),
                    'security_name_abbr': line_data.get('SECURITY_NAME_ABBR'),
                    'org_code': line_data.get('ORG_CODE'),
                    'org_type': line_data.get('ORG_TYPE'),
                    'report_date': report_date,
                    'report_type': line_data.get('REPORT_TYPE'),
                    'continued_netprofit': line_data.get('CONTINUED_NETPROFIT'),
                    'interest_expense': line_data.get('INTEREST_EXPENSE'),
                }
                _logger.info('利润表: {}'.format(report_date))
                all_data.append((0, 0, data))
            try:
                stock_id.write({
                    'lrb_ids': all_data
                })
            except Exception as e:
                _logger.error('出错了: {}'.format(e))

    def cron_fetch_business(self):
        """
        经营分析
        """
        res = self.env['finance.stock.basic'].search([])
        for x in res:
            x.with_delay().get_business_analysis()

    def get_business_analysis(self):
        """
            MAINOP_TYPE: 分类：1（按行业分类）；2（按产品分类）；3（按地区分类）
            RANK: 1（外币）；2（人民币）
            MBI_RATIO：收入比例
            """
        business_analysis_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax'
        all_business_ids = self.env['finance.stock.business'].search([('stock_id', 'in', self.ids)])
        for stock_id in self:
            stock_business_ids = all_business_ids.filtered(lambda x: x.stock_id == stock_id)
            start_time = time.time()
            _logger.info('开始获取经营分析信息: {}'.format(stock_id.symbol))
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            payload_data = {
                'code': security_code
            }
            res = requests.get(business_analysis_url, params=payload_data, headers=headers, timeout=10.0)
            _logger.info('开始解析经营分析信息: {}, 获取数据耗时: {}'.format(stock_id.symbol, time.time() - start_time))
            result = res.json().get('zygcfx')
            all_data = []
            if not result:
                continue
            for business_data in result:
                secucode = business_data.get('SECUCODE')
                report_date = business_data.get('REPORT_DATE')
                if stock_business_ids.filtered(lambda x: x.report_date == report_date):
                    continue
                tmp = {
                    'business_json': json.dumps(business_data),
                    'gross_profit_ratio': business_data.get('GROSS_RPOFIT_RATIO'),
                    'item_name': business_data.get('ITEM_NAME'),
                    'mainop_type': business_data.get('MAINOP_TYPE'),
                    'main_business_cost': business_data.get('MAIN_BUSINESS_COST'),
                    'main_business_income': business_data.get('MAIN_BUSINESS_INCOME'),
                    'main_business_profit': business_data.get('MAIN_BUSINESS_RPOFIT'),
                    'mbc_ratio': business_data.get('MBC_RATIO'),
                    'mbi_ratio': business_data.get('MBI_RATIO'),
                    'mbr_ratio': business_data.get('MBR_RATIO'),
                    'rank': business_data.get('RANK'),
                    'security_code': business_data.get('SECURITY_CODE'),
                    'report_date': report_date,
                    'secucode': secucode,
                }
                _logger.info('经营分析: {}'.format(report_date))
                all_data.append((0, 0, tmp))
            stock_id.with_delay().write({
                'business_ids': all_data
            })

    def cron_fetch_peg_value(self):
        res = self.env['finance.stock.basic'].search([('peg_car', '=', False)])
        for x in res:
            x.with_delay().get_east_money_peg_value()
        # res.get_east_money_peg_value()

    def get_east_money_peg_value(self):
        req_url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
        for stock_id in self:
            _logger.info('获取PEG信息: {}'.format(stock_id.symbol))
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
                'filter': '(SECURITY_CODE="{}")'.format(stock_id.symbol),
                '_': int(time.time() * 1000)
            }
            res = requests.get(req_url, params=payload_data, headers=headers)
            if not res.json().get('result'):
                continue
            result_data = res.json().get('result', {}).get('data', [])
            if not result_data:
                continue
            result_data = result_data[0]
            stock_id.write({
                'peg_car': result_data.get('PEG_CAR'),
                'pb_mrq': result_data.get('PEG_MRQ'),
                'pcf_ocf_tim': result_data.get('PCF_OCF_TTM'),
            })


class FinanceStockMainData(models.Model):
    _name = 'finance.stock.main.data'
    _description = '主要指标'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码和时间唯一')
    ]
    _rec_name = 'security_code'

    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    secucode = fields.Char('SECUCODE', required=True)
    security_code = fields.Char('SECURITY_CODE')
    security_name_abbr = fields.Char('SECURITY_NAME_ABBR')
    org_code = fields.Char('ORG_CODE')
    org_type = fields.Char('ORG_TYPE')
    report_date = fields.Char('REPORT_DATE')
    report_type = fields.Char('REPORT_TYPE')
    report_date_name = fields.Char('REPORT_DATE_NAME')
    security_type_code = fields.Char('SECURITY_TYPE_CODE')
    notice_date = fields.Char('NOTICE_DATE')
    update_date = fields.Char('UPDATE_DATE')
    currency = fields.Char('CURRENCY')
    epsjb = fields.Char('EPSJB')
    epskcjb = fields.Char('EPSKCJB')
    epsxs = fields.Char('EPSXS')
    bps = fields.Char('BPS')
    mgzbgj = fields.Char('MGZBGJ')
    mgwfrplr = fields.Char('MGWFPLR')
    mgjyxjje = fields.Char('MGJYXJJE')
    mlr = fields.Char('MLR')
    parent_net_profit = fields.Char('PARENTNETPROFIT')
    kcfjcxsyjlr = fields.Char('KCFJCXSYJLR')
    totaloperatereve = fields.Char('TOTALOPERATEREVE')
    totaloperaterevetz = fields.Char('TOTALOPERATEREVETZ')
    chzzl = fields.Char('存货周转率')
    xsjll = fields.Char('净利率')
    xsmll = fields.Char('毛利率')
    roejq = fields.Char('净资产收益率')
    zcfzl = fields.Char('资产负债率')
    total_operate_reve = fields.Char('营业总收入')
    main_json = fields.Char('JSON')

    def update_json_value(self):
        for line_id in self:
            main_json = json.loads(line_id.main_json)
            totaloperatereve = main_json.get('TOTALOPERATEREVE')
            line_id.write({
                'totaloperatereve': totaloperatereve
            })


class FinanceStockHolder(models.Model):
    _name = 'finance.stock.holder'
    _description = '基金机构'
    _sql_constraints = [
        ('unique_ts_code_report_date_org_name', 'unique(ts_code, report_date, org_name)', '股票代码、日期必须唯一')
    ]

    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    ts_code = fields.Char('股票代码', required=True)
    security_code = fields.Char('SECURITY CODE')
    org_name = fields.Char('机构名称')
    report_date = fields.Char('REPORT DATE')
    rate = fields.Char('占比')
    holder_json = fields.Char('HOLDER JSON')


class FinanceStockCompany(models.Model):
    _name = 'finance.stock.company'
    _description = '上市公司基本信息'
    _rec_name = 'ts_code'
    _sql_constraints = [
        ('unique_ts_code', 'unique(ts_code)', '股票代码必须唯一')
    ]

    ts_code = fields.Char('股票代码', required=True)
    security_code = fields.Char('SECURITY CODE')
    exchange = fields.Selection([
        ('SSE', '上交所'),
        ('SZSE', '深交所'),
        ('OTHER', '其它')
    ], string='交易所代码')
    chairman = fields.Char('法人代表')
    manager = fields.Char('总经理')
    secretary = fields.Char('董秘')
    reg_capital = fields.Char('注册资本')
    setup_date = fields.Char('注册日期')
    province = fields.Char('所在省份')
    city = fields.Char('所在城市')
    introduction = fields.Char('公司介绍')
    website = fields.Char('公司主页')
    email = fields.Char('电子邮件')
    office = fields.Char('办公室')
    ann_date = fields.Char('公告日期')
    employees = fields.Char('雇员')
    emp_num = fields.Char('雇员人数')
    reg_num = fields.Char('工商登记')
    address_postcode = fields.Char('邮政编码')
    main_business = fields.Char('主要业务及产品')
    business_scope = fields.Char('经营范围')
    industry_csrc = fields.Char('所属行业')
    survey_json = fields.Char('SURVEY JSON')

    def get_security_code(self, code):
        if code.startswith('6') or code.startswith('5') or code.startswith('9'):
            prefix_code = 'SH'
            sec_id = '1'
        else:
            prefix_code = 'SZ'
            sec_id = '0'
        return prefix_code + code, sec_id + '.' + code

    def cron_fetch_company_survey(self):
        """
        员工人数
        """
        res = self.env['finance.stock.company'].search([('emp_num', '=', False)])
        for x in res:
            x.with_delay().get_company_survey()
            # res.get_company_survey()

    def get_company_survey(self):
        company_survey_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/PageAjax'
        for survey_id in self:
            _logger.info('获取公司信息: {}'.format(survey_id.ts_code))
            security_code = survey_id.ts_code.split('.')[0]
            security_code, sec_id = self.get_security_code(security_code)
            payload_data = {
                'code': security_code
            }
            res = requests.post(company_survey_url, data=payload_data, headers=headers)
            # 资本资料
            jbzl = res.json().get('jbzl')
            if not jbzl:
                continue
            survey_id.write({
                'emp_num': jbzl[0].get('EMP_NUM'),
                'reg_num': jbzl[0].get('REG_NUM'),
                'address_postcode': jbzl[0].get('ADDRESS_POSTCODE'),
                'survey_json': json.dumps(jbzl[0]),
                'industry_csrc': jbzl[0].get('INDUSTRYCSRC1')
            })

    def fetch_company_manager_info(self, stock_code):
        try:
            manager_info = get_10jqka_company_manager_info(stock_code)
        except Exception as e:
            return
        manger_ids = self.env['stock.company.manager'].search([
            ('security_code', '=', stock_code)
        ])
        manger_ids.unlink()
        manger_ids.create([{
            'security_code': stock_code,
            'tc': x.get('tc'),
            'tc_url': x.get('tc_url'),
            'tc_name': x.get('tc_name'),
            'tc_title': x.get('title'),
            'td1': x.get('direct_shr'),
            'td2': x.get('shr'),
            'tr_json': json.dumps(x),
        } for x in manager_info])

    def cron_get_company_manager(self):
        # 数据来源: 同花顺
        res = self.env['finance.stock.company'].search([])
        for x in res:
            x.with_delay().fetch_company_manager_info(x.security_code)

    def manual_fetch_manger(self):
        for company_id in self:
            self.fetch_company_manager_info(company_id.security_code)