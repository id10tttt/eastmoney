# -*- coding: utf-8 -*-
import json
from odoo import http, exceptions, fields
from odoo.http import request
from .base import BaseController
import logging
from .wxa_common import verify_auth_token
# from Crypto.Cipher import AES
# from Crypto.Util.Padding import pad
# from base64 import b64encode
# import binascii

_logger = logging.getLogger(__name__)

AES_ENCRYPT_KEY = 'Hcl97tpCW3mc2Wd3'


# def aes_encrypt_msg(msg):
#     cipher = AES.new(AES_ENCRYPT_KEY.encode(), AES.MODE_CBC)
#     ct_bytes = cipher.encrypt(pad(msg.encode(), 16))
#     iv = b64encode(cipher.iv).decode('utf-8')
#     encrypt_msg = binascii.hexlify(ct_bytes)
#     # encrypt_msg = b64encode(ct_bytes)
#     return {
#         'iv': iv,
#         'data': msg
#         # 'data': encrypt_msg
#     }


class VIPContent(http.Controller, BaseController):

    @http.route('/api/wechat/mini/vip/content', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def query_vip_content(self, **kwargs):
        """
        获取订阅链接
        """
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(-1, '股票不存在!')
        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip:
            return self.response_json_error(-1, '没有权限查看')

        compare_type_data = request.env['stock.compare.analysis'].sudo().read_group(
            domain=[], fields=['type_id'],
            groupby=['type_id'])
        compare_ids = request.env['stock.compare.analysis'].sudo().search([], order='type_id')
        type_ids = sorted(list(set(compare_ids.mapped('type_id'))))
        if False not in type_ids:
            type_ids.append(False)

        vip_content = []
        for type_id in type_ids:
            tmp_data = []

            if type_id:
                compare_type_ids = compare_ids.filtered(lambda x: x.type_id == type_id)
            else:
                compare_type_ids = compare_ids.filtered(lambda x: not x.type_id)
            for compare_id in compare_type_ids:
                tmp_data.append({
                    'name': compare_id.name,
                    'value': 1,
                    'uuid': compare_id.uuid
                })
            if tmp_data:
                vip_content.append({
                    'type': type_id.name if type_id else '其它',
                    'type_id': type_id.id if type_id else -1,
                    'data': tmp_data
                })
        # vip_content_json = json.dumps(vip_content)
        # encrypt_data = aes_encrypt_msg(vip_content_json)
        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'default_content': type_ids[0].id if type_ids else -1,
            'data': vip_content
        }
        # data.update(**encrypt_data)
        return self.response_json_success(data)

    @http.route('/api/wechat/mini/vip/content/sync', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def sync_vip_content(self, **kwargs):
        """
        获取订阅链接
        """
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')
        type_id = body.get('type_id')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(-1, '股票不存在!')
        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip:
            return self.response_json_error(-1, '没有权限查看')

        compare_type_data = request.env['stock.compare.analysis'].sudo().read_group(
            domain=[], fields=['type_id'],
            groupby=['type_id'])
        compare_ids = request.env['stock.compare.analysis'].sudo().search([])
        type_ids = sorted(list(set(compare_ids.mapped('type_id'))))
        if False not in type_ids:
            type_ids.append(False)

        vip_content = []
        for type_id in type_ids:
            tmp_data = []

            if type_id:
                compare_type_ids = compare_ids.filtered(lambda x: x.type_id == type_id)
            else:
                compare_type_ids = compare_ids.filtered(lambda x: not x.type_id)
            for compare_id in compare_type_ids:
                tmp_data.append({
                    'name': compare_id.name,
                    'value': 1,
                    'uuid': compare_id.uuid
                })
            vip_content.append({
                'type': type_id.name if type_id else '其它',
                'type_id': type_id.id if type_id else -1,
                'data': tmp_data
            })
        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'default_content': type_ids[0].id if type_ids else -1,
            'data': vip_content
        }
        return self.response_json_success(data)
