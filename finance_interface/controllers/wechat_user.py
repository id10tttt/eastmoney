# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from wechatpy import WeChatClient
from wechatpy.crypto import WeChatWxaCrypto
import json
from .base import BaseController
import logging
import time
import traceback
import uuid
from .wxa_common import verify_auth_token, get_wxa_user_openid, get_wxa_access_token
from odoo.tools import config

_logger = logging.getLogger(__name__)

# APP_MINI_ID = config.get('wxa_app_id')
# APP_MINI_SECRET = config.get('wxa_app_secret')


# 测试账号
APP_MINI_ID = 'wxb0d07325ab5d8d9b'
APP_MINI_SECRET = '0d1b8355aff72dd0c83d910d1353e224'


class WeChatUser(http.Controller, BaseController):

    def parse_wechat_user_info(self, user_info):
        return {
            'name': user_info['nickName'],
            'nickname': user_info['nickName'],
            'gender': user_info.get('gender'),
            'language': user_info.get('language'),
            'country': user_info.get('country'),
            'province': user_info.get('province'),
            'city': user_info.get('city'),
            'avatar_url': user_info.get('avatarUrl'),
            'register_ip': request.httprequest.remote_addr,
            'phone': user_info.get('purePhoneNumber'),
            'user_uuid': str(uuid.uuid4())
        }

    def save_update_wechat_user_info(self, openid, user_info):
        try:
            user_id = request.env['wxa.user'].sudo().search([('open_id', '=', openid)])
            if user_id:
                if user_info:
                    user_data = self.parse_wechat_user_info(user_info)
                    user_id[0].write(user_data)
                    _logger.info('更新用户: {}'.format(openid))
            else:
                user_data = {
                    'open_id': openid,
                    'name': '微信用户',
                    'nickname': '微信用户',
                }
                if user_info:
                    user_data.update(self.parse_wechat_user_info(user_info))
                user_id = request.env['wxa.user'].sudo().create(user_data)
                _logger.info('创建用户: {}, {}'.format(user_id, openid))
            return user_id.user_uuid
        except Exception as e:
            _logger.error('e: {}, {}'.format(e, traceback.format_exc()))

    @http.route('/api/wechat/mini/user/auth', auth='public', methods=['POST'], csrf=False, cors="*", type='json')
    def wechat_mini_user_login(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        user_name = body.get('user_name')
        password = body.get('password')

        if not all([user_name, password]):
            return self.response_json_error(-1, '参数错误')

        try:
            uid = request.session.authenticate(request.session.db, user_name, password)
        except Exception as e:
            return self.response_json_error(-1, '认证失败: {}'.format(e))
        if not uid:
            return self.response_json_success({'success': 0, 'code': 403, 'message': 'Forbidden'})

        result = {
            'uid': uid
        }
        return self.response_json_success(result)

    @http.route('/api/wechat/mini/program/login', auth='public', methods=['POST'], csrf=False, cors="*", type='json')
    def wechat_mini_program_login(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        user_code = body.get('code', None)

        # 为啥code to session 如此慢呢？
        wechat_client = WeChatClient(APP_MINI_ID, APP_MINI_SECRET)
        try:
            session_data = wechat_client.wxa.code_to_session(user_code)
        except Exception as e:
            _logger.error('登录失败: {}'.format(e))
            return self.response_json_error(-1, '登录失败! {}'.format(e))

        self.save_update_wechat_user_info(session_data.get('openid'), {})
        user_token = self.save_update_wechat_user_info(session_data.get('openid'), {})
        session_data.update({
            'token': {
                'access_token': user_token,
                'refresh_token': ''
            },
            'user_info': {}
        })
        return self.response_json_success(session_data)

    @http.route('/api/wechat/mini/token/check', auth='public', methods=['POST'], csrf=True, cors="*", type='json')
    @verify_auth_token()
    def check_user_token(self):
        payload_data = json.loads(request.httprequest.data)
        return self.response_json_success({
            'msg': 'success'
        })

    @http.route('/api/wechat/mini/program/bind', auth='public', methods=['POST'], csrf=False, type='json', cors="*", )
    def wechat_mini_program_bind(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        user_code = body.get('code', None)
        session_key = body.get('session_key', None)
        encrypted_data = body.get('encryptedData', None)
        user_info = body.get('user_info')
        openid = body.get('openid')
        iv = body.get('iv', None)
        if not session_key:
            return self.response_json_error(-1, 'session_key为空')
        if not iv:
            return self.response_json_error(-1, 'getPhoneNumber权限错误!')
        wxa_decrypt = WeChatWxaCrypto(session_key, iv, APP_MINI_ID)

        try:
            decrypt_data = wxa_decrypt.decrypt_message(encrypted_data)
        except Exception as e:
            err_msg = '解密失败, {}'.format(e)
            _logger.error(err_msg)
            return self.response_json_error(-1, err_msg)

        user_info.update({
            'purePhoneNumber': decrypt_data.get('purePhoneNumber')
        })
        user_token = self.save_update_wechat_user_info(openid, user_info)
        decrypt_data.update({
            'token': {
                'access_token': user_token,
                'refresh_token': ''
            },
            'user_info': user_info
        })
        return self.response_json_success(decrypt_data)

    @http.route('/api/wechat/mini/vip/check', auth='public', methods=['POST'], csrf=True, cors="*", type='json')
    @verify_auth_token()
    def check_user_is_vip(self):
        payload_data = json.loads(request.httprequest.data)

        user_vip = request.env['wxa.subscribe.order'].sudo().wx_user_is_vip(request.wxa_uid)
        if not user_vip:
            return self.response_json_error(-1, '没有权限查看')
        return self.response_json_success({
            'msg': 'success'
        })