# -*- coding: utf-8 -*-
import json
import odoo
from odoo import http
from odoo.http import request
from odoo import fields
import traceback
from .base import BaseController
from .tools import get_wx_session_info, get_wx_user_info, get_decrypt_info

import logging

_logger = logging.getLogger(__name__)


class WxUser(http.Controller, BaseController):

    def user_auth(self, username, password):
        _code = -1
        _error = '登录异常'
        old_uid = request.uid
        try:
            uid = request.session.authenticate(request.session.db, username, password)
            return 0, uid
        except odoo.exceptions.AccessDenied as e:
            try:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    _error = '用户名或密码不正确'
                    _code = -2
                else:
                    _error = e.args[0]
                    _code = -99
                _logger.info('>>> %s %s', _code, _error)
                return _code, _error
            finally:
                pass

    @http.route('/finance/<string:sub_domain>/user/bind/login', auth='public', methods=['POST'], csrf=False,
                type='http')
    def bind(self, sub_domain, **kwargs):
        http_headers = request.httprequest.headers
        headers = kwargs.get('header')
        body = kwargs.get('body')
        try:
            token = headers.get('token', None)
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res:
                return res
            username = body.get('username', None)
            password = body.get('password', None)
            _code, ret = self.user_auth(username, password)
            if _code == 0:
                request.session['login_uid'] = ret
                _logger.info('>>> set session login_uid %s', ret)
                wechat_user.write({
                    'user_id': ret,
                    'partner_id': request.env['res.users'].sudo().browse(ret).partner_id.id,
                    'category_id': [(4, request.env.ref('finance_interface.res_partner_category_mine_1').sudo().id)]
                })
                return self.res_ok({'userid': ret})
            return self.res_err(_code, ret)
        except Exception as e:
            _logger.error('bind error: {}'.format(e))
            return self.res_err(-1, '服务异常')

    @http.route('/finance/<string:sub_domain>/user/check-token', auth='public', methods=['GET'])
    def check_token(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        try:
            token = headers.get('token', None)
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res:
                return self.res_err(609)

            if wechat_user.check_account_ok():
                data = self.get_user_info(wechat_user)
                return self.res_ok(data)
            else:
                return self.res_err(608, u'账号不可用')
        except Exception as e:
            _logger.error('check_token error: {}'.format(e))
            return self.res_err(-1, str(e))

    @http.route(['/finance/<string:sub_domain>/user/wx/login', '/finance/<string:sub_domain>/user/wx/authorize'],
                auth='public', methods=['GET', 'POST'], csrf=False)
    def login(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        code = body.get('code')
        try:
            ret, entry = self._check_domain(sub_domain)
            if ret:
                return ret

            if not code:
                return self.res_err(300)

            app_id = entry.get_config('app_id')
            secret = entry.get_config('secret')

            if not app_id or not secret:
                return self.res_err(404)

            session_info = get_wx_session_info(app_id, secret, code)
            if session_info.get('errcode'):
                return self.res_err(-1, session_info.get('errmsg'))

            open_id = session_info['openid']
            wechat_user = request.env(user=1)['wx.user'].search([
                ('open_id', '=', open_id),
                # ('create_uid', '=', user.id)
            ])
            if not wechat_user:
                return self.res_err(10000, {'session_info': session_info})

            wechat_user.write({
                'last_login': fields.Datetime.now(),
                'ip': request.httprequest.remote_addr
            })
            access_token = request.env(user=1)['wx.access.token'].search([
                ('open_id', '=', open_id),
                # ('create_uid', '=', user.id)
            ])

            if not access_token:
                session_key = session_info['session_key']
                access_token = request.env(user=1)['wx.access.token'].create({
                    'open_id': open_id,
                    'session_key': session_key,
                    'sub_domain': sub_domain,
                })
            else:
                access_token.write({'session_key': session_info['session_key']})

            data = {
                'token': access_token.token,
                'uid': wechat_user.id,
                'info': self.get_user_info(wechat_user)
            }
            return self.res_ok(data)

        except AttributeError as e:
            _logger.error('报错了: {}, {}'.format(traceback.format_exc(), e))
            return self.res_err(404)

        except Exception as e:
            _logger.error('login error: {}'.format(e))
            return self.res_err(-1, str(e))

    @http.route('/finance/<string:sub_domain>/user/wx/register/complex', auth='public', methods=['POST'],
                csrf=False)
    def register(self, sub_domain, **kwargs):
        '''
        用户注册
        '''
        headers = kwargs.get('header')
        body = kwargs.get('body')
        username = body.get('username')
        password = body.get('password')
        code = body.get('code')
        iv = body.get('iv')
        if username:
            _code, ret = self.user_auth(username, password)
            if _code == 0:
                request.user_id = ret
            else:
                return self.res_err(_code, ret)
        try:
            ret, entry = self._check_domain(sub_domain)
            if ret:
                return ret

            session_info = body.get('session_info')
            if session_info:
                session_info = json.loads(session_info)
                user_info = {
                    'nickName': '微信用户',
                    'openId': session_info.get('openid'),
                    'unionId': session_info.get('unionid')
                }
            else:
                encrypted_data = body.get('encryptedData')
                if not code or not encrypted_data or not iv:
                    return self.res_err(300)

                app_id = entry.get_config('app_id')
                secret = entry.get_config('secret')

                if not app_id or not secret:
                    return self.res_err(404)

                session_key, user_info = get_wx_user_info(app_id, secret, code, encrypted_data, iv)
                if kwargs.get('userInfo'):
                    user_info.update(json.loads(kwargs.get('userInfo')))

            user_id = None
            if hasattr(request, 'user_id'):
                user_id = request.user_id

            vals = {
                'name': user_info['nickName'],
                'nickname': user_info['nickName'],
                'open_id': user_info['openId'],
                'gender': user_info.get('gender'),
                'language': user_info.get('language'),
                'country': user_info.get('country'),
                'province': user_info.get('province'),
                'city': user_info.get('city'),
                'avatar_url': user_info.get('avatarUrl'),
                'register_ip': request.httprequest.remote_addr,
                'user_id': user_id,
                'partner_id': user_id and request.env['res.users'].sudo().browse(user_id).partner_id.id or None,
                'category_id': [(4, request.env.ref('finance_interface.res_partner_category_mine_1').sudo().id)],
                'entry_id': entry.id,
            }
            if user_id:
                vals['user_id'] = user_id
                vals['partner_id'] = request.env['res.users'].sudo().browse(user_id).partner_id.id
                vals.pop('name')
            try:
                wechat_user = request.env(user=1)['wx.user'].create(vals)
            except Exception as e:
                _logger.error('报错了: {}, {}'.format(traceback.format_exc(), e))
                return self.res_err(-99, u'账号状态异常')
            wechat_user.action_created(vals)
            request.wechat_user = wechat_user
            request.entry = entry
            return self.res_ok()

        except AttributeError:
            return self.res_err(404)

        except Exception as e:
            _logger.error('register error: {}'.format(e))
            return self.res_err(-1, str(e))

    def get_user_info(self, wechat_user):
        mobile = ''
        if hasattr(wechat_user, 'partner_id'):
            mobile = wechat_user.partner_id.mobile
        user = wechat_user.user_id
        data = {
            'base': {
                'mobile': mobile or '',
                'username': user and user.login or '',
                'nickname': user and user.name or '',
                'avatar': wechat_user.avatar_url or '',
                'userid': user and user.id or '',
            },
        }
        return data

    def get_user_more(self, wechat_user):
        return {}

    @http.route('/finance/<string:sub_domain>/user/detail', auth='public', methods=['GET'])
    def detail(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        token = headers.get('token')
        try:
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res:
                return res

            data = self.get_user_info(wechat_user)
            data.update(self.get_user_more(wechat_user))
            return self.res_ok(data)

        except Exception as e:
            _logger.error('detail error: {}'.format(e))
            return self.res_err(-1, str(e))

    @http.route('/finance/<string:sub_domain>/user/wx/bind', auth='public', methods=['GET', 'POST'],
                csrf=False)
    def bind_mobile(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        iv = body.get('iv')
        token = headers.get('token')
        try:
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res and not wechat_user:
                return res

            encrypted_data = body.get('encryptedData')
            if not token or not encrypted_data or not iv:
                return self.res_err(300)

            app_id = entry.get_config('app_id')
            secret = entry.get_config('secret')

            if not app_id or not secret:
                return self.res_err(404)

            access_token = request.env(user=1)['wx.access.token'].search([
                ('token', '=', token),
            ])
            if not access_token:
                return self.res_err(901)
            session_key = access_token[0].session_key

            _logger.info('>>> decrypt: %s %s %s %s', app_id, session_key, encrypted_data, iv)
            user_info = get_decrypt_info(app_id, session_key, encrypted_data, iv)
            _logger.info('>>> bind_mobile: %s', user_info)
            wechat_user.bind_mobile(user_info.get('phoneNumber'))
            ret = {
                'account_ok': wechat_user.check_account_ok(),
            }
            return self.res_ok(ret)

        except Exception as e:
            _logger.error('bind_mobile error: {}'.format(e))
            return self.res_err(-1, str(e))

    @http.route('/finance/<string:sub_domain>/user/amount', auth='public', methods=['GET'])
    def user_amount(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        token = headers.get('token')
        try:
            res, wechat_user, entry = self._check_user(sub_domain, token)
            if res:
                if entry and kwargs.get('access_token'):
                    return self.res_ok({'balance': 0, 'score': 0})
                else:
                    return res
            _data = {
                'balance': wechat_user.get_balance(),
                'creditLimit': wechat_user.get_credit_limit(),
                'freeze': 0,
                'score': wechat_user.get_score(),
                'totleConsumed': 0,
            }
            return self.res_ok(_data)

        except Exception as e:
            _logger.error('user_amount error: {}'.format(e))
            return self.res_err(-1, str(e))
