# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceStockXJLLB(models.Model):
    _name = 'finance.stock.xjllb'
    _description = '现金流量表'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码唯一')
    ]
    _rec_name = 'secucode'

    xjllb_json = fields.Char('XJLLB JSON')
    stock_id = fields.Many2one('finance.stock.basic', string='股票代码', index=True)
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    report_date = fields.Char('REPORT DATE')
    report_date_name = fields.Char('REPORT DATE TYPE')
    report_type = fields.Char('REPORT TYPE')
    operate_in_flow = fields.Char('IN FLOW')
    operate_out_flow = fields.Char('OUT FLOW')
