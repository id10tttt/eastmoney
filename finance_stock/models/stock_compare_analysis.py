# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class StockCompareAnalysis(models.Model):
    _name = 'stock.compare.analysis'
    _description = '数据比较分析、定义雷'

    name = fields.Char('名称', required=True)
    left_model_id = fields.Many2one('ir.model', string='表', required=True, ondelete='cascade')
    left_field_name = fields.Many2one('ir.model.fields', string='字段', required=True, ondelete='cascade')
    left_filter_field = fields.Many2one('ir.model.fields', string='筛选字段A', required=True, ondelete='cascade')
    left_domain = fields.Char('筛选条件A', required=True)

    right_model_id = fields.Many2one('ir.model', string='比较表', required=True, ondelete='cascade')
    right_field_name = fields.Many2one('ir.model.fields', string='比较字段', required=True, ondelete='cascade')
    right_filter_field = fields.Many2one('ir.model.fields', string='筛选字段B', required=True, ondelete='cascade')
    right_domain = fields.Char('筛选条件B', required=True)

    usage = fields.Selection([
        ('free', '免费使用'),
        ('vip', 'VIP专属')
    ], string='使用范围', default='free', required=True)

    def get_mine_value(self, security_code='000001'):
        left_record = self.env[self.left_model_id.model].search([
            (self.left_filter_field.name, '=', self.left_domain),
            ('security_code', '=', security_code)
        ])
        right_record = self.env[self.right_model_id.model].search([
            (self.right_filter_field.name, '=', self.right_domain),
            ('security_code', '=', security_code)
        ])
        notif_message = ''
        left_value = ''
        right_value = ''
        if hasattr(left_record, self.left_field_name.name):
            notif_message += '{}: {}, {}; \n'.format(self.left_field_name.field_description, self.left_domain,
                                                     getattr(left_record, self.left_field_name.name))
            left_value = getattr(left_record, self.left_field_name.name)
        if hasattr(right_record, self.right_field_name.name):
            notif_message += '{}: {}, {}; \n'.format(self.right_field_name.field_description, self.right_domain,
                                                     getattr(right_record, self.right_field_name.name))
            right_value = getattr(right_record, self.right_field_name.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': '{} 指标: {}'.format(security_code, self.name),
                'message': notif_message,
                'next': {
                    'type': 'ir.actions.act_window_close'
                },
            }
        }
