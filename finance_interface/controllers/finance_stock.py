# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json
from .base import BaseController
from .wxa_common import verify_auth_token
import logging
from itertools import groupby as itergroupby
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

    @http.route('/api/wechat/mini/finance/stock/list', auth='public', methods=['POST'], csrf=False, cors="*",
                type='json')
    @verify_auth_token()
    def finance_stock_list(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')

        stock_data = request.env['finance.stock.basic'].sudo().search_read(
            domain=[], fields=['ts_code', 'symbol', 'name', 'exchange', 'id'])

        groupby_stock_data = {
            exchange_key: list(tuple(y)) for exchange_key, y in itergroupby(stock_data, lambda x: x.get('exchange'))}

        result = [{
            'exchange': STOCK_DICT.get(stock_key, '其它'),
            'title': stock_key,
            'badgeProps': {},
            'items': groupby_stock_data.get(stock_key)
        } for stock_key in groupby_stock_data.keys()]

        return self.response_json_success(result)
