# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceFiscalData(models.Model):
    _name = 'finance.fiscal.data'
    _description = 'table: fiscal_data处理后的财务信息'

    report_date = fields.Datetime('日期', index=True)
    period_type = fields.Selection([
        ('year', '年'),
        ('quarter', '季度'),
        ('month', '月份'),
        ('other', '其它')
    ], default='quarter', string='日期类型', index=True)

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
