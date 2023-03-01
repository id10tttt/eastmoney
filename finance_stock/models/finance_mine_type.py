# -*- coding: utf-8 -*-
from odoo import models, fields


class FinanceMineType(models.Model):
    _name = 'finance.mine.type'
    _description = '雷区类别'
    _sql_constraints = [
        ('unique_name', 'unique(name)', '名称唯一')
    ]

    name = fields.Char('名称')
    description = fields.Char('说明')
