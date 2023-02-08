# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class WxConfig(models.Model):
    _name = 'wx.config'
    _description = u'对接设置'
    _rec_name = 'mall_name'

    sub_domain = fields.Char('接口前缀', help='商城访问的接口url前缀', index=True, required=True, default='mine')

    mall_name = fields.Char('名称', help='显示在顶部')

    app_id = fields.Char('AppId')
    secret = fields.Char('Secret')

    team_id = fields.Many2one('crm.team', string='所属销售渠道', required=True)
    gmt_diff = fields.Integer('客户端时区GMT ± N', default=8)

    wechat_pay_id = fields.Char('微信支付商户号')
    wechat_pay_secret = fields.Char('微信支付商户秘钥')
    sub_mch_id = fields.Char('微信支付特约商户号')
    kdniao_app_id = fields.Char('快递鸟APP ID')
    kdniao_app_key = fields.Char('快递鸟APP key')
    msgtpl_order_created = fields.Char('下单成功通知')
    msgtpl_order_paid = fields.Char('订单支付成功通知')
    msgtpl_order_delivery = fields.Char('订单发货通知')
    msgtpl_order_closed = fields.Char('订单已关闭通知')
    msgtpl_order_confirmed = fields.Char('订单已确认待付款通知')
    user_id = fields.Many2one('res.users', string='默认销售员')
    enable_no_service_period = fields.Boolean('启用禁止下单时段', default=False)
    no_service_start_hour = fields.Integer('禁止下单开始时间小时(0-23)')
    no_service_start_minute = fields.Integer('禁止下单开始时间分(0-59)')
    no_service_long = fields.Integer('禁止下单持续时长/分钟')
    auto_cancel_expired_order = fields.Boolean('超时未支付订单自动取消', default=False)
    allow_self_collection = fields.Boolean('允许到店自提', default=False)
    recharge_open = fields.Boolean('是否开启钱包积分', default=False)

    def need_login(self):
        return False

    def get_config(self, key):
        if key == 'mallName':
            key = 'mall_name'
        if hasattr(self, key):
            return self.__getattribute__(key)
        else:
            return None

    @api.model
    def get_entry(self, sub_domain):
        # mine 默认使用平台的配置
        if sub_domain in ['mine']:
            entry = self.env.ref('finance_interface.wx_config_data_finance')
            entry._platform = sub_domain
            return entry
        config = self.search([('sub_domain', '=', sub_domain)])
        if config:
            config.ensure_one()
            config._platform = 'wx|%s' % config.id
            return config
        else:
            return False

    def get_id(self):
        if self._platform in ['mirror']:
            return self.id
        else:
            return int(self._platform.replace('wx|', ''))

    @api.model
    def get_from_team(self, team_id):
        config = self.search([('team_id', '=', team_id)])
        if config:
            config.ensure_one()
            return config
        else:
            return False

    @api.model
    def get_from_id(self, id):
        return self.browse(id)

    def clean_all_token(self):
        self.env['wx.access.token'].search([]).unlink()

    def clean_all_token_window(self):
        new_context = dict(self._context) or {}
        new_context['default_info'] = "确认将所有会话 token 清除？"
        new_context['default_model'] = 'wx.config'
        new_context['default_method'] = 'clean_all_token'
        new_context['record_ids'] = [obj.id for obj in self]
        return {
            'name': u'确认清除',
            'type': 'ir.actions.act_window',
            'res_model': 'wx.confirm',
            'res_id': None,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'view_id': self.env.ref('finance_interface.confirm_view_form').id,
            'target': 'new'
        }

    def get_level(self):
        return 0

    def get_ext_config(self):
        return {}
