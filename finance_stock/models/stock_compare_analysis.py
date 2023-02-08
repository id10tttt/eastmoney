# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import uuid


class StockCompareAnalysis(models.Model):
    _name = 'stock.compare.analysis'
    _description = '数据比较分析、定义雷'
    _sql_constraints = [
        ("name_uuid", "unique(uuid)", "uuid must be unique")
    ]

    name = fields.Char('名称', required=True)
    uuid = fields.Char(string="UUID", default=lambda self: self.get_default_uuid(), index=True, required=True)
    value_type = fields.Selection([
        ('value', u'取值'),
        ('vs', u'比较'),
        ('other', u'其它')
    ], string='取值类别', default='vs')
    value_model_id = fields.Many2one('ir.model', string='取值表', ondelete='cascade')
    value_field_name = fields.Many2one('ir.model.fields', string='取值字段', ondelete='cascade')

    left_model_id = fields.Many2one('ir.model', string='表', required=False, ondelete='cascade')
    left_field_name = fields.Many2one('ir.model.fields', string='字段', required=False, ondelete='cascade')
    left_filter_field = fields.Many2one('ir.model.fields', string='筛选字段A', required=False, ondelete='cascade')
    left_domain = fields.Char('筛选条件A', required=False)

    right_model_id = fields.Many2one('ir.model', string='比较表', required=False, ondelete='cascade')
    right_field_name = fields.Many2one('ir.model.fields', string='比较字段', required=False, ondelete='cascade')
    right_filter_field = fields.Many2one('ir.model.fields', string='筛选字段B', required=False, ondelete='cascade')
    right_domain = fields.Char('筛选条件B', required=False)

    type_id = fields.Many2one('finance.mine.type', string='类别')
    usage = fields.Selection([
        ('free', '免费使用'),
        ('vip', 'VIP专属')
    ], string='使用范围', default='free', required=True)

    def get_default_uuid(self):
        return str(uuid.uuid4())

    def get_mine_list(self, vip_mode=False):
        if vip_mode:
            filter_domain = []
        else:
            filter_domain = [('usage', '=', 'free')]
        return self.env['stock.compare.analysis'].search_read(domain=filter_domain, fields=['name', 'uuid'])

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

    def _query_mine_data_vs(self, security_code='000001'):
        return self._query_mine_data_vs_value(security_code=security_code)

    def _query_mine_data_value(self, security_code='000001'):
        record_id = self.env[self.left_model_id.model].search([
            (self.left_filter_field.name, '=', self.left_domain),
            ('security_code', '=', security_code)
        ])
        value = getattr(record_id, self.value_field_name.name)
        return {
            'security_code': security_code,
            'name': self.name,
            'value': value,
            'uuid': self.uuid,
            'msg': 'success'
        }

    def _query_mine_data_other(self, security_code='000001'):
        return {
            'security_code': security_code,
            'name': '',
            'left_value': '',
            'right_value': '',
            'left_field_name': '',
            'right_field_name': '',
            'uuid': '',
            'msg': '没有找到这个指标/权限错误!!'
        }

    def _query_mine_data_vs_value(self, security_code='000001'):
        self.ensure_one()
        left_record = self.env[self.left_model_id.model].search([
            (self.left_filter_field.name, '=', self.left_domain),
            ('security_code', '=', security_code)
        ])
        right_record = self.env[self.right_model_id.model].search([
            (self.right_filter_field.name, '=', self.right_domain),
            ('security_code', '=', security_code)
        ])
        left_value = ''
        right_value = ''
        if hasattr(left_record, self.left_field_name.name):
            left_value = getattr(left_record, self.left_field_name.name)
        if hasattr(right_record, self.right_field_name.name):
            right_value = getattr(right_record, self.right_field_name.name)
        return {
            'security_code': security_code,
            'name': self.name,
            'left_value': left_value,
            'right_value': right_value,
            'left_field_name': self.left_field_name.name,
            'right_field_name': self.right_field_name.name,
            'uuid': self.uuid,
            'msg': 'success'
        }

    def return_error_msg(self, security_code, mine_uuid):
        return {
            'security_code': security_code,
            'name': '',
            'left_value': '',
            'right_value': '',
            'left_field_name': '',
            'right_field_name': '',
            'uuid': mine_uuid,
            'msg': '没有找到这个指标/权限错误!!'
        }

    def query_mine_sweep_data(self, wechat_user, mine_uuid, security_code):
        if_allow = self.env['wx.subscribe.order'].if_allow_view_mine_sweep(wechat_user, mine_uuid)
        if not if_allow:
            return self.return_error_msg(security_code, mine_uuid)
        record_id = self.env['stock.compare.analysis'].search([
            ('uuid', '=', mine_uuid)
        ])
        if not record_id or len(record_id) > 1:
            return self.return_error_msg(security_code, mine_uuid)
        try:
            return getattr(record_id, '_query_mine_data_{}'.format(record_id))(security_code=security_code)
        except Exception as e:
            return self.return_error_msg(security_code, mine_uuid)
