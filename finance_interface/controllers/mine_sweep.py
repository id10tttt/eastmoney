# -*- coding: utf-8 -*-
import sys
import json
from .wxa_common import verify_auth_token
from odoo import http
from odoo.http import request

from .base import BaseController

import logging

_logger = logging.getLogger(__name__)


class FinanceMineSweep(http.Controller, BaseController):

    def pre_check(self, entry, wechat_user, post_data):
        return None

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
        print('payload_data: ', payload_data)
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
    def get_free_stock_value(self):
        payload_data = json.loads(request.httprequest.data)
        print('payload_data: ', payload_data)
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
            'peg': stock_id.peg_car,
            'plge': stock_id.plge_rat,
            'plge_freeze': stock_id.plge_shr,
            'restricted': stock_id.restricted_json,
            'shr_red': stock_id.shr_red_json,
            'gw_netast': stock_id.gw_netast_rat,
            'options': stock_id.options_rslt,
            'law_case': stock_id.law_case or 0
        }
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
