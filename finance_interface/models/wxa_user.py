# -*- coding: utf-8 -*-

from odoo import models, fields, api
import uuid
from .. import utils


class WxaAppUser(models.Model):
    _name = 'wxa.user'
    _description = u'小程序: 微信客户'
    _order = 'id desc'

    name = fields.Char(string='名称')
    nickname = fields.Char('昵称')

    open_id = fields.Char('OpenId', required=True, index=True, readonly=True)
    union_id = fields.Char('UnionId', readonly=True)
    gender = fields.Integer('性别')
    language = fields.Char('语言')
    phone = fields.Char('手机号码')
    country = fields.Char('国家')
    province = fields.Char('省份')
    city = fields.Char('城市')
    avatar = fields.Html('头像', compute='_compute_avatar')
    avatar_url = fields.Char('头像链接')
    register_ip = fields.Char('注册IP')
    last_login = fields.Datetime('登陆时间')
    ip = fields.Char('登陆IP')
    status = fields.Selection(utils.WechatUserStatus.attrs.items(), string='状态',
                              default=utils.WechatUserStatus.default)
    register_type = fields.Selection(utils.WechatUserRegisterType.attrs.items(), string='注册来源',
                                     default=utils.WechatUserRegisterType.app)
    user_uuid = fields.Char(compute='_compute_user_uuid', string='UUID', store=True)

    # partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', string='关联联系人')
    # address_ids = fields.One2many('res.partner', compute='_compute_address_ids', string='收货地址')
    entry_id = fields.Integer(u'来源ID')
    balance = fields.Float(u'余额')
    score = fields.Float(u'评分')

    active = fields.Boolean('是否有效', default=True)
    forbidden_user = fields.Boolean('禁用用户', default=False)
    real_name = fields.Char(u'真实姓名')

    _sql_constraints = [
        ('unique_open_id_phone', 'unique(open_id, phone)', '手机和openid 必须唯一'),
    ]

    def change_access_token(self):
        for user_id in self:
            user_id.user_uuid = str(uuid.uuid4())

    @api.depends('open_id')
    def _compute_user_uuid(self):
        for line_id in self:
            line_id.user_uuid = str(uuid.uuid4())

    @api.depends('avatar_url')
    def _compute_avatar(self):
        for each_record in self:
            if each_record.avatar_url:
                each_record.avatar = """
                <img src="{avatar_url}" style="max-width:100px;">
                """.format(avatar_url=each_record.avatar_url)
            else:
                each_record.avatar = False

    def bind_mobile(self, mobile):
        self.partner_id.write({'mobile': mobile})

    def check_account_ok(self):
        return True

    def get_balance(self):
        return hasattr(self, 'balance') and self.balance or 0

    def get_score(self):
        return hasattr(self, 'score') and self.score or 0

    def get_credit_limit(self):
        return 0
