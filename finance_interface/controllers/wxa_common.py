# -*- coding: utf-8 -*-
from odoo import http
from .response_code import ResponseCode
from odoo.http import request
from odoo import fields
from odoo.tools import ormcache
import requests
import json
from functools import wraps
import logging

_logger = logging.getLogger(__name__)


def get_wxa_access_token(appid, secret):
    req_url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}'.format(
        appid, secret
    )
    res = requests.get(req_url)
    result = res.json()
    return result


def get_wxa_user_openid(access_token, js_code):
    req_url = 'https://api.weixin.qq.com/wxa/getpluginopenpid?access_token={}'.format(access_token)
    payload_data = {
        'code': js_code
    }
    res = requests.post(req_url, data=payload_data)
    result = res.json()
    return result


@ormcache('access_token')
def get_wxa_user(access_token):
    wx_user = request.env['wxa.user'].sudo().search([
        ('user_uuid', '=', access_token),
        ('forbidden_user', '=', False)
    ])
    return wx_user


def check_access_token(access_token):
    wx_user = request.env['wxa.user'].sudo().search([
        ('user_uuid', '=', access_token)
    ])
    if not wx_user:
        return False
    http.request.wxa_uid = wx_user[0].id
    http.request.wxa_openid = wx_user[0].open_id
    return True


def verify_auth_token():
    def decorator(func):
        @wraps(func)
        def decorated_function(request, *args, **kwargs):
            access_token = http.request.httprequest.headers.get('Authorization')
            if not access_token:
                _logger.error('access token 异常, 数据为空')
                results = ResponseCode.CODE_403
                return results

            if access_token.startswith('Bearer '):
                access_token = access_token[7:]

            if not access_token:
                _logger.error('access token 异常，无效数据')
                results = ResponseCode.CODE_403
                return results

            verify_token = check_access_token(access_token)
            if not verify_token:
                _logger.error('access token 异常，认证失败')
                results = ResponseCode.CODE_403
                return results
            return func(request, *args, **kwargs)

        return decorated_function

    return decorator


def save_operate_log(payload_data):
    res = request.env['wxa.operate.log'].sudo().create_with_delay(payload_data)
    _logger.info('创建成功: {}'.format(res))


def log_operate_request():
    def decorator(func):
        @wraps(func)
        def decorated_function(request, *args, **kwargs):
            try:
                payload_data = {
                    'name': http.request.httprequest.path,
                    'operate_wxa_uid': http.request.wxa_uid,
                    'operate_detail': http.request.httprequest.data.decode(),
                    'operate_path': http.request.httprequest.path,
                    'operate_header': {item_key: http.request.httprequest.headers.get(item_key) for item_key in
                                       http.request.httprequest.headers.keys()},
                    'operate_date': fields.Datetime.now()
                }
                save_operate_log(payload_data)
            except Exception as e:
                _logger.error('保存出错: {}'.format(e))
            return func(request, *args, **kwargs)

        return decorated_function

    return decorator


def check_payload_sign():
    pass
