# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceStockLRB(models.Model):
    _name = 'finance.stock.lrb'
    _description = '利润表'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码唯一')
    ]
    _rec_name = 'secucode'

    lrb_json = fields.Char('LRB JSON')
    stock_id = fields.Many2one('finance.stock.basic', string='股票代码')
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    security_name_abbr = fields.Char('SECURITY_NAME_ABBR')
    org_code = fields.Char('ORG_CODE')
    org_type = fields.Char('ORG_TYPE')
    report_date = fields.Char('REPORT_DATE', index=True)
    report_type = fields.Char('REPORT_TYPE')
    continued_netprofit = fields.Char('CONTINUED_NETPROFIT')
    interest_expense = fields.Char('INTEREST_EXPENSE')
