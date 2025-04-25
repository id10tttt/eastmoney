# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceStockBusiness(models.Model):
    _name = 'finance.stock.business'
    _description = '主营构成分析'
    _sql_constraints = [
        ('unique_secucode_report_date_item_name_mainop_type', 'unique(secucode, report_date, item_name, mainop_type)',
         '股票代码、时间、名称、mainop_type唯一')
    ]
    _rec_name = 'display_name'
    _order = 'secucode, report_date desc'

    display_name = fields.Char(compute='_compute_display_name')
    stock_id = fields.Many2one('finance.stock.basic', index=True)
    gross_profit_ratio = fields.Char('毛利率(%)')
    item_name = fields.Char('主营构成')
    mainop_type = fields.Char('MAINOP_TYPE')
    main_business_cost = fields.Char('主营成本(元)')
    main_business_income = fields.Char('主营收入(元)')
    main_business_profit = fields.Char('主营利润(元)')
    mbc_ratio = fields.Char('成本比例')
    mbi_ratio = fields.Char('收入比例')
    mbr_ratio = fields.Char('利润比例')
    rank = fields.Char('RANK')
    report_date = fields.Char('REPORT_DATE', index=True)
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE', index=True)
    business_json = fields.Char('BUSINESS JSON')

    def _compute_display_name(self):
        for line_id in self:
            line_id.display_name = '{}/{}/{}'.format(line_id.secucode, line_id.report_date, line_id.item_name)
