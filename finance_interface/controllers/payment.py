# -*- coding: utf-8 -*-
import requests
import time
import json
from wechatpy import WeChatClient
import xmltodict
from odoo.tools import config
from odoo import http, exceptions, fields
from odoo.http import request
from .wxa_common import verify_auth_token
from wechatpy.pay import WeChatPay
from datetime import timedelta
from .. import utils
from .base import BaseController
import logging
import datetime
import random

_logger = logging.getLogger(__name__)

# WXA_SUB_APP_ID = 'wx37cb18884ba26d78'
# WXA_PAY_SECRET = 'Id10ttttId10ttttId10ttttId10tttt'
# MCH_ID = '1642567832'

APP_MINI_ID = config.get('wxa_app_id')
WXA_SUB_APP_ID = config.get('wxa_sub_id')
APP_MINI_SECRET = config.get('wxa_app_secret')

MCH_ID = config.get('wxa_mch_id')
WXA_PAY_SECRET = config.get('wxa_pay_secret')


def get_random_char():
    random_list = random.sample('ABCDEFGHIJLMNOPQRSTUVWXYZ1234567890', 6)
    return ''.join(str(x) for x in random_list)


def get_datetime_format():
    req_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return req_time


def get_finance_mine_number():
    order_name = 'SUB/MINE/{}{}'.format(get_random_char(), str(get_datetime_format()))
    return order_name


def wechat_mini_payment(appid, mchid, out_trade_no, openid, base_url):
    req_url = 'https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi'
    payload_data = {
        "mchid": mchid,
        "out_trade_no": out_trade_no,
        "appid": appid,
        "description": "扫雷订阅",
        "notify_url": "{}/api/wechat/mini/pay/notify".format(base_url),
        "amount": {
            "total": 1,
            "currency": "CNY"
        },
        "payer": {
            "openid": openid
        }
    }
    res = requests.post(req_url, data=payload_data)


class WxPayment(http.Controller, BaseController):

    @http.route('/api/wechat/mini/pay/subscribe', auth='public', methods=['POST'], csrf=False, cors="*", type='json')
    @verify_auth_token()
    def get_pay_data(self):
        """
        发起支付
        """
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        try:

            user_code = headers.get('code')
            args_key_set = {'subscribe_uuid', 'price'}
            missing_args_key = args_key_set - set(body.keys())
            if missing_args_key:
                return self.res_err(600)

            subscribe_id = request.env['wxa.subscribe'].sudo().search([
                ('uuid', '=', body.get('subscribe_uuid'))
            ])
            if not subscribe_id:
                return self.res_err(700)

            pay_money = subscribe_id.price_total
            old_payment_count = request.env(user=1)['wxa.payment'].search_count([
                ('wechat_user_id', '=', request.wxa_uid),
                ('subscribe_id', '=', subscribe_id.id)
            ])
            out_trade_no = get_finance_mine_number()
            if old_payment_count > 0:
                out_trade_no = '%s-%s' % (out_trade_no, old_payment_count)
            payment = request.env(user=1)['wxa.payment'].create({
                'payment_number': out_trade_no,
                'subscribe_id': subscribe_id.id,
                'wechat_user_id': request.wxa_uid,
                'price': float(pay_money)
            })
            wechat_client = WeChatClient(APP_MINI_ID, APP_MINI_SECRET)
            session_data = wechat_client.wxa.code_to_session(user_code)

            mall_name = '扫雷: {}'.format(out_trade_no)

            base_url = 'https://www.pickbest.cn/api/wechat/mini/pay/notify'

            wxa_pay_client = WeChatPay(WXA_SUB_APP_ID, api_key=WXA_PAY_SECRET, sub_appid=WXA_SUB_APP_ID, mch_id=MCH_ID)
            wxa_order_data = wxa_pay_client.order.create(
                out_trade_no=out_trade_no,
                trade_type='JSAPI', body=mall_name, total_fee=1,
                notify_url=base_url, user_id=session_data.get('openid'),
            )
            jsapi_params = wxa_pay_client.jsapi.get_jsapi_params(prepay_id=wxa_order_data.get('prepay_id'))

            return self.response_json_success(jsapi_params)
        except Exception as e:
            _logger.error('error: {}'.format(e))
            return self.response_json_error(-1, str(e))

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

    @http.route('/api/wechat/mini/pay/notify', auth='public', methods=['POST', 'GET'], csrf=False,
                type='http')
    def notify(self):
        """
        微信支付回调
        """
        try:
            xml_data = request.httprequest.stream.read()
            _logger.info('支付回调： {}'.format(xml_data))
            data = xmltodict.parse(xml_data)['xml']
            if data['return_code'] == 'SUCCESS':
                data.update({'status': utils.PaymentStatus.success})
                payment_id = request.env['wxa.payment'].sudo().search([('payment_number', '=', data['out_trade_no'])],
                                                                      limit=1)

                current_date = fields.Date.today()
                duration_time = payment_id.subscribe_id.duration_time or 30
                payment_id.write({
                    'openid': data['openid'],
                    'bank_type': data['bank_type'],
                    'fee_type': data['fee_type'],
                    'result_code': data['result_code'],
                    'return_code': data['return_code'],
                    'total_fee': data['total_fee'],
                    'transaction_id': data['transaction_id'],
                    'notify_json': json.dumps(data),
                    'notify_xml': '{}'.format(xml_data),
                })
                order_id = request.env['wxa.subscribe.order'].sudo().create({
                    'name': payment_id.payment_number,
                    'wechat_user_id': payment_id.wechat_user_id.id,
                    'subscribe_id': payment_id.subscribe_id.id,
                    'price_total': payment_id.price,
                    'payment_id': payment_id.id,
                    'start_date': current_date,
                    'end_date': current_date + timedelta(days=duration_time)
                })
                _logger.info('生成订单: {}'.format(order_id))
            else:
                data.update({'status': utils.PaymentStatus.fail})
                payment = request.env['wxa.payment'].sudo().search([('payment_number', '=', data['out_trade_no'])])
                payment.write(data)
            return self._res_xml('SUCCESS', 'SUCCESS')
        except Exception as e:
            _logger.error('error: {}'.format(e))
            return self._res_xml('FAIL', '服务器内部错误')
