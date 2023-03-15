# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceCompanyEvent(models.Model):
    _name = 'finance.company.event'
    _description = '公司事件'

    stock_id = fields.Many2one('finance.stock.basic', index=True)
    security_code = fields.Char(related='stock_id.symbol', store=True)
    name = fields.Char('事件')
    event_date = fields.Date('事件日期')
    event_type = fields.Char('类型')
    specific_event_type = fields.Char('Specific Event Type')
    event_content_other = fields.Char('Other Content')
