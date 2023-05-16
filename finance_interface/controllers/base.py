# -*- coding: utf-8 -*-
import logging
from .response_code import ResponseCode
from odoo.tools import config
import json
from odoo import http
from ..utils import get_redis_client
_logger = logging.getLogger(__name__)

ERROR_CODE = {
    -1: u'禁止访问',
}
ALLOW_QUERY_TIME = 3

EXPIRY_TIME = 30 * 3 * 24 * 60 * 60


class UserException(Exception):
    pass


class BaseController(object):

    def response_json_success(self, data=None):
        result = ResponseCode.CODE_200
        if data is not None:
            result['data'] = data
        return result

    def response_json_error(self, code, data=None):
        custom_code = 'CODE_{}'.format(code)
        if hasattr(ResponseCode, custom_code):
            result = getattr(ResponseCode, custom_code)
        else:
            result = ResponseCode.CODE_403
        if data:
            result['data'] = data
        return result

    def save_and_check_query_time(self, stock_id=None):
        wx_uid = http.request.wxa_uid
        query_redis_prefix = '{}:{}:query:stock:vip'.format(config.get('redis_cache_prefix'), wx_uid)
        redis_client = get_redis_client(config.get('redis_cache_db'))
        if stock_id:
            store_key = '{}:{}'.format(query_redis_prefix, stock_id.symbol)

            # TODO: 不定
            # 如果已经存在，则允许查询
            # if redis_client.get(store_key):
            #     return True

            # 如果没有查询过，则验证是否超过数量限制
            res = redis_client.keys('{}:*'.format(query_redis_prefix))
            if len(res) < ALLOW_QUERY_TIME:
                # 保存查询记录
                redis_client.set(store_key, json.dumps({
                    'code': stock_id.symbol,
                    'name': stock_id.name
                }), ex=EXPIRY_TIME)
                return True

            return False
        else:
            res = redis_client.keys('{}:*'.format(query_redis_prefix))
            if len(res) <= ALLOW_QUERY_TIME:
                return True
            return False
