# -*- coding: utf-8 -*-
import sys
import json

from odoo import http
from odoo.http import request

from .. import utils
from .base import BaseController
from .base import convert_static_link

import logging

_logger = logging.getLogger(__name__)


class FinanceMineSweep(http.Controller, BaseController):

    def pre_check(self, entry, wechat_user, post_data):
        return None

    @http.route(['/finance/<string:sub_domain>/sweep/list'], auth='public', methods=['GET', 'POST'], csrf=False)
    def mine_sweep_list(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        token = headers.get('token', None)
        try:
            ret, wechat_user, entry = self._check_user(sub_domain, token)
            if ret:
                return ret
            self.pre_check(entry, wechat_user, kwargs)
            user_is_vip = self._check_user_is_vip(wechat_user)

            _logger.info('微信用户: {}'.format(wechat_user))
            res = request.env['stock.compare.analysis'].get_mine_list(vip_mode=user_is_vip)
            return self.res_ok(res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))

    @http.route(['/finance/<string:sub_domain>/sweep/value'], auth='public', methods=['POST'], csrf=False)
    def mine_sweep_value(self, sub_domain, **kwargs):
        headers = kwargs.get('header')
        body = kwargs.get('body')
        token = headers.get('token', None)
        security_code = body.get('security_code', None)
        mine_uuid = body.get('uuid', None)
        if not all([security_code, mine_uuid]):
            return self.res_err(-1, str('请选择股票代码/UUID'))

        try:
            ret, wechat_user, entry = self._check_user(sub_domain, token)
            if ret:
                return ret
            self.pre_check(entry, wechat_user, kwargs)
            _logger.info('微信用户: {}'.format(wechat_user))
            analysis_res = request.env['stock.compare.analysis'].query_mine_sweep_data(wechat_user, mine_uuid,
                                                                                       security_code)

            return self.res_ok(analysis_res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))
