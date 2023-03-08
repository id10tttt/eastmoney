# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceStockReport(models.Model):
    _name = 'finance.stock.report'
    _description = '业绩报表明细(https://data.eastmoney.com/bbsj/000001.html)'
    _sql_constraints = [
        ('unique_secucode_reportdate', 'unique(secucode, reportdate)', '股票代码唯一')
    ]
    _rec_name = 'secucode'
    _order = 'secucode, reportdate desc'

    stock_id = fields.Many2one('finance.stock.basic')

    basic_eps = fields.Char(u'每股收益率')
    bps = fields.Char('每股净资产(元)')
    data_type = fields.Char('DATATYPE')
    data_year = fields.Char('DATAYEAR')
    date_mmdd = fields.Char('DATEMMDD')
    deduct_basic_eps = fields.Char('DEDUCT_BASIC_EPS')
    eitime = fields.Char('EITIME')
    isnew = fields.Char('ISNEW')
    mgjyxjje = fields.Char('每股经营现金流量(元)')
    notice_date = fields.Char('NOTICE_DATE')
    org_code = fields.Char('ORG_CODE')
    parent_netprofit = fields.Char(u'净利润')
    publishname = fields.Char('PUBLISHNAME')
    qdate = fields.Char('QDATE')
    reportdate = fields.Char('REPORTDATE', index=True)
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    security_name_abbr = fields.Char('SECURITY_NAME_ABBR')
    security_type = fields.Char('SECURITY_TYPE')
    security_type_code = fields.Char('SECURITY_TYPE_CODE')
    sjlhz = fields.Char('净利润-季度环比增长(%)')
    sjltz = fields.Char('净利润-同比增长(%)')
    total_operate_income = fields.Char('营业总收入(元)')
    trade_market = fields.Char('TRADE_MARKET')
    trade_market_code = fields.Char('TRADE_MARKET_CODE')
    trade_market_zjg = fields.Char('TRADE_MARKET_ZJG')
    weightavg_roe = fields.Char('净资产收益率(%)')
    yshz = fields.Char('营业总收入-季度环比增长(%)')
    ystz = fields.Char('营业总收入-同比增长(%)')

    report_json = fields.Char('JSON')
