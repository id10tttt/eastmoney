# -*- coding: utf-8 -*-
from odoo import http, exceptions, fields
from odoo.http import request
from .base import BaseController
import logging

from .wxa_common import verify_auth_token
import json

_logger = logging.getLogger(__name__)

AES_ENCRYPT_KEY = 'Hcl97tpCW3mc2Wd3'
ALLOW_QUERY_TIME = 3


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

    def parse_compare_value(self, compare_data):
        try:
            compare_data = json.loads(compare_data)
            compare_data_list = compare_data.get('data', [])
            if compare_data_list:
                return compare_data_list[0].get('data')
            return None
        except Exception as e:
            _logger.error('解析出错! {}'.format(e))
            return None

    def parse_compare_display_data(self, compare_id):
        try:
            if compare_id.display_data:
                compare_data = compare_id.display_data
                compare_data = eval(compare_data)
                return [{'value': x.get('display_data')} for x in compare_data]
            else:
                compare_data = compare_id.value
                compare_data = json.loads(compare_data)
                compare_data_list = compare_data.get('data', [])
                if compare_data_list:
                    return compare_data_list[0].get('display_data', [])
            return None
        except Exception as e:
            import traceback
            _logger.error('解析出错! {}, {}'.format(e, traceback.format_exc()))
            return None

    @http.route('/api/wechat/mini/vip/content', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def query_vip_content(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        check_access_right = self.save_and_check_query_time(stock_id)
        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip and not check_access_right:
            err_msg = '未订阅用户，仅允许查询{}次!'.format(ALLOW_QUERY_TIME)
            return self.response_json_error(-1, err_msg)

        benchmark_data_ids = request.env['compare.benchmark.data'].sudo().search([
            ('stock_id', '=', stock_id.id),
            ('compare_id.active', '=', True)
        ])
        type_ids = sorted(list(set(benchmark_data_ids.compare_id.mapped('type_id'))))
        if False not in type_ids:
            type_ids.append(False)
        vip_content = []
        benchmark_count = {
            'danger': 0,
            'rain': 0,
            'sun': 0,
        }
        for type_id in type_ids:
            tmp_data = []

            if type_id:
                benchmark_ids = benchmark_data_ids.filtered(lambda bd: bd.compare_id.type_id == type_id)
            else:
                benchmark_ids = benchmark_data_ids.filtered(lambda bd: not bd.compare_id.type_id)
            for benchmark_data_id in benchmark_ids:
                tmp_data.append({
                    'name': benchmark_data_id.compare_id.name,
                    'value': self.parse_compare_value(benchmark_data_id.value),
                    'sign': benchmark_data_id.sign,
                    'benchmark_id': benchmark_data_id.id,
                    'compare_type': benchmark_data_id.compare_id.value_type
                })
                benchmark_count.update({
                    benchmark_data_id.sign: benchmark_count.get(benchmark_data_id.sign) + 1
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
            'data': vip_content,
            'benchmark_count': benchmark_count
        }
        # data.update(**encrypt_data)
        return self.response_json_success(data)

    @http.route('/v1/api/wechat/mini/vip/content', auth='public', methods=['POST'], csrf=False, type='json')
    @verify_auth_token()
    def query_vip_content_data(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        # 拼音缩写
        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([
            '|',
            '|',
            '|',
            ('symbol', '=', stock_code),
            ('ts_code', '=', stock_code),
            ('cnspell', '=', stock_code),
            ('name', '=', stock_code),
        ], limit=1)

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        check_access_right = self.save_and_check_query_time(stock_id)
        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip and not check_access_right:
            err_msg = '未订阅用户，仅允许查询{}次!'.format(ALLOW_QUERY_TIME)
            return self.response_json_error(-1, err_msg)

        benchmark_data_ids = request.env['compare.benchmark.data'].sudo().search([
            ('stock_id', '=', stock_id.id),
            ('compare_id.active', '=', True)
        ])
        vip_content = []
        benchmark_count = {
            'danger': 0,
            'rain': 0,
            'sun': 0,
        }

        for benchmark_data_id in benchmark_data_ids:
            value_type = benchmark_data_id.compare_id.value_type
            if value_type == 'value':
                display_data = self.parse_compare_display_data(benchmark_data_id)
                origin_data = display_data
            else:
                display_data = self.parse_compare_value(benchmark_data_id.value)
                origin_data = self.parse_compare_display_data(benchmark_data_id)

            if not display_data:
                display_data = [{'value': '暂无'}]
            tmp_data = {
                'name': benchmark_data_id.compare_id.name,
                'value': display_data,
                'origin_data': origin_data,
                'data': display_data,
                'chart': display_data,
                'sign': benchmark_data_id.sign,
                'benchmark_id': benchmark_data_id.id,
                'compare_type': benchmark_data_id.compare_id.value_type
            }
            benchmark_count.update({
                benchmark_data_id.sign: benchmark_count.get(benchmark_data_id.sign) + 1
            })
            vip_content.append(tmp_data)
        # vip_content_json = json.dumps(vip_content)
        # encrypt_data = aes_encrypt_msg(vip_content_json)
        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'data': vip_content,
            'benchmark_count': benchmark_count
        }
        # data.update(**encrypt_data)
        return self.response_json_success(data)

    @http.route('/v1/api/wechat/mini/vip/count', auth='public', methods=['POST'], csrf=False, type='json')
    @verify_auth_token()
    def query_vip_count_data(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')

        stock_id = request.env['finance.stock.basic'].sudo().search([
            '|',
            '|',
            '|',
            ('symbol', '=', stock_code),
            ('ts_code', '=', stock_code),
            ('cnspell', '=', stock_code),
            ('name', '=', stock_code),
        ], limit=1)

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')

        benchmark_data_ids = request.env['compare.benchmark.data'].sudo().search([
            ('stock_id', '=', stock_id.id),
            ('compare_id.active', '=', True)
        ])
        benchmark_count = {
            'danger': 0,
            'rain': 0,
            'sun': 0,
        }

        for benchmark_data_id in benchmark_data_ids:
            benchmark_count.update({
                benchmark_data_id.sign: benchmark_count.get(benchmark_data_id.sign) + 1
            })
        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'danger': benchmark_count.get('danger'),
            'rain': benchmark_count.get('rain'),
            'sun': benchmark_count.get('sun'),
        }
        return self.response_json_success(data)

    def parse_vip_content_detail(self, data):
        result = json.loads(data)
        return_data = []
        for line_data in result.get('data'):
            for compare_line_data in line_data.get('data'):
                if len(compare_line_data) > 1:
                    return_data.append({
                        'date': compare_line_data[1] if len(compare_line_data) > 1 else None,
                        'value': compare_line_data[0]
                    })
        if return_data:
            return_data = sorted(return_data, key=lambda x: x.get('date'))
        return return_data

    @http.route('/api/wechat/mini/vip/content/detail', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def query_vip_content_detail(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_code = body.get('stock_code')
        benchmark_id = body.get('benchmark_id')

        stock_id = request.env['finance.stock.basic'].sudo().search([('symbol', '=', stock_code)])

        if not stock_id:
            return self.response_json_error(404, '股票不存在!')
        check_access_right = self.save_and_check_query_time(stock_id)
        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip and not check_access_right:
            err_msg = '未订阅用户，仅允许查询{}次!'.format(ALLOW_QUERY_TIME)
            return self.response_json_error(-1, err_msg)

        try:
            benchmark_id = int(benchmark_id)
        except Exception as e:
            return self.response_json_error(-1, '参数错误')

        benchmark_data_id = request.env['compare.benchmark.data'].sudo().browse(benchmark_id)

        content_detail = self.parse_vip_content_detail(benchmark_data_id.value)
        if not content_detail:
            return self.response_json_error(-1, '暂无数据')

        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'data': self.parse_vip_content_detail(benchmark_data_id.value),
            'benchmark': benchmark_data_id.compare_id.name
        }
        return self.response_json_success(data)
