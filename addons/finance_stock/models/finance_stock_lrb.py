# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json


class FinanceStockLRB(models.Model):
    _name = 'finance.stock.lrb'
    _description = '利润表'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码唯一')
    ]
    _rec_name = 'secucode'
    _order = 'secucode, report_date desc'

    lrb_json = fields.Char('LRB JSON')
    stock_id = fields.Many2one('finance.stock.basic', string='股票代码', index=True)
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    security_name_abbr = fields.Char('SECURITY_NAME_ABBR')
    org_code = fields.Char('ORG_CODE')
    org_type = fields.Char('ORG_TYPE')
    report_date = fields.Char('REPORT_DATE', index=True)
    report_type = fields.Char('REPORT_TYPE')
    continued_netprofit = fields.Char('CONTINUED_NETPROFIT')
    interest_expense = fields.Char('INTEREST_EXPENSE')
    diluted_eps = fields.Char('DILUTED_EPS', compute='_compute_lrb_value', store=True)
    operate_income = fields.Char('OPERATE_INCOME', compute='_compute_lrb_value', store=True)

    @api.depends('lrb_json')
    def _compute_lrb_value(self):
        for line_id in self:
            try:
                if line_id.lrb_json:
                    lrb_json = json.loads(line_id.lrb_json)
                    line_id.operate_income = lrb_json.get('OPERATE_INCOME')
                    line_id.diluted_eps = lrb_json.get('DILUTED_EPS')
            except Exception as e:
                continue
