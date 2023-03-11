# -*- coding: utf-8 -*-
from odoo import models, fields


class BenchmarkData(models.Model):
    _name = 'compare.benchmark.data'
    _description = '储存结果'
    _sql_constraints = [
        ("unique_compare_stock", "unique(compare_id, stock_code)", "stock compare must unique")
    ]

    compare_id = fields.Many2one('stock.compare.analysis', string='Compare')
    stock_code = fields.Char('Stock', index=True)
    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    value = fields.Char('Value')
    sign = fields.Selection([
        ('sun', '阳'),
        ('rain', '阴'),
        ('danger', '雷')
    ], string='Sign')
