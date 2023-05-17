# -*- coding: utf-8 -*-
import json
from odoo import http, exceptions, fields
from odoo.http import request
from .base import BaseController
from odoo.tools import config
import logging
from .wxa_common import verify_auth_token
from ..utils import get_redis_client

_logger = logging.getLogger(__name__)


class QueryHis(http.Controller, BaseController):

    def parse_redis_value(self, parse_data):
        try:
            result = json.loads(parse_data)
            return result
        except Exception as e:
            return {
                'code': parse_data
            }

    @http.route('/api/wechat/mini/query/his/list', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def query_his(self, **kwargs):

        wx_uid = http.request.wxa_uid
        redis_client = get_redis_client(config.get('redis_cache_db'))
        store_key = '{}:{}:query:stock'.format(config.get('redis_cache_prefix'), wx_uid)

        res = redis_client.lrange(store_key, 0, 10)
        data = {
            'data': [self.parse_redis_value(x.decode()) for x in res]
        }
        return self.response_json_success(data)

    @http.route('/api/wechat/mini/query/his/unlink', auth='public', methods=['POST'],
                csrf=False, type='json')
    @verify_auth_token()
    def del_query_his(self, **kwargs):
        payload_data = json.loads(request.httprequest.data)

        query_word = payload_data.get('body', {}).get('key')
        if not query_word:
            return self.response_json_error(-1, '参数错误')
        wx_uid = http.request.wxa_uid
        redis_client = get_redis_client(config.get('redis_cache_db'))
        store_key = '{}:{}:query:stock'.format(config.get('redis_cache_prefix'), wx_uid)

        res = redis_client.lrem(store_key, query_word, 2)
        data = {
            'success': query_word
        }
        return self.response_json_success(data)
