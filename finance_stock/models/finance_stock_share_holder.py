# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceStockShareHolder(models.Model):
    _name = 'finance.stock.share.holder'
    _description = '流通股东'
    _order = 'report_date, holder_rank'
    _sql_constraints = [
        ("name_report_date", "unique(holder_name, report_date)", "股票、日期必须唯一")
    ]

    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    report_date = fields.Char('日期')
    free_holder_number_ratio = fields.Char('占总流通股本持股比例')
    holder_name = fields.Char('股东名称')
    holder_type = fields.Char('HOLDER_TYPE')
    holder_rank = fields.Integer('HOLDER_RANK')
    hold_num = fields.Char('HOLD NUM')
    hold_num_change = fields.Char('HOLD NUM CHANGE')
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    share_type = fields.Char('SHARES_TYPE')
    share_holder_json = fields.Char('JSON')
