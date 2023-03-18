# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json


class BenchmarkData(models.Model):
    _name = 'compare.benchmark.data'
    _description = '储存结果'
    _sql_constraints = [
        ("unique_compare_stock", "unique(compare_id, stock_code)", "stock compare must unique")
    ]

    compare_id = fields.Many2one('stock.compare.analysis', string='Compare')
    stock_code = fields.Char('Stock', index=True)
    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    value = fields.Text('Value')
    sign = fields.Selection([
        ('sun', '阳'),
        ('rain', '阴'),
        ('danger', '雷')
    ], string='Sign', compute='_compute_benchmark_sign', store=True)

    def analyse_benchmark_result(self, benchmark_data):
        for benchmark_line_id in benchmark_data:
            if all(benchmark_line_id.get('data')):
                return benchmark_line_id.get('sign')
            if benchmark_line_id.get('sign') == 'danger' and any(benchmark_line_id.get('data')):
                return benchmark_line_id.get('sign')
        return 'rain'

    @api.depends('value')
    def _compute_benchmark_sign(self):
        for line_id in self:
            benchmark_value = json.loads(line_id.value)
            benchmark_data = benchmark_value.get('benchmark_data')
            benchmark_sign = self.analyse_benchmark_result(benchmark_data)
            line_id.sign = benchmark_sign
