# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import datetime
from datetime import timedelta
import json

_logger = logging.getLogger(__name__)


def float_or_zero(float_str):
    try:
        return float(float_str)
    except Exception as e:
        return 0.0


class FinanceFiscalData(models.Model):
    _name = 'finance.fiscal.data'
    _description = 'table: fiscal_data处理后的财务信息'
    _rec_name = 'secucode'

    report_date = fields.Datetime('日期', index=True)
    period_type = fields.Selection([
        ('year', '年'),
        ('quarter', '季度'),
        ('month', '月份'),
        ('other', '其它')
    ], default='quarter', string='日期类型', index=True)

    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    stock_id = fields.Many2one('finance.stock.basic', index=True)
    per_share = fields.Float(u'每股收益')
    per_share_mm_ratio = fields.Float('每股收益环比', help='环比上个财务期间，例如本年Q1环比去年Q1')
    per_share_speed = fields.Float('每股收益增速', help='相邻环比值的比较')
    operate_revenue = fields.Float('营业收入')
    operate_revenue_mm_ratio = fields.Float('营业收入环比', help='环比上个财务期间，例如本年Q1环比去年Q1')
    operate_revenue_speed = fields.Float('营业收入增速', help='相邻环比值的比较')
    roe = fields.Float('净资产收益率')
    roe_mm_ratio = fields.Float('ROE环比', help='环比上个财务期间，例如本年Q1环比去年Q1')
    roe_speed = fields.Float('ROE增速', help='相邻环比值的比较')
    operate_cash_flow = fields.Float('经营性现金流')
    net_working_capital = fields.Float('净运营资本')
    accounts_receivable = fields.Float('应收账款')
    accounts_receivable_mm_ratio = fields.Float('应收账款环比', help='环比上个财务期间，例如本年Q1环比去年Q1')
    accounts_receivable_speed = fields.Float('应收账款增速', help='相邻环比值的比较')
    revenue_quality = fields.Float('收入质量', help=' = 应收账款 / 营业收入')
    total_share_capital = fields.Float('总股本')
    pcf_ocf_tim = fields.Float('市现率')
    pb_mrq = fields.Float('市净率')
    pe_ratio = fields.Float('市盈率')
    trade_ratio = fields.Float('市销率')
    peg = fields.Float('PEG')
    gw_netast_rat = fields.Char('商誉')
    net_asset_ratio = fields.Float('商誉/净资产')
    employee = fields.Float('员工数量')
    operate_revenue_per = fields.Float('营业收入/员工数量')
    inventory_turnover = fields.Float('库存周转次数')
    asset_liability_ratio = fields.Float('资产负债率')
    profit_margin = fields.Float('净利率')
    gross_profit_ratio = fields.Float('毛利率')
    net_asset = fields.Float('净资产')
    sign = fields.Char('Sign')

    def get_default_period(self, all_period=False):
        search_today = datetime.date.today()
        search_month = search_today.month
        search_year = search_today.year
        search_year = int(search_year)
        search_month = int(search_month)
        search_period = []
        for x in range(search_year - 2, search_year):
            search_period += [f'{x}-03-31 00:00:00', f'{x}-06-30 00:00:00', f'{x}-09-30 00:00:00',
                              f'{x}-12-31 00:00:00']
        if all_period:
            search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                              f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        else:
            if search_month < 3:
                search_period += [f'{search_year}-03-31 00:00:00']
            elif 3 <= search_month < 6:
                search_period += [f'{search_year}-03-31 00:00:00']
            elif 6 <= search_month < 9:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00']
            elif 9 <= search_month < 12:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00']
            else:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        return search_period

    def update_fiscal_data(self):
        for line_id in self:
            update_data = self.parse_fiscal_data(self.stock_id, str(self.report_date))
            line_id.write(update_data)

    def cron_fetch_fiscal_data(self):
        all_period = self.get_default_period()
        all_period = all_period[:-4]
        all_fiscal_ids = self.env['finance.fiscal.data'].search([])
        all_stock_ids = self.env['finance.stock.basic'].search([('id', 'not in', all_fiscal_ids.stock_id.ids)])
        for stock_id in all_stock_ids:
            self.with_delay().generate_fiscal_data(stock_ids=stock_id, report_date=all_period)

    def get_operate_cash_flow(self, xjllb_id):
        xjllb_json = xjllb_id.xjllb_json
        if not xjllb_json:
            return 0.0
        xjllb_json = json.loads(xjllb_json)
        return float_or_zero(xjllb_json.get('TOTAL_OPERATE_INFLOW')) - float_or_zero(
            xjllb_json.get('TOTAL_OPERATE_OUTFLOW'))

    def get_per_share_value(self, lrb_id):
        lrb_json = lrb_id.lrb_json
        if not lrb_json:
            return 0.0
        lrb_json = json.loads(lrb_json)
        return float_or_zero(lrb_json.get('DILUTED_EPS'))

    def parse_fiscal_data(self, stock_id, period_date):
        survey_ids = self.env['finance.stock.company'].search([('ts_code', '=', stock_id.ts_code)])
        main_ids = self.env['finance.stock.main.data'].search([('stock_id', '=', stock_id.id)])
        business_ids = self.env['finance.stock.business'].search([('stock_id', '=', stock_id.id)])
        lrb_ids = self.env['finance.stock.lrb'].search([('stock_id', '=', stock_id.id)])
        xjllb_ids = self.env['finance.stock.xjllb'].search([('stock_id', '=', stock_id.id)])
        zcfzb_ids = self.env['finance.stock.zcfzb'].search([('stock_id', '=', stock_id.id)])
        report_ids = self.env['finance.stock.report'].search([('stock_id', '=', stock_id.id)])

        survey_id = survey_ids.filtered(lambda x: x.ts_code == stock_id.ts_code)
        xjllb_id = xjllb_ids.filtered(lambda x: x.stock_id == stock_id)

        # 主要指标
        main_id = main_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)

        # 怎么判断海外呢？ mainop_type = '3' and '境外?海外?国外?' in item_name?
        business_id = business_ids.filtered(
            lambda x: x.stock_id == stock_id and
                      x.report_date == period_date and x.mainop_type == '3' and
                      ('境外' in x.item_name or '海外' in x.item_name or '国外' in x.item_name))

        # 利润表
        lrb_id = lrb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
        # 资产负债表
        zcfzb_id = zcfzb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
        report_id = report_ids.filtered(
            lambda x: x.stock_id == stock_id and x.reportdate == period_date)

        tmp_data = {
            'report_date': period_date,
            'period_type': 'quarter',
            # 每股收益
            'per_share': self.get_per_share_value(lrb_id),
            # 每股收益环比
            'per_share_mm_ratio': '',
            # 每股收益增速
            'per_share_speed': '',
            # 营业收入
            'operate_revenue': main_id.total_operate_reve,
            # 营业收入环比
            'operate_revenue_mm_ratio': '',
            # 营业收入增速
            'operate_revenue_speed': '',
            # ROE
            'roe': main_id.roejq,
            # ROE环比
            'roe_mm_ratio': '',
            # ROE增速
            'roe_speed': '',
            # 经营性现金流
            'operate_cash_flow': self.get_operate_cash_flow(xjllb_id),
            # 净运营资本
            'net_working_capital': '',
            # 应收账款
            'accounts_receivable': zcfzb_id.total_other_rece,
            # 应收账款环比
            'accounts_receivable_mm_ratio': '',
            # 应收账款增速
            'accounts_receivable_speed': '',
            # 收入质量
            'revenue_quality': '',
            # 总股本
            'total_share_capital': float_or_zero(stock_id.f84),
            # 市现率
            'pcf_ocf_tim': float_or_zero(stock_id.pcf_ocf_tim),
            # 市净率
            'pb_mrq': float_or_zero(stock_id.pb_mrq),
            # 市盈率
            'pe_ratio': '',
            # 市销率
            'trade_ratio': self.get_ratio(stock_id.f277, main_id.totaloperatereve),
            # PEG
            'peg': float_or_zero(stock_id.peg_car),
            # 商誉
            'gw_netast_rat': float_or_zero(stock_id.gw_netast_rat),
            # 商誉/净资产
            'net_asset_ratio': '',
            # 员工数
            'employee': float_or_zero(survey_id.emp_num),
            # 营业收入/员工数量
            'operate_revenue_per': self.get_ratio(report_id.total_operate_income, survey_id.emp_num),
            # 库存周转次数
            'inventory_turnover': float_or_zero(main_id.chzzl),
            # 资产负债率
            'asset_liability_ratio': float_or_zero(main_id.zcfzl),
            # 净利率
            'profit_margin': float_or_zero(main_id.xsjll),
            # 毛利率
            'gross_profit_ratio': float_or_zero(main_id.xsmll),
            # 净资产
            'net_asset': '',
        }
        return tmp_data

    def generate_fiscal_data(self, stock_ids=None, report_date=None):
        if report_date:
            all_period = report_date
        else:
            all_period = self.get_default_period()
        if stock_ids:
            all_stock_ids = stock_ids
        else:
            all_stock_ids = self.env['finance.stock.basic'].search([])

        all_data = []
        for stock_id in all_stock_ids:
            _logger.info('开始生成 [{}] 报表'.format(stock_id.symbol))
            survey_ids = self.env['finance.stock.company'].search([('ts_code', '=', stock_id.ts_code)])
            main_ids = self.env['finance.stock.main.data'].search([('stock_id', '=', stock_id.id)])
            business_ids = self.env['finance.stock.business'].search([('stock_id', '=', stock_id.id)])
            lrb_ids = self.env['finance.stock.lrb'].search([('stock_id', '=', stock_id.id)])
            zcfzb_ids = self.env['finance.stock.zcfzb'].search([('stock_id', '=', stock_id.id)])
            report_ids = self.env['finance.stock.report'].search([('stock_id', '=', stock_id.id)])
            all_fiscal_ids = self.env['finance.fiscal.data'].search([('stock_id', '=', stock_id.id)])
            xjllb_ids = self.env['finance.stock.xjllb'].search([('stock_id', '=', stock_id.id)])

            for period_date in all_period:
                fiscal_id = all_fiscal_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
                if fiscal_id:
                    continue
                survey_id = survey_ids.filtered(lambda x: x.ts_code == stock_id.ts_code)
                # 主要指标
                main_id = main_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)

                # 怎么判断海外呢？ mainop_type = '3' and '境外?海外?国外?' in item_name?
                business_id = business_ids.filtered(
                    lambda x: x.stock_id == stock_id and
                              x.report_date == period_date and x.mainop_type == '3' and
                              ('境外' in x.item_name or '海外' in x.item_name or '国外' in x.item_name))

                # 利润表
                lrb_id = lrb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
                # 资产负债表
                zcfzb_id = zcfzb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
                report_id = report_ids.filtered(
                    lambda x: x.stock_id == stock_id and x.reportdate == period_date)
                xjllb_id = xjllb_ids.filtered(lambda x: x.stock_id == stock_id)

                tmp_data = {
                    'secucode': stock_id.ts_code,
                    'security_code': stock_id.symbol,
                    'report_date': period_date,
                    'period_type': 'quarter',
                    'stock_id': stock_id.id,
                    # 每股收益
                    'per_share': self.get_per_share_value(lrb_id),
                    # 每股收益环比
                    'per_share_mm_ratio': '',
                    # 每股收益增速
                    'per_share_speed': '',
                    # 营业收入
                    'operate_revenue': main_id.total_operate_reve,
                    # 营业收入环比
                    'operate_revenue_mm_ratio': '',
                    # 营业收入增速
                    'operate_revenue_speed': '',
                    # ROE
                    'roe': main_id.roejq,
                    # ROE环比
                    'roe_mm_ratio': '',
                    # ROE增速
                    'roe_speed': '',
                    # 经营性现金流
                    'operate_cash_flow': self.get_operate_cash_flow(xjllb_id),
                    # 净运营资本
                    'net_working_capital': '',
                    # 应收账款
                    'accounts_receivable': zcfzb_id.total_other_rece,
                    # 应收账款环比
                    'accounts_receivable_mm_ratio': '',
                    # 应收账款增速
                    'accounts_receivable_speed': '',
                    # 收入质量
                    'revenue_quality': '',
                    # 总股本
                    'total_share_capital': float_or_zero(stock_id.f84),
                    # 市现率
                    'pcf_ocf_tim': float_or_zero(stock_id.pcf_ocf_tim),
                    # 市净率
                    'pb_mrq': float_or_zero(stock_id.pb_mrq),
                    # 市盈率
                    'pe_ratio': '',
                    # 市销率
                    'trade_ratio': self.get_ratio(stock_id.f277, main_id.totaloperatereve),
                    # PEG
                    'peg': float_or_zero(stock_id.peg_car),
                    # 商誉
                    'gw_netast_rat': float_or_zero(stock_id.gw_netast_rat),
                    # 商誉/净资产
                    'net_asset_ratio': '',
                    # 员工数
                    'employee': float_or_zero(survey_id.emp_num),
                    # 营业收入/员工数量
                    'operate_revenue_per': self.get_ratio(report_id.total_operate_income, survey_id.emp_num),
                    # 库存周转次数
                    'inventory_turnover': float_or_zero(main_id.chzzl),
                    # 资产负债率
                    'asset_liability_ratio': float_or_zero(main_id.zcfzl),
                    # 净利率
                    'profit_margin': float_or_zero(main_id.xsjll),
                    # 毛利率
                    'gross_profit_ratio': float_or_zero(main_id.xsmll),
                    # 净资产
                    'net_asset': '',
                }
                # 更新？
                # if fiscal_id:
                #     fiscal_id.write(tmp_data)
                all_data.append(tmp_data)
        if all_data:
            res = self.create(all_data)
            _logger.info('创建【处理后财务信息】成功: {}'.format(res))

    def get_ratio(self, left_value, right_value):
        try:
            trade_ratio = float_or_zero(left_value) / float_or_zero(right_value)
        except Exception as e:
            trade_ratio = 0
        return trade_ratio

    def update_mm_ratio_value(self):
        for fiscal_id in self:
            stock_fiscal_ids = self.env['finance.fiscal.data'].search([
                ('stock_id', '=', fiscal_id.stock_id.id)
            ])
            current_date = fiscal_id.report_date
            # 去年的期间
            mm_date = current_date.replace(current_date.year - 1)

            mm_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == mm_date)
            if not mm_fiscal_id:
                continue
            print('mm_fiscal_id: ', mm_fiscal_id, mm_date)

            fiscal_id.write({
                'operate_revenue_mm_ratio': self.get_ratio(mm_fiscal_id.operate_revenue, fiscal_id.operate_revenue),
                'per_share_mm_ratio': self.get_ratio(mm_fiscal_id.per_share, fiscal_id.per_share),
                'roe_mm_ratio': self.get_ratio(mm_fiscal_id.roe, fiscal_id.roe),
                'accounts_receivable_mm_ratio': self.get_ratio(mm_fiscal_id.accounts_receivable,
                                                               fiscal_id.accounts_receivable)
            })
        self.update_value_speed()

    def update_value_speed(self):
        for fiscal_id in self:
            stock_fiscal_ids = self.env['finance.fiscal.data'].search([
                ('stock_id', '=', fiscal_id.stock_id.id)
            ])
            current_date = fiscal_id.report_date

            last_q_month = current_date.month - 3
            if last_q_month == 0:
                last_q_date = datetime.datetime(current_date.year - 1, 12, current_date.day, current_date.hour,
                                                current_date.minute, current_date.second, current_date.microsecond)
            elif last_q_month > 0:
                last_q_date = datetime.datetime(current_date.year, current_date.month - 3, current_date.day,
                                                current_date.hour, current_date.minute, current_date.second,
                                                current_date.microsecond)
            else:
                last_q_date = None
            if not last_q_date:
                continue
            # 去年的期间
            last_year_date = current_date.replace(current_date.year - 1)
            ll_year_q_data = last_q_date.replace(current_date.year - 1)

            last_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == last_year_date)
            ll_q_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == ll_year_q_data)
            last_q_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == last_q_date)

            fiscal_id.write({
                'operate_revenue_speed': self.get_ratio(
                    self.get_ratio(fiscal_id.operate_revenue, last_q_fiscal_id.operate_revenue),
                    self.get_ratio(last_fiscal_id.operate_revenue, ll_q_fiscal_id.operate_revenue)),
                'per_share_speed': self.get_ratio(
                    self.get_ratio(fiscal_id.per_share, last_q_fiscal_id.per_share),
                    self.get_ratio(last_fiscal_id.per_share, ll_q_fiscal_id.per_share)),
                'roe_speed': self.get_ratio(
                    self.get_ratio(fiscal_id.roe, last_q_fiscal_id.roe),
                    self.get_ratio(last_fiscal_id.roe, ll_q_fiscal_id.roe)),
                'accounts_receivable_speed': self.get_ratio(
                    self.get_ratio(fiscal_id.accounts_receivable, last_q_fiscal_id.accounts_receivable),
                    self.get_ratio(last_fiscal_id.accounts_receivable, ll_q_fiscal_id.accounts_receivable)),
            })
