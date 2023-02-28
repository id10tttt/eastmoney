# -*- coding: utf-8 -*-
import json
from odoo import http, exceptions, fields
from odoo.http import request
from .base import BaseController
import logging

_logger = logging.getLogger(__name__)


class Subscribe(http.Controller, BaseController):

    @http.route('/api/wechat/mini/pay/subscribe/list', auth='public', methods=['POST'],
                csrf=False, type='json')
    def query_subscribe_list(self, **kwargs):
        """
        获取订阅链接
        """
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        user_open_id = headers.get('openid')

        token = kwargs.pop('token', None)
        subscribe_data = request.env['wxa.subscribe'].sudo().get_all_subscribe_data()
        return self.response_json_success(subscribe_data)
