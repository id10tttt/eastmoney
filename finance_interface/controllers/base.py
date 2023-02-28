# -*- coding: utf-8 -*-
import logging
from .response_code import ResponseCode
_logger = logging.getLogger(__name__)

ERROR_CODE = {
    -1: u'禁止访问',
}


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
