# -*- coding: utf-8 -*-
from odoo import models, fields, api
import uuid


class WxaSubscribe(models.Model):
    _name = 'wxa.subscribe'
    _description = '订阅设置'

    name = fields.Char(u'名称', required=True)
    type = fields.Selection([
        ('normal', u'普通订阅'),
        ('vip', u'高级订阅')
    ], string='订阅类别', default='normal', required=True)
    uuid = fields.Char(string="UUID", default=lambda self: self._default_uuid(), index=True, required=True)
    price_total = fields.Float(u'金额', required=True)
    duration_time = fields.Float(u'生效天数', required=True)
    allow_analysis_ids = fields.Many2many('stock.compare.analysis', string='指标', domain=[('usage', '=', 'vip')])

    def _default_uuid(self):
        return str(uuid.uuid4())

    def get_all_subscribe_data(self):
        subscribe_data = self.env['wxa.subscribe'].sudo().search_read(
            domain=[],
            fields=['name', 'uuid', 'type', 'price_total', 'duration_time'])
        return subscribe_data


class WxaSubscribeOrder(models.Model):
    _name = 'wxa.subscribe.order'
    _description = '订阅订单'

    name = fields.Char('名称', required=True)
    wechat_user_id = fields.Many2one('wxa.user', string='客户')
    subscribe_id = fields.Many2one('wxa.subscribe', string='订阅')
    price_total = fields.Float('支付金额')
    payment_id = fields.Many2one('wxa.payment', string='支付')
    start_date = fields.Date('生效日期')
    end_date = fields.Date('时效日期')

    def wx_user_is_vip(self, user_id):
        """
        是否是VIP用户
        """
        all_ids = self.env['wxa.subscribe.order'].sudo().search([
            ('wechat_user_id', '=', user_id),
            ('payment_id.status', '=', 'success')
        ])
        if not all_ids:
            return False
        # 有效期内，且支付成功
        if all_ids.filtered(
                lambda x: x.start_date < fields.Date.today() < x.end_date and x.payment_id.status == 'success'):
            return True
        return False

    def if_allow_view_mine_sweep(self, user_id, mine_uuid):
        """
        判断用户是不是能访问该指标
        """
        self.ensure_one()
        all_ids = self.env['wxa.subscribe.order'].sudo().search([('wechat_user_id', '=', user_id)])
        if not all_ids:
            return False
        all_uuid = all_ids.mapped('subscribe_id').mapped('allow_analysis_ids').mapped('uuid')
        if mine_uuid in all_uuid:
            return True
        else:
            return False
