# -*- coding: utf-8 -*-
import sys
import json
from .wxa_common import verify_auth_token
from odoo.tools import config
from odoo import http
from odoo.http import request
import redis
from ..utils import get_redis_client
from .base import BaseController

import logging

_logger = logging.getLogger(__name__)


class FinanceMineSweep(http.Controller, BaseController):

    def pre_check(self, entry, wechat_user, post_data):
        return None

    def save_query_to_redis(self, stock_code):
        wx_uid = http.request.wxa_uid
        store_key = '{}:{}:query:stock'.format(config.get('redis_cache_prefix'), wx_uid)
        redis_client = get_redis_client(config.get('redis_cache_db'))
        all_values = redis_client.lrange(store_key, 0, -1 )
        all_values = [x.decode() for x in all_values]
        if stock_code not in all_values:
            redis_client.lpush(store_key, stock_code)
            redis_client.close()

    @http.route(['/api/wechat/mini/stock/validate'], auth='public', methods=['POST'], csrf=False,
                type='json')
    def validate_stock(self):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code')
        if not stock_code:
            return self.response_json_error(-1, '请输入股票代码')
        try:
            res = request.env['finance.stock.basic'].sudo().search([
                '|',
                ('symbol', '=', stock_code),
                ('ts_code', '=', stock_code)
            ])
            if not res:
                return self.response_json_error(-1, '请求的股票代码 [{}] 无效!'.format(stock_code))
            return self.response_json_success({
                'code': stock_code
            })
        except Exception as e:
            _logger.exception(e)
            return self.response_json_error(-1, str(e))

    @http.route(['/api/wechat/mini/sweep/list'], auth='public', methods=['GET', 'POST'], csrf=False,
                type='json')
    @verify_auth_token()
    def mine_sweep_list(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code', None)
        try:
            user_is_vip = self._check_user_is_vip(request.wxa_uid)

            res = request.env['stock.compare.analysis'].get_mine_list(vip_mode=user_is_vip)
            return self.response_json_success(res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))

    @http.route(['/api/wechat/mini/sweep/value/free'], auth='public', methods=['GET', 'POST'], csrf=False,
                type='json')
    @verify_auth_token()
    def get_free_stock_value(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code', None)

        stock_id = request.env['finance.stock.basic'].sudo().search([
            ('symbol', '=', stock_code)
        ], limit=1)
        if not stock_id:
            result = {
                'peg': '',
                'pleg': '',
                'pleg_freeze': '',
                'restricted': '',
                'shr_red': '',
                'gw_netast': '',
                'options': '',
                'law_case': ''
            }
            return self.response_json_success(result)
        result = {
            'peg': stock_id.peg_car or '暂无',
            'plge': stock_id.plge_rat or '暂无',
            'plge_freeze': stock_id.plge_shr or '暂无',
            'restricted': stock_id.restricted_json or '暂无',
            'shr_red': stock_id.shr_red_json or '暂无',
            'gw_netast': stock_id.gw_netast_rat or '暂无',
            'options': stock_id.options_rslt or '暂无',
            'law_case': stock_id.law_case or 0
        }
        self.save_query_to_redis(stock_code)
        return self.response_json_success(result)

    @http.route(['/api/wechat/mini/sweep/value/vip'], auth='public', methods=['POST'], csrf=False, type='json')
    def mine_sweep_value(self):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        security_code = body.get('security_code', None)
        mine_uuid = body.get('uuid', None)
        if not all([security_code, mine_uuid]):
            return self.res_err(-1, str('请选择股票代码/UUID'))

        try:
            analysis_res = request.env['stock.compare.analysis'].query_mine_sweep_data(request.wxa_uid, mine_uuid,
                                                                                       security_code)

            return self.res_ok(analysis_res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))
