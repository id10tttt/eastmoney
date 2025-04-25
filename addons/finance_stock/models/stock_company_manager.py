# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockCompanyManger(models.Model):
    _name = 'stock.company.manager'
    _description = '数据来源：同花顺'

    security_code = fields.Char('SECURITY CODE', index=True)

    tc = fields.Char('序号')
    tc_url = fields.Char('Url')
    tc_name = fields.Char('姓名')
    tc_title = fields.Char('职务')
    td1 = fields.Char('直接持股数')
    td2 = fields.Char('间接持股数')
    tr_json = fields.Char('Json')
    shr_hold = fields.Boolean(compute='_compute_td', store=True, index=True, string='是否持股')

    @api.depends('td1', 'td2')
    def _compute_td(self):
        for line_id in self:
            try:
                if any([x.isdigit() for x in line_id.td1]) or any([x.isdigit() for x in line_id.td2]):
                    line_id.shr_hold = True
                else:
                    line_id.shr_hold = False
            except Exception as e:
                line_id.shr_hold = False
