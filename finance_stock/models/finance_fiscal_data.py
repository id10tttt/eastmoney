# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import datetime
import calendar
import json
import itertools

_logger = logging.getLogger(__name__)


def float_or_zero(float_str):
    try:
        return float(float_str)
    except Exception as e:
        return 0.0


def verify_pairwise_increase(compare_list):
    return all(s <= t for s, t in itertools.pairwise(compare_list))


class FinanceFiscalData(models.Model):
    _name = 'finance.fiscal.data'
    _inherit = 'finance.stock.mixin'
    _description = 'table: fiscal_data处理后的财务信息'
    _rec_name = 'secucode'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票、日期必须唯一')
    ]
    _order = 'secucode, report_date desc'

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
    net_asset = fields.Float('净资产(股东权益合计)', help='资产负债表')
    sign = fields.Char('Sign')

    def _delete_invalidate_records(self, all_period, stock_ids):
        unlink_records = self.env['finance.fiscal.data']
        for stock_id in stock_ids:
            _logger.info('开始生成 [{}] 报表'.format(stock_id.symbol))
            lrb_ids = self.env['finance.stock.lrb'].search([('stock_id', '=', stock_id.id)])
            zcfzb_ids = self.env['finance.stock.zcfzb'].search([('stock_id', '=', stock_id.id)])
            all_fiscal_ids = self.env['finance.fiscal.data'].search([
                ('stock_id', '=', stock_id.id)
            ])
            xjllb_ids = self.env['finance.stock.xjllb'].search([('stock_id', '=', stock_id.id)])

            for period_date in all_period:
                fiscal_id = all_fiscal_ids.filtered(
                    lambda x: x.stock_id == stock_id and x.report_date == self.convert_str_to_datetime(period_date))
                if not fiscal_id:
                    continue

                # 利润表
                lrb_id = lrb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
                # 资产负债表
                zcfzb_id = zcfzb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)
                # 现金流量表
                xjllb_id = xjllb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)

                if not all([zcfzb_id, lrb_id, xjllb_id]):
                    unlink_records += fiscal_id
        unlink_records.unlink()

    def cron_delete_invalidate_records(self):
        all_period = self.get_default_period()
        all_stock_ids = self.env['finance.stock.basic'].search([])
        for stock_id in all_stock_ids:
            self.with_delay()._delete_invalidate_records(all_period, stock_id)

    def cron_update_finance_fiscal_data(self):
        # 更新数据
        all_stock = self.env['finance.stock.basic'].search([])
        for stock_id in all_stock:
            all_fiscal_ids = self.env['finance.fiscal.data'].search([('stock_id', '=', stock_id.id)],
                                                                    order='report_date asc')
            all_fiscal_ids.with_delay().update_fiscal_data()

    def update_fiscal_data(self):
        for line_id in self:
            update_data = self.parse_fiscal_data(line_id.stock_id, str(line_id.report_date))
            # 更新环比、增速等数据
            mm_value = self.parse_mm_ratio_value(line_id)
            speed_value = self.parse_speed_value(line_id)
            update_data.update(**mm_value)
            update_data.update(**speed_value)
            _logger.info('开始更新: {}, {}'.format(line_id.security_code, line_id.report_date))
            line_id.write(update_data)

    def cron_fetch_fiscal_data(self):
        all_period = self.get_default_period()
        all_stock_ids = self.env['finance.stock.basic'].search([])
        for stock_id in all_stock_ids:
            self.with_delay().generate_fiscal_data(stock_ids=stock_id, report_date=all_period)

    def get_operate_cash_flow(self, xjllb_id):
        xjllb_json = xjllb_id.xjllb_json
        if not xjllb_json:
            return 0.0
        xjllb_json = json.loads(xjllb_json)
        return float_or_zero(xjllb_json.get('TOTAL_OPERATE_INFLOW')) - float_or_zero(
            xjllb_json.get('TOTAL_OPERATE_OUTFLOW'))

    def get_lrb_value(self, lrb_id, field_name):
        lrb_json = lrb_id.lrb_json
        if not lrb_json:
            return 0.0
        lrb_json = json.loads(lrb_json)
        return float_or_zero(lrb_json.get(field_name))

    def get_zcfzb_value(self, zcfzb_id, field_name):
        # INTANGIBLE_ASSET
        zcfbb_json = zcfzb_id.zcfbb_json
        if not zcfbb_json:
            return 0.0
        lrb_json = json.loads(zcfbb_json)
        return float_or_zero(lrb_json.get(field_name))

    def get_pb_mrq(self):
        pass

    def parse_fiscal_data(self, stock_id, period_date):
        survey_ids = self.env['finance.stock.company'].search([('ts_code', '=', stock_id.ts_code)])
        main_ids = self.env['finance.stock.main.data'].search([('stock_id', '=', stock_id.id)])
        business_ids = self.env['finance.stock.business'].search([('stock_id', '=', stock_id.id)])
        lrb_ids = self.env['finance.stock.lrb'].search([('stock_id', '=', stock_id.id)])
        xjllb_ids = self.env['finance.stock.xjllb'].search([('stock_id', '=', stock_id.id)])
        zcfzb_ids = self.env['finance.stock.zcfzb'].search([('stock_id', '=', stock_id.id)])
        report_ids = self.env['finance.stock.report'].search([('stock_id', '=', stock_id.id)])

        survey_id = survey_ids.filtered(lambda x: x.ts_code == stock_id.ts_code)
        xjllb_id = xjllb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)

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
            # 每股收益
            'per_share': self.get_lrb_value(lrb_id, 'DILUTED_EPS'),
            # 营业收入
            'operate_revenue': self.get_lrb_value(lrb_id, 'OPERATE_INCOME'),
            # ROE
            'roe': float_or_zero(main_id.roejq),
            # 经营性现金流
            'operate_cash_flow': self.get_operate_cash_flow(xjllb_id),
            # 净运营资本
            'net_working_capital': '',
            # 应收账款
            'accounts_receivable': self.get_zcfzb_value(zcfzb_id, 'ACCOUNTS_RECE'),
            # 收入质量
            'revenue_quality': self.get_ratio(self.get_zcfzb_value(zcfzb_id, 'ACCOUNTS_RECE'),
                                              self.get_lrb_value(lrb_id, 'OPERATE_INCOME')),
            # 总股本
            'total_share_capital': float_or_zero(stock_id.f84),
            # 市现率
            'pcf_ocf_tim': float_or_zero(stock_id.pcf_ocf_tim),
            # 市净率 = 股票价格/每股净资产(f102)
            'pb_mrq': float_or_zero(stock_id.pb_mrq),
            # 市盈率
            'pe_ratio': '',
            # 市销率
            'trade_ratio': self.get_ratio(stock_id.f277, main_id.totaloperatereve),
            # PEG
            'peg': float_or_zero(stock_id.peg_car),
            # 商誉
            # 'gw_netast_rat': self.get_zcfzb_value(zcfzb_id, 'INTANGIBLE_ASSET'),
            'gw_netast_rat': self.get_zcfzb_value(zcfzb_id, 'GOODWILL'),
            # 商誉/净资产
            'net_asset_ratio': self.get_ratio(self.get_zcfzb_value(zcfzb_id, 'GOODWILL'),
                                              float_or_zero(zcfzb_id.total_equity)),
            # 员工数
            'employee': float_or_zero(survey_id.emp_num),
            # 营业收入/员工数量
            'operate_revenue_per': self.get_ratio(self.get_lrb_value(lrb_id, 'OPERATE_INCOME'), survey_id.emp_num),
            # 库存周转次数
            'inventory_turnover': float_or_zero(main_id.chzzl),
            # 资产负债率
            'asset_liability_ratio': float_or_zero(main_id.zcfzl),
            # 净利率
            'profit_margin': float_or_zero(main_id.xsjll),
            # 毛利率
            'gross_profit_ratio': float_or_zero(main_id.xsmll),
            # 净资产
            'net_asset': float_or_zero(zcfzb_id.total_equity),
        }
        return tmp_data

    def convert_str_to_datetime(self, datetime_str):
        date = datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        return date

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
            all_fiscal_ids = self.env['finance.fiscal.data'].search([
                ('stock_id', '=', stock_id.id)
            ])
            xjllb_ids = self.env['finance.stock.xjllb'].search([('stock_id', '=', stock_id.id)])

            for period_date in all_period:
                fiscal_id = all_fiscal_ids.filtered(
                    lambda x: x.stock_id == stock_id and x.report_date == self.convert_str_to_datetime(period_date))
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
                xjllb_id = xjllb_ids.filtered(lambda x: x.stock_id == stock_id and x.report_date == period_date)

                if not all([zcfzb_id, lrb_id, xjllb_id]):
                    continue
                tmp_data = {
                    'secucode': stock_id.ts_code,
                    'security_code': stock_id.symbol,
                    'report_date': period_date,
                    'period_type': 'quarter',
                    'stock_id': stock_id.id,
                    # 每股收益
                    'per_share': self.get_lrb_value(lrb_id, 'DILUTED_EPS'),
                    # 每股收益环比
                    # 'per_share_mm_ratio': '',
                    # 每股收益增速
                    # 'per_share_speed': '',
                    # 营业收入
                    'operate_revenue': self.get_lrb_value(lrb_id, 'OPERATE_INCOME'),
                    # 营业收入环比
                    # 'operate_revenue_mm_ratio': '',
                    # 营业收入增速
                    # 'operate_revenue_speed': '',
                    # ROE
                    'roe': float_or_zero(main_id.roejq),
                    # ROE环比
                    # 'roe_mm_ratio': '',
                    # ROE增速
                    # 'roe_speed': '',
                    # 经营性现金流
                    'operate_cash_flow': self.get_operate_cash_flow(xjllb_id),
                    # 净运营资本
                    'net_working_capital': '',
                    # 应收账款
                    'accounts_receivable': self.get_zcfzb_value(zcfzb_id, 'ACCOUNTS_RECE'),
                    # 应收账款环比
                    # 'accounts_receivable_mm_ratio': '',
                    # 应收账款增速
                    # 'accounts_receivable_speed': '',
                    # 收入质量
                    'revenue_quality': self.get_ratio(self.get_zcfzb_value(zcfzb_id, 'ACCOUNTS_RECE'),
                                                      self.get_lrb_value(lrb_id, 'OPERATE_INCOME')),
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
                    'gw_netast_rat': self.get_zcfzb_value(zcfzb_id, 'GOODWILL'),
                    # 商誉/净资产
                    'net_asset_ratio': self.get_ratio(self.get_zcfzb_value(zcfzb_id, 'GOODWILL'),
                                                      float_or_zero(zcfzb_id.total_equity)),
                    # 员工数
                    'employee': float_or_zero(survey_id.emp_num),
                    # 营业收入/员工数量
                    'operate_revenue_per': self.get_ratio(self.get_lrb_value(lrb_id, 'OPERATE_INCOME'),
                                                          survey_id.emp_num),
                    # 库存周转次数
                    'inventory_turnover': float_or_zero(main_id.chzzl),
                    # 资产负债率
                    'asset_liability_ratio': float_or_zero(main_id.zcfzl),
                    # 净利率
                    'profit_margin': float_or_zero(main_id.xsjll),
                    # 毛利率
                    'gross_profit_ratio': float_or_zero(main_id.xsmll),
                    # 净资产
                    'net_asset': float_or_zero(zcfzb_id.total_equity),
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

    def cron_update_fiscal_data(self):
        all_fiscal_ids = self.env['finance.fiscal.data'].search([])
        for fiscal_id in all_fiscal_ids:
            fiscal_id.with_delay().update_mm_ratio_value()

    def parse_mm_ratio_value(self, fiscal_id):
        stock_fiscal_ids = self.env['finance.fiscal.data'].search([
            ('stock_id', '=', fiscal_id.stock_id.id)
        ], order='report_date asc')
        current_date = fiscal_id.report_date
        # 去年的期间
        mm_date = current_date.replace(current_date.year - 1)

        mm_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == mm_date)
        if not mm_fiscal_id:
            return {}

        result = {
            'operate_revenue_mm_ratio': self.get_ratio(fiscal_id.operate_revenue - mm_fiscal_id.operate_revenue,
                                                       mm_fiscal_id.operate_revenue),
            'per_share_mm_ratio': self.get_ratio(fiscal_id.per_share - mm_fiscal_id.per_share, mm_fiscal_id.per_share),
            'roe_mm_ratio': self.get_ratio(fiscal_id.roe - mm_fiscal_id.roe, mm_fiscal_id.roe),
            'accounts_receivable_mm_ratio': self.get_ratio(
                fiscal_id.accounts_receivable - mm_fiscal_id.accounts_receivable,
                mm_fiscal_id.accounts_receivable)
        }
        return result

    def update_mm_ratio_value(self):
        for fiscal_id in self:
            data = self.parse_mm_ratio_value(fiscal_id)
            if data:
                fiscal_id.write(data)
        self.update_value_speed()

    def parse_speed_value(self, fiscal_id):
        stock_fiscal_ids = self.env['finance.fiscal.data'].search([
            ('stock_id', '=', fiscal_id.stock_id.id)
        ])
        current_date = fiscal_id.report_date

        last_q_month = current_date.month - 3
        if last_q_month == 0:
            last_month_day = calendar.monthrange(current_date.year, 12)
            last_q_date = datetime.datetime(current_date.year - 1, 12, last_month_day[1], current_date.hour,
                                            current_date.minute, current_date.second, current_date.microsecond)
        elif last_q_month > 0:
            last_month_day = calendar.monthrange(current_date.year, current_date.month - 3)
            last_q_date = datetime.datetime(current_date.year, current_date.month - 3, last_month_day[1],
                                            current_date.hour, current_date.minute, current_date.second,
                                            current_date.microsecond)
        else:
            last_q_date = None
        if not last_q_date:
            return {}
        # 去年的期间
        last_year_date = current_date.replace(current_date.year - 1)
        ll_year_q_data = last_q_date.replace(current_date.year - 1)

        last_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == last_year_date)
        ll_q_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == ll_year_q_data)
        last_q_fiscal_id = stock_fiscal_ids.filtered(lambda x: x.report_date == last_q_date)

        result = {
            'operate_revenue_speed': self.compute_value_speed(
                fiscal_id.operate_revenue, last_fiscal_id.operate_revenue,
                last_q_fiscal_id.operate_revenue, ll_q_fiscal_id.operate_revenue
            ),
            'per_share_speed': self.compute_value_speed(
                fiscal_id.per_share, last_fiscal_id.per_share,
                last_q_fiscal_id.per_share, ll_q_fiscal_id.per_share
            ),
            'roe_speed': self.compute_value_speed(
                fiscal_id.roe, last_fiscal_id.roe,
                last_q_fiscal_id.roe, ll_q_fiscal_id.roe
            ),
            'accounts_receivable_speed': self.compute_value_speed(
                fiscal_id.accounts_receivable, last_fiscal_id.accounts_receivable,
                last_q_fiscal_id.accounts_receivable, ll_q_fiscal_id.accounts_receivable
            ),
        }
        return result

    def compute_value_speed(self, val1, val2, val3, val4):
        val5 = self.get_ratio(val1 - val2, val2)
        val6 = self.get_ratio(val3 - val4, val4)
        return self.get_ratio(val5 - val6, val6)

    def update_value_speed(self):
        for fiscal_id in self:
            data = self.parse_speed_value(fiscal_id)
            if data:
                fiscal_id.write(data)
