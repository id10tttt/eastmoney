# -*- coding: utf-8 -*-
from odoo import models, fields


class StockZCFZB(models.Model):
    _name = 'finance.stock.zcfzb'
    _description = '资产负债表'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码唯一')
    ]
    _rec_name = 'secucode'

    stock_id = fields.Many2one('finance.stock.basic', string='股票代码')
    zcfbb_json = fields.Char('ZCFZB JSON')

    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')
    security_name_abbr = fields.Char('SECURITY_NAME_ABBR')
    org_code = fields.Char('ORG_CODE')
    org_type = fields.Char('ORG_TYPE')
    report_date = fields.Char('REPORT_DATE', index=True)
    report_type = fields.Char('REPORT_TYPE')
    report_date_name = fields.Char('REPORT_DATE_NAME')
    security_type_code = fields.Char('SECURITY_TYPE_CODE')
    notice_date = fields.Char('NOTICE_DATE')
    update_date = fields.Char('UPDATE_DATE')
    currency = fields.Char('CURRENCY')
    total_assets = fields.Char('资产总计')
    total_current_assets = fields.Char('流动资产合计')
    total_current_liab = fields.Char('流动负债合计')
    total_equity = fields.Char('股东权益合计')
    total_liab_equity = fields.Char('负债和股东权益总计')
    total_liablifties = fields.Char('负债合计')
    total_noncurrent_assets = fields.Char('其他非流动资产')
    total_noncurrent_liab = fields.Char('非流动负债合计')
    total_other_payable = fields.Char('其他应付款合计')
    total_other_rece = fields.Char('其他应收款合计')
    total_parent_equity = fields.Char('归属于母公司股东权益总计')
