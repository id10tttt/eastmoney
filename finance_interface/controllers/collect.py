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
import json

_logger = logging.getLogger(__name__)


class MyCollect(http.Controller, BaseController):

    @http.route('/api/wechat/mini/my/collect/list', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def query_my_collect_list(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        collect_ids = request.env['wxa.stock.collect'].sudo().search([
            ('wxa_id', '=', request.wxa_uid)
        ])
        if not collect_ids:
            return self.response_json_error(204, '暂时没有收藏数据!')

        data = [{
            'stock_code': collect_id.name,
            'stock_name': collect_id.stock_id.name
        } for collect_id in collect_ids]
        return self.response_json_success(data)

    @http.route('/api/wechat/mini/my/collect/add', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def add_to_my_collect(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)], limit=1)

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        collect_id = request.env['wxa.stock.collect'].sudo().search([
            ('wxa_id', '=', request.wxa_uid),
            ('stock_id', '=', stock_id.id)
        ])
        if not collect_id:
            try:
                collect_id = request.env['wxa.stock.collect'].sudo().create({
                    'name': stock_code,
                    'stock_id': stock_id.id,
                    'wxa_id': request.wxa_uid
                })
                return self.response_json_success({
                    'msg': '添加成功'
                })
            except Exception as e:
                _logger.error('添加我的收藏发生错误! {}'.format(e))
                return self.response_json_error(-1, '添加失败!')
        else:
            return self.response_json_error(-1, '已经在我的收藏内，无需重复添加!')

    @http.route('/api/wechat/mini/my/collect/unlink', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def unlink_my_collect(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        collect_id = request.env['wxa.stock.collect'].sudo().search([
            ('wxa_id', '=', request.wxa_uid),
            ('stock_id', '=', stock_id.id)
        ])
        if not collect_id:
            return self.response_json_success({
                'msg': '无须删除'
            })
        try:
            collect_id.unlink()
            return self.response_json_success({
                'msg': '无须删除'
            })
        except Exception as e:
            _logger.error('删除我的收藏出错! {}'.format(e))
            return self.response_json_error(-1, '删除失败!')

    @http.route('/api/wechat/mini/my/collect/check', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def check_is_my_collect(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        collect_id = request.env['wxa.stock.collect'].sudo().search([
            ('wxa_id', '=', request.wxa_uid),
            ('stock_id', '=', stock_id.id)
        ])
        if collect_id:
            return self.response_json_success({
                'msg': '我的收藏'
            })
        else:
            return self.response_json_error(204, '未添加到我的收藏')
