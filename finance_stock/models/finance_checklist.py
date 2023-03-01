# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceEventType(models.Model):
    _name = 'finance.event.type'
    _description = '事件类型'

    name = fields.Char('事件')
    description = fields.Date('说明')


class FinanceCheckList(models.Model):
    _name = 'finance.check.list'
    _description = 'table: checklist检测清单'

    event_id = fields.Many2one('finance.company.event', '事件')
    stock_id = fields.Many2one('finance.stock.basic', index=True)
    name = fields.Char('事项')
    event_data = fields.Char('数据')
    event_type = fields.Many2one('finance.event.type', '事件类型')
    event_date = fields.Date('事件日期')
    updated_date = fields.Date('更新日期')
    sign = fields.Char('签名')
