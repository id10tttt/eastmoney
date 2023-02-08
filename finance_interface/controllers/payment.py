# -*- coding: utf-8 -*-
import time
import json
import xmltodict
from odoo import http, exceptions, fields
from odoo.http import request
from datetime import timedelta
from .. import utils
from .base import BaseController
from ..rpc.pay import WeixinPay, build_pay_sign
import logging
import datetime
import random

_logger = logging.getLogger(__name__)


def get_random_char():
    random_list = random.sample('ABCDEFGHIJLMNOPQRSTUVWXYZ1234567890', 6)
    return ''.join(str(x) for x in random_list)


def get_datetime_format():
    req_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return req_time


def get_finance_mine_number():
    order_name = 'SUB/MINE/{}{}'.format(get_random_char(), str(get_datetime_format()))
    return order_name


class WxPayment(http.Controller, BaseController):

    @http.route('/finance/<string:sub_domain>/pay/subscribe', auth='public', methods=['GET'], csrf=False,
                type='http')
    def query_subscribe_list(self, **kwargs):
        """
        获取订阅链接
        """
        token = kwargs.pop('token', None)
        subscribe_data = request.env['wx.subscribe'].get_all_subscribe_data()
        return self.res_ok(subscribe_data)

    @http.route('/finance/<string:sub_domain>/pay/subscribe', auth='public', methods=['POST'], csrf=False,
                type='http')
    def get_pay_data(self, sub_domain, **kwargs):
        """
        发起支付
        """
        headers = kwargs.get('header')
        body = kwargs.get('body')
        token = headers.get('token', None)
        try:
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res:
                return res
            else:
                app_id = entry.get_config('app_id')
                wechat_pay_id = entry.get_config('wechat_pay_id')
                wechat_pay_secret = entry.get_config('wechat_pay_secret')
                if not all([app_id, wechat_pay_id, wechat_pay_secret]):
                    return self.res_err(404, '参数配置错误!')

            args_key_set = {'subscribe_uuid', 'price'}
            missing_args_key = args_key_set - set(body.keys())
            if missing_args_key:
                return self.res_err(600)

            subscribe_id = request.env['wx.subscribe'].search([
                ('uuid', '=', body.get('subscribe_uuid'))
            ])
            if not subscribe_id:
                return self.res_err(700)

            pay_money = subscribe_id.price_total
            old_payment_count = request.env(user=1)['wx.payment'].search_count([
                ('wechat_user_id', '=', wechat_user.id),
                ('subscribe_id', '=', subscribe_id.id)
            ])
            out_trade_no = get_finance_mine_number()
            if old_payment_count > 0:
                out_trade_no = '%s-%s' % (out_trade_no, old_payment_count)
            payment = request.env(user=1)['wx.payment'].create({
                'payment_number': out_trade_no,
                'subscribe_id': subscribe_id.id,
                'wechat_user_id': wechat_user.id,
                'price': float(pay_money)
            })
            mall_name = '%s %s' % (entry.get_config('mall_name') or '扫雷', out_trade_no)
            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            wxpay = WeixinPay(appid=app_id, mch_id=wechat_pay_id, partner_key=wechat_pay_secret)
            unified_order = wxpay.unifiedorder(
                body=mall_name,
                total_fee=(int(round(float(pay_money) * 100))),
                notify_url='{base_url}/finance/{sub_domain}/pay/notify'.format(
                    base_url=base_url, sub_domain=sub_domain),
                openid=('{}'.format(wechat_user.open_id)),
                out_trade_no=out_trade_no
            )
            _logger.info('WeixinPay return %s' % unified_order)
            if unified_order['return_code'] == 'SUCCESS':
                time_stamp = unified_order['result_code'] == 'FAIL' or str(int(time.time()))
                response = request.make_response(
                    headers={'Content-Type': 'json'},
                    data=(json.dumps({
                        'code': 0,
                        'data': {
                            'timeStamp': str(int(time.time())),
                            'nonceStr': unified_order['nonce_str'],
                            'prepayId': unified_order['prepay_id'],
                            'sign': build_pay_sign(app_id, unified_order['nonce_str'], unified_order['prepay_id'],
                                                   time_stamp, wechat_pay_secret)},
                        'msg': 'success'
                    })))
            else:
                if unified_order.get('err_code') == 'ORDERPAID':
                    order = payment.order_id
                    order.write({'status': 'pending'})
                    payment.unlink()
                return request.make_response(
                    json.dumps({
                        'code': -1,
                        'msg': unified_order.get('err_code_des', unified_order['return_msg'])
                    }))
            return response
        except Exception as e:
            _logger.error('error: {}'.format(e))
            return self.res_err(-1, str(e))

    def _res_xml(self, code, msg):
        response = request.make_response(
            headers={'Content-Type': 'application/xml'},
            data=(xmltodict.unparse({
                'xml': {
                    'return_code': code,
                    'return_msg': msg
                }
            })))
        return response

    @http.route('/finance/<string:sub_domain>/pay/notify', auth='public', methods=['POST', 'GET'], csrf=False,
                type='http')
    def notify(self, sub_domain, **kwargs):
        """
        微信支付回调
        """
        try:
            entry = request.env['wx.config'].sudo().search([('sub_domain', '=', sub_domain)])
            if not entry:
                return self._res_xml('FAIL', '参数格式校验错误')
            xml_data = request.httprequest.stream.read()
            data = xmltodict.parse(xml_data)['xml']
            if data['return_code'] == 'SUCCESS':
                data.update({'status': utils.PaymentStatus.success})
                payment_id = request.env['wx.payment'].sudo().search([('payment_number', '=', data['out_trade_no'])])

                current_date = fields.Date.today()
                order_id = request.env['wx.subscribe.order'].create({
                    'name': payment_id.payment_number,
                    'wechat_user_id': payment_id.wechat_user_id.id,
                    'subscribe_id': payment_id.subscribe_id.id,
                    'price_total': payment_id.price,
                    'payment_id': payment_id.id,
                    'start_date': current_date,
                    'end_date': current_date + timedelta(days=self.expiration_time)
                })
                _logger.info('生成订单: {}'.format(order_id))
            else:
                data.update({'status': utils.PaymentStatus.fail})
                payment = request.env['wx.payment'].sudo().search([('payment_number', '=', data['out_trade_no'])])
                payment.write(data)
            return self._res_xml('SUCCESS', 'SUCCESS')
        except Exception as e:
            _logger.error('error: {}'.format(e))
            return self._res_xml('FAIL', '服务器内部错误')
