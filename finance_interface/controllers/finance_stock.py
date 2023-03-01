# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from .base import BaseController
from .wxa_common import verify_auth_token
import logging
from itertools import groupby
from odoo.tools import ormcache
import uuid
from odoo.tools import config

_logger = logging.getLogger(__name__)

# APP_MINI_ID = config.get('wxa_app_id')
# APP_MINI_SECRET = config.get('wxa_app_secret')

APP_MINI_ID = 'wxb0d07325ab5d8d9b'
APP_MINI_SECRET = '0d1b8355aff72dd0c83d910d1353e224'

STOCK_DICT = {
    'SSE': '上交所',
    'SZSE': '深交所',
    'OTHER': '其它'
}


class FinanceStock(http.Controller, BaseController):

    def get_finance_basic_value(self, exchange):
        result = request.env['finance.stock.basic'].sudo().get_finance_basic_value(exchange)
        return result

    @http.route('/api/wechat/mini/finance/stock/exchange', auth='public', methods=['POST'], csrf=False, cors="*",
                type='json')
    # @verify_auth_token()
    def finance_stock_exchange(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        result = [{
            'exchange': STOCK_DICT.get(exchange_key),
            'title': exchange_key,
            'badgeProps': {},
            'items': []
        } for exchange_key in STOCK_DICT.keys()]
        return self.response_json_success(result)

    @http.route('/api/wechat/mini/finance/stock/list', auth='public', methods=['POST'], csrf=False, cors="*",
                type='json')
    # @verify_auth_token()
    def finance_stock_list(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')

        exchange = body.get('exchange')

        result = self.get_finance_basic_value(exchange)

        return self.response_json_success(result)
