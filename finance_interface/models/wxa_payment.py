# -*- coding: utf-8 -*-

from odoo import models, fields, api

from .. import utils


class WxaPayment(models.Model):
    _name = 'wxa.payment'
    _description = u'支付记录'
    _order = 'id desc'
    _rec_name = 'payment_number'

    wechat_user_id = fields.Many2one('wxa.user', string='客户')
    subscribe_id = fields.Many2one('wxa.subscribe', string='订阅')
    subscribe_order_id = fields.Many2one('wxa.subscribe.order', string='订阅订单', required=False)
    payment_number = fields.Char('支付单号', index=True)
    price = fields.Float('支付金额(元)')
    status = fields.Selection([
        ('unpaid', '未支付'),
        ('success', '成功'),
        ('fail', '失败'),
    ], string='状态', default='unpaid')

    payment_state = fields.Boolean(compute='_compute_payment_state', store=True)
    # notify返回参数
    openid = fields.Char('openid')
    result_code = fields.Char('业务结果')
    return_code = fields.Char('返回CODE')
    err_code = fields.Char('错误代码')
    err_code_des = fields.Char('错误代码描述')
    transaction_id = fields.Char('订单号')
    bank_type = fields.Char('付款银行')
    fee_type = fields.Char('货币种类')
    total_fee = fields.Integer('订单金额(分)')
    settlement_total_fee = fields.Integer('应结订单金额(分)')
    cash_fee = fields.Integer('现金支付金额')
    cash_fee_type = fields.Char('货币类型')
    coupon_fee = fields.Integer('代金券金额(分)')
    coupon_count = fields.Integer('代金券使用数量')
    notify_json = fields.Char('回调记录JSON')
    notify_xml = fields.Char('回调记录XML')

    _sql_constraints = [(
        'wxapp_payment_payment_number_unique',
        'UNIQUE (payment_number)',
        'wechat payment payment_number is existed！'
    )]

    @api.depends('transaction_id', 'bank_type')
    def _compute_payment_state(self):
        for line_id in self:
            if line_id.transaction_id and line_id.result_code == 'SUCCESS':
                line_id.payment_state = True
                line_id.status = 'success'
            else:
                line_id.payment_state = False

    def manual_compute_payment_state(self):
        self._compute_payment_state()
