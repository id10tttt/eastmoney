# -*- coding: utf-8 -*-
import json
import datetime
import decimal
from .wxa_common import verify_auth_token
from odoo.tools import config
from odoo import http
from odoo.http import request
from ..utils import get_redis_client
from .base import BaseController

import logging

_logger = logging.getLogger(__name__)


def decimal_float_number(number, rounding='0.00'):
    decimal.getcontext().rounding = "ROUND_HALF_UP"
    res = decimal.Decimal(str(number)).quantize(decimal.Decimal(rounding))
    return str(res)


def convert_timestamp_to_datetime(timestamp):
    try:
        if timestamp:
            dt = datetime.datetime.fromtimestamp(timestamp / 1000)
            return str(dt.date())
        else:
            return timestamp
    except Exception as e:
        _logger.error('error: {}'.format(e))
        return timestamp


class FinanceMineSweep(http.Controller, BaseController):

    def pre_check(self, entry, wechat_user, post_data):
        return None

    def parse_redis_value(self, parse_data):
        try:
            result = json.loads(parse_data)
            return result.get('code')
        except Exception as e:
            return parse_data

    def save_query_to_redis(self, stock_id):
        stock_code = stock_id.symbol
        stock_name = stock_id.name
        wx_uid = http.request.wxa_uid
        store_key = '{}:{}:query:stock'.format(config.get('redis_cache_prefix'), wx_uid)
        redis_client = get_redis_client(config.get('redis_cache_db'))
        all_values = redis_client.lrange(store_key, 0, -1)
        all_values = [self.parse_redis_value(x.decode()) for x in all_values]
        if stock_code not in all_values:
            redis_client.lpush(store_key, json.dumps({
                'code': stock_code,
                'name': stock_name
            }))
            redis_client.close()

    @http.route(['/api/wechat/mini/stock/validate'], auth='public', methods=['POST'], csrf=False,
                type='json')
    def validate_stock(self):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code')
        if not stock_code:
            return self.response_json_error(-1, '请输入股票代码')
        try:
            res = request.env['finance.stock.basic'].sudo().search([
                '|',
                '|',
                '|',
                ('symbol', '=', stock_code),
                ('ts_code', '=', stock_code),
                ('cnspell', '=', stock_code),
                ('name', '=', stock_code),
            ])
            if not res:
                return self.response_json_error(404, '请求的股票代码 [{}] 无效!'.format(stock_code))
            return self.response_json_success({
                'code': stock_code,
                'data': [{
                    'name': x.name,
                    'code': x.symbol
                } for x in res]
            })
        except Exception as e:
            _logger.exception(e)
            return self.response_json_error(-1, str(e))

    @http.route(['/api/wechat/mini/sweep/list'], auth='public', methods=['GET', 'POST'], csrf=False,
                type='json')
    @verify_auth_token()
    def mine_sweep_list(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code', None)
        try:
            user_is_vip = self._check_user_is_vip(request.wxa_uid)

            res = request.env['stock.compare.analysis'].get_mine_list(vip_mode=user_is_vip)
            return self.response_json_success(res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))

    def get_peg_sign(self, peg_value):
        try:
            if 0 <= float(peg_value) < 1:
                return 'sun', decimal_float_number(peg_value)
            return 'danger', decimal_float_number(peg_value)
        except Exception as e:
            return 'danger', 0

    def get_plge_rat_sign(self, plge_rat_value):
        try:
            if float(plge_rat_value) > 0.1:
                return 'danger', decimal_float_number(plge_rat_value)
            return 'sun', decimal_float_number(plge_rat_value)
        except Exception as e:
            _logger.error('发生异常: {}'.format(e))
            return 'sun', 0

    def get_shr_redu_sign(self, stock_id):
        try:
            shr_redu_value = stock_id.shr_redu
            redu_tshr_rat = stock_id.redu_tshr_rat
            if redu_tshr_rat:
                msg = '{} 减持{}%'.format(stock_id.stat_datetime or '', redu_tshr_rat)
                return 'danger', msg
            return 'sun', decimal_float_number(shr_redu_value)
        except Exception as e:
            _logger.error('发生异常: {}'.format(e))
            return 'sun', 0

    def get_rls_tshr_rat_sign(self, stock_id):
        rls_tshr_rat = stock_id.rls_tshr_rat
        shr_type = stock_id.shr_type
        try:
            stock_json = json.loads(stock_id.restricted_json)
            nearest_unrestricted = stock_json.get('nearestUnrestricted')
            bgn_date = convert_timestamp_to_datetime(nearest_unrestricted.get('bgnDt'))
            display_msg = '{} {}'.format(bgn_date, '解禁{}%'.format(rls_tshr_rat) if rls_tshr_rat else shr_type)
            if not rls_tshr_rat or float(rls_tshr_rat) == 0:
                return 'sun', '暂无'
            return 'danger', display_msg
        except Exception as e:
            display_msg = rls_tshr_rat or shr_type
            return 'sun', display_msg or '暂无'

    def get_options_rslt_sign(self, options_rslt):
        try:
            if not options_rslt:
                return 'rain', '暂无'
            if options_rslt == '标准的无保留意见':
                return 'sun', options_rslt
            return 'danger', options_rslt
        except Exception as e:
            return 'rain', '暂无'

    def get_law_case_sign(self, law_case_value):
        try:
            if not law_case_value:
                return 'sun', 0
            if float(law_case_value) == 0:
                return 'danger', decimal_float_number(law_case_value)
            if 0 < float(law_case_value) <= 5:
                return 'rain', decimal_float_number(law_case_value)
            return 'danger', decimal_float_number(law_case_value)
        except Exception as e:
            return 'sun', 0

    def get_plge_shr_value(self, plge_shr_value):
        try:
            res = decimal_float_number(float(plge_shr_value) / 10000)
            return '{} 万股'.format(res)
        except Exception as e:
            return '暂无'

    def get_pred_typ_value(self, stock_id):
        try:
            net_prof_pco = stock_id.net_prof_pco
            if stock_id.pred_typ_name in ['预增', '略增']:
                return 'sun', stock_id.pred_typ_name
            if float(net_prof_pco) > 0:
                return 'sun', stock_id.pred_typ_name
            else:
                return 'danger', stock_id.pred_typ_name
        except Exception as e:
            return None, stock_id.pred_typ_name or '暂无'

    @http.route(['/v1/api/wechat/mini/sweep/value/free'], auth='public', methods=['GET', 'POST'], csrf=False,
                type='json')
    @verify_auth_token()
    def get_free_finance_stock_value(self):
        payload_data = json.loads(request.httprequest.data)

        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        stock_code = body.get('stock_code', None)

        stock_id = request.env['finance.stock.basic'].sudo().search([
            '|',
            '|',
            '|',
            ('symbol', '=', stock_code),
            ('ts_code', '=', stock_code),
            ('cnspell', '=', stock_code),
            ('name', '=', stock_code),
        ], limit=1)
        if not stock_id:
            result = {
            }
            return self.response_json_success(result)
        peg_sign, peg_result = self.get_peg_sign(stock_id.peg_car)
        plge_sign, plge_result = self.get_plge_rat_sign(stock_id.plge_rat)

        shr_red_sign, shr_redu_result = self.get_shr_redu_sign(stock_id)
        law_case_sign, law_case_result = self.get_law_case_sign(stock_id.law_case)
        restricted_sign, restricted_value = self.get_rls_tshr_rat_sign(stock_id)
        options_sign, options_result = self.get_options_rslt_sign(stock_id.options_rslt)

        pred_typ_sign, pred_typ_name = self.get_pred_typ_value(stock_id)

        free_content = [{
            'name': 'PEG（市盈率对比公司盈利增长速度）',
            'value': peg_result or '暂无',
            'sign': peg_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '股权质押',
            'value': '质押比例{}%'.format(plge_result) or '暂无',
            'sign': plge_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '股权冻结',
            'value': self.get_plge_shr_value(stock_id.plge_shr),
            'sign': None,
            'data': [],
            'chart': [],
        }, {
            'name': '限售解禁',
            'value': restricted_value or '暂无',
            'sign': restricted_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '股东减持',
            'value': shr_redu_result or '暂无',
            'sign': shr_red_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '业绩',
            'value': pred_typ_name,
            'sign': pred_typ_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '会计师审计',
            'value': options_result or '暂无',
            'sign': options_sign,
            'data': [],
            'chart': [],
        }, {
            'name': '商誉净资产占比',
            'value': '{}%'.format(stock_id.gw_netast_rat) if stock_id.gw_netast_rat else '暂无',
            'sign': 'rain',
            'data': [],
            'chart': [],
        }, {
            'name': '诉讼仲裁数量',
            'value': stock_id.law_case or 0,
            'sign': '',
            'data': [],
            'chart': [],
        }]
        data = {
            'stock_code': stock_id[0].symbol,
            'stock_name': stock_id[0].name,
            'data': free_content
        }

        self.save_query_to_redis(stock_id)
        return self.response_json_success(data)

    @http.route(['/api/wechat/mini/sweep/value/vip'], auth='public', methods=['POST'], csrf=False, type='json')
    def mine_sweep_value(self):
        payload_data = json.loads(request.httprequest.data)
        headers = payload_data.get('header')
        body = payload_data.get('body')
        token = headers.get('token', None)
        security_code = body.get('security_code', None)
        mine_uuid = body.get('uuid', None)
        if not all([security_code, mine_uuid]):
            return self.res_err(-1, str('请选择股票代码/UUID'))

        try:
            analysis_res = request.env['stock.compare.analysis'].query_mine_sweep_data(request.wxa_uid, mine_uuid,
                                                                                       security_code)

            return self.res_ok(analysis_res)
        except Exception as e:
            _logger.exception(e)
            return self.res_err(-1, str(e))
