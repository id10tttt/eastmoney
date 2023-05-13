# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import json
import logging
import datetime
from itertools import tee
from odoo.exceptions import ValidationError
import uuid

_logger = logging.getLogger(__name__)


def itertools_pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    if a and b:
        return zip(a, b)


def verify_pairwise_increase(compare_list):
    state = []
    for s, t in itertools_pairwise(compare_list):
        try:
            if len(s) > 1:
                s = s[0]
                t = t[0]
        except Exception as e:
            s = s
            t = t
        if s is not None and t is not None:
            state.append(s <= t)
    return all(state)


def verify_pairwise_decrease(compare_list):
    state = []
    for s, t in itertools_pairwise(compare_list):
        try:
            if len(s) > 1:
                s = s[0]
                t = t[0]
        except Exception as e:
            s = s
            t = t
        if s is not None and t is not None:
            state.append(s > t)
    return all(state)


class StockCompareAnalysis(models.Model):
    _name = 'stock.compare.analysis'
    _description = '数据比较分析、定义雷'
    _sql_constraints = [
        ("name_uuid", "unique(uuid)", "uuid must be unique")
    ]

    name = fields.Char('名称', required=True)
    uuid = fields.Char(string="UUID", default=lambda self: self.get_default_uuid(), index=True, required=True)
    value_type = fields.Selection([
        ('value', u'取值'),
        ('vs', u'比较'),
        ('other', u'其它')
    ], string='取值类别', default='value')
    line_ids = fields.One2many('stock.compare.analysis.line', 'compare_id', string='明细行')

    type_id = fields.Many2one('finance.mine.type', string='类别')
    usage = fields.Selection([
        ('free', '免费使用'),
        ('vip', 'VIP专属')
    ], string='使用范围', default='free', required=True)
    stock_code = fields.Char('Stock code')

    def get_stock_id(self, stock_code):
        stock_id = self.env['finance.stock.basic'].search([
            ('symbol', '=', stock_code)
        ])
        return stock_id.id if stock_id else False

    def save_benchmark_data(self, security_code, all_result, all_benchmark_result, display_data, origin_data):
        benchmark_obj = self.env['compare.benchmark.data']
        benchmark_id = benchmark_obj.search([
            ('compare_id', '=', self.id),
            ('stock_code', '=', security_code)
        ])
        data = {
            'data': all_result,
            'benchmark_data': all_benchmark_result
        }
        try:
            result_data = json.dumps(data)
        except Exception as e:
            import traceback
            raise ValidationError('发生异常: {}, {}'.format(e, traceback.format_exc()))
        if not benchmark_id:
            benchmark_data = {
                'compare_id': self.id,
                'stock_code': security_code,
                'stock_id': self.get_stock_id(security_code),
                'value': result_data,
                'data': origin_data,
                'display_data': display_data
            }
            res = benchmark_obj.create(benchmark_data)
            _logger.info('创建记录: {}'.format(res))
        else:
            benchmark_id.write({
                'value': result_data,
                'data': origin_data,
                'display_data': display_data
            })
            _logger.info('更新记录: {}'.format(benchmark_id))

    def _get_benchmark_result(self, stock_id, compare_ids, benchmark_data_ids):
        for compare_id in compare_ids:
            if compare_id.value_type == 'value':
                compare_id._get_benchmark_result_value(stock_id.symbol)
            if compare_id.value_type == 'vs':
                compare_id._get_benchmark_result_vs(stock_id.symbol)
            else:
                continue

    def cron_get_benchmark_result(self):
        stock_ids = self.env['finance.stock.basic'].search([])
        compare_ids = self.env['stock.compare.analysis'].search([])
        for stock_id in stock_ids:
            benchmark_data_ids = self.env['compare.benchmark.data'].search([('stock_id', '=', stock_id.id)])
            self.with_delay()._get_benchmark_result(stock_id, compare_ids, benchmark_data_ids)

    def _get_benchmark_result_vs(self, security_code='000001'):
        self.ensure_one()
        all_result = []
        all_benchmark_result = []
        display_data = []
        origin_data = []
        if not self.line_ids:
            return False
        for compare_line in self.line_ids:
            sql_result, benchmark_result = compare_line.get_benchmark_result(security_code)
            all_result.append(sql_result)
            display_data += sql_result.get('display_data')
            origin_data += sql_result.get('data')
            all_benchmark_result.append(benchmark_result)
        if all_result and all_benchmark_result:
            self.save_benchmark_data(security_code, all_result, all_benchmark_result, display_data, origin_data)

    def _get_benchmark_result_value(self, security_code='000001'):
        self.ensure_one()
        all_result = []
        all_benchmark_result = []
        display_data = []
        origin_data = []
        if not self.line_ids:
            return False
        for compare_line in self.line_ids:
            sql_result, benchmark_result = compare_line.get_benchmark_result(security_code, value_type='value')
            all_result.append(sql_result)
            display_data += sql_result.get('display_data')
            origin_data += sql_result.get('data')
            all_benchmark_result.append(benchmark_result)
        if all_result and all_benchmark_result:
            self.save_benchmark_data(security_code, all_result, all_benchmark_result, display_data, origin_data)

    def get_benchmark_result_value(self, security_code='000001'):
        self.ensure_one()
        all_result = []
        all_benchmark_result = []
        if not self.line_ids:
            raise ValidationError('没有定义规则!')
        for compare_line in self.line_ids:
            sql_result, benchmark_result = compare_line.get_benchmark_result(security_code)
            all_result.append(sql_result)
            all_benchmark_result.append(benchmark_result)
        if all_result and all_benchmark_result:
            self.save_benchmark_data(security_code, all_result, all_benchmark_result)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': '{} 指标: {}'.format(self.stock_code or security_code, self.name),
                'message': '值: {},\n Benchmark结果: {}'.format(all_result, all_benchmark_result),
                'next': {
                    'type': 'ir.actions.act_window_close'
                },
            }
        }

    def get_benchmark_result_vs(self):
        pass

    def get_benchmark_result_other(self):
        pass

    def get_benchmark_result(self):
        stock_ids = self.env['finance.stock.basic'].search([], limit=50)
        if self.stock_code:
            stock_ids = stock_ids.filtered(lambda s: s.symbol == self.stock_code)
        compare_ids = self.env['stock.compare.analysis'].browse(self.ids)
        for stock_id in stock_ids:
            benchmark_data_ids = self.env['compare.benchmark.data'].search([('stock_id', '=', stock_id.id)])
            self._get_benchmark_result(stock_id, compare_ids, benchmark_data_ids)
            # self.with_delay()._get_benchmark_result(stock_id, compare_ids, benchmark_data_ids)

    def get_default_uuid(self):
        return str(uuid.uuid4())

    def get_mine_list(self, vip_mode=False):
        if vip_mode:
            filter_domain = []
        else:
            filter_domain = [('usage', '=', 'free')]
        return self.env['stock.compare.analysis'].search_read(domain=filter_domain, fields=['name', 'uuid'])

    def get_mine_value(self, security_code='000001'):
        self.ensure_one()
        result = getattr(self, '_query_mine_data_{}'.format(self.value_type))(security_code=security_code)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': '{} 指标: {}'.format(security_code, self.name),
                'message': result,
                'next': {
                    'type': 'ir.actions.act_window_close'
                },
            }
        }

    def _query_mine_data_vs(self, security_code='000001'):
        return self._query_mine_data_vs_value(security_code=security_code)

    def _query_mine_data_value(self, security_code='000001'):
        record_id = self.env[self.value_model_id.model].search([
            (self.value_field_name.name, '=', self.value_model_domain),
            ('security_code', '=', security_code)
        ])
        value = getattr(record_id, self.value_field_name.name)
        return {
            'security_code': security_code,
            'name': self.name,
            'value': value,
            'uuid': self.uuid,
            'msg': 'success'
        }

    def _query_mine_data_other(self, security_code='000001'):
        return {
            'security_code': security_code,
            'name': '',
            'left_value': '',
            'right_value': '',
            'left_field_name': '',
            'right_field_name': '',
            'uuid': '',
            'msg': '没有找到这个指标/权限错误!!'
        }

    def _query_mine_data_vs_value(self, security_code='000001'):
        self.ensure_one()
        left_record = self.env[self.left_model_id.model].search([
            (self.left_filter_field.name, '=', self.left_domain),
            ('security_code', '=', security_code)
        ])
        right_record = self.env[self.right_model_id.model].search([
            (self.right_filter_field.name, '=', self.right_domain),
            ('security_code', '=', security_code)
        ])
        left_value = ''
        right_value = ''
        if hasattr(left_record, self.left_field_name.name):
            left_value = getattr(left_record, self.left_field_name.name)
        if hasattr(right_record, self.right_field_name.name):
            right_value = getattr(right_record, self.right_field_name.name)
        return {
            'security_code': security_code,
            'name': self.name,
            'left_value': left_value,
            'right_value': right_value,
            'left_field_name': self.left_field_name.name,
            'right_field_name': self.right_field_name.name,
            'uuid': self.uuid,
            'msg': 'success'
        }

    def return_error_msg(self, security_code, mine_uuid):
        return {
            'security_code': security_code,
            'name': '',
            'left_value': '',
            'right_value': '',
            'left_field_name': '',
            'right_field_name': '',
            'uuid': mine_uuid,
            'msg': '没有找到这个指标/权限错误!!'
        }

    def query_mine_sweep_data(self, wechat_user, mine_uuid, security_code):
        if_allow = self.env['wx.subscribe.order'].if_allow_view_mine_sweep(wechat_user, mine_uuid)
        if not if_allow:
            return self.return_error_msg(security_code, mine_uuid)
        record_id = self.env['stock.compare.analysis'].search([
            ('uuid', '=', mine_uuid)
        ])
        if not record_id or len(record_id) > 1:
            return self.return_error_msg(security_code, mine_uuid)
        try:
            return getattr(record_id, '_query_mine_data_{}'.format(record_id.value_type))(security_code=security_code)
        except Exception as e:
            return self.return_error_msg(security_code, mine_uuid)

    def unlink(self):
        all_benchmark_data = self.env['compare.benchmark.data'].sudo().search([
            ('compare_id', 'in', self.ids)
        ])
        all_benchmark_data.with_delay().unlink()
        return super().unlink()

    def manual_update_all_stock_matrix(self):
        stock_ids = self.env['finance.stock.basic'].search([])
        compare_id = self
        for stock_id in stock_ids:
            benchmark_data_ids = self.env['compare.benchmark.data'].search([('stock_id', '=', stock_id.id)])
            self.with_delay()._get_benchmark_result(stock_id, compare_id, benchmark_data_ids)


class StockCompareLine(models.Model):
    _inherit = 'finance.stock.mixin'
    _name = 'stock.compare.analysis.line'
    _description = '明细行'

    compare_id = fields.Many2one('stock.compare.analysis', string='Compare')
    source_data = fields.Text('Data Source', required=True)
    source_args = fields.Text('Args Source')
    display_data = fields.Text('显示值')
    render_template = fields.Text('显示模板')
    use_latest_period = fields.Integer('最近多少期间？', default=12)
    period_detail = fields.Char('期间明细', compute='_compute_period_detail')
    benchmark_line_ids = fields.One2many('stock.compare.benchmark.line', 'compare_line_id', string='Benchmark 明细')

    def get_default_period(self, default_year=5, all_period=False):
        search_today = datetime.date.today()
        search_month = search_today.month
        search_day = search_today.day
        search_year = search_today.year
        search_year = int(search_year)
        search_month = int(search_month)
        search_period = []
        for x in range(search_year - default_year, search_year):
            search_period += [f'{x}-03-31 00:00:00', f'{x}-06-30 00:00:00', f'{x}-09-30 00:00:00',
                              f'{x}-12-31 00:00:00']
        if all_period:
            search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                              f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        else:
            if 4 <= search_month < 6:
                search_period += [f'{search_year}-03-31 00:00:00']
            elif 7 <= search_month < 9:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00']
            elif 10 <= search_month < 12:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00']
            elif search_day == 31 and search_month == 12:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        return search_period

    @api.depends('use_latest_period')
    def _compute_period_detail(self):
        for line_id in self:
            default_period = self.get_default_period()[::-1]
            period_detail = '\',\''.join("{}".format(x) for x in default_period[:line_id.use_latest_period])
            line_id.period_detail = '\'{}\''.format(period_detail)

    def fetch_metric_select_sql_result_vs(self, security_code):
        select_sql = self.get_metric_parsed_sql(security_code)
        try:
            self.env.cr.execute(select_sql)
        except Exception as e:
            raise ValidationError('错误: {}'.format(e))
        res = self.env.cr.fetchall()
        result = {
            'compare_id': self.id,
            'data': res,
            'sql': select_sql,
            'source_data': self.source_data,
            'source_args': self.source_args,
            'period_detail': self.period_detail,
        }
        return result

    def fetch_metric_select_sql_result_value(self, security_code):
        select_sql = self.get_metric_parsed_sql(security_code)
        try:
            self.env.cr.execute(select_sql)
        except Exception as e:
            raise ValidationError('错误: {}'.format(e))
        res = self.env.cr.dictfetchall()
        result = {
            'compare_id': self.id,
            'data': res,
            'sql': select_sql,
            'source_data': self.source_data,
            'source_args': self.source_args,
            'period_detail': self.period_detail,
        }
        return result

    def fetch_display_metric_select_sql_result_value(self, security_code):
        if self.display_data:
            select_sql = self.get_metric_parsed_sql(security_code, usage='display')
            try:
                self.env.cr.execute(select_sql)
            except Exception as e:
                raise ValidationError('错误: {}'.format(e))
            res = self.env.cr.dictfetchall()
            res = self.render_display_data(res)
            return res
        return []

    def render_display_data(self, result):
        return_res = []
        for line_data in result:
            if self.render_template:
                try:
                    display_data = self.render_template.format(**line_data)
                except Exception as e:
                    display_data = ''
            else:
                display_data = ''
            line_data['display_data'] = display_data
            return_res.append(line_data)
        return return_res

    def get_metric_parsed_sql(self, security_code, usage='vs'):
        return self._get_metric_parsed_sql(security_code, usage=usage)

    def _get_metric_parsed_sql(self, security_code, usage='vs'):
        source_data = self._get_metric_source_data(usage=usage)
        source_args = self._get_metric_source_args(security_code, source_data)
        if self.use_latest_period > 0:
            if '{report_date}' in source_data:
                if 'report_date' not in source_args.keys():
                    source_args.update({
                        'report_date': self.period_detail
                    })
        try:
            select_sql = source_data.format(**source_args)
        except Exception as e:
            _logger.error('错误 {}'.format(e))
            raise ValidationError('Params error!')
        return select_sql

    def _get_metric_source_data(self, usage='vs'):
        if usage == 'vs':
            source_data = self.source_data
        else:
            source_data = self.display_data
        return source_data

    def _get_metric_source_args(self, security_code, source_data):
        try:
            source_args = self.source_args
            source_args = json.loads(source_args)
            if 'security_code' not in source_args.keys():
                if '{security_code}' in source_data:
                    source_args.update({
                        'security_code': security_code
                    })
            return source_args
        except Exception as e:
            raise ValidationError('出现错误: {}'.format(e))

    def verify_benchmark_result_sign_vs(self, compare_result):
        sql_result = compare_result.get('data')
        benchmark_result = []
        for line_id in self.benchmark_line_ids:
            if line_id.inequality_operator == '>':
                benchmark_data = [x[0] > line_id.benchmark_left for x in sql_result if x[0] is not None]
            elif line_id.inequality_operator == '<':
                benchmark_data = [x[0] < line_id.benchmark_left for x in sql_result if x[0] is not None]
            elif line_id.inequality_operator == '=':
                benchmark_data = [x[0] == line_id.benchmark_left for x in sql_result if x[0] is not None]
            elif line_id.inequality_operator == '>=':
                benchmark_data = [x[0] >= line_id.benchmark_left for x in sql_result if x[0] is not None]
            elif line_id.inequality_operator == '<=':
                benchmark_data = [x[0] <= line_id.benchmark_left for x in sql_result if x[0] is not None]
            elif line_id.inequality_operator == 'between':
                benchmark_data = [line_id.benchmark_left < x[0] < line_id.benchmark_right for x in sql_result if
                                  x[0] is not None]
            elif line_id.inequality_operator == 'increase':
                benchmark_data = verify_pairwise_increase([x[0] for x in sql_result if x[0] is not None])
            elif line_id.inequality_operator == 'decrease':
                benchmark_data = verify_pairwise_decrease([x[0] for x in sql_result if x[0] is not None])
            else:
                benchmark_data = None
            benchmark_result.append({
                'sign': line_id.sign,
                'benchmark_line': line_id.id,
                'data': benchmark_data
            })
        return benchmark_result

    def verify_benchmark_result_sign_value(self, compare_result):
        sql_result = compare_result.get('data')
        benchmark_result = []
        for line_id in self.benchmark_line_ids:
            if line_id.inequality_operator == '>':
                benchmark_data = [x.get('value') > line_id.benchmark_left for x in sql_result if
                                  x.get('value') is not None]
            elif line_id.inequality_operator == '<':
                benchmark_data = [x.get('value') < line_id.benchmark_left for x in sql_result if
                                  x.get('value') is not None]
            elif line_id.inequality_operator == '=':
                benchmark_data = [x.get('value') == line_id.benchmark_left for x in sql_result if
                                  x.get('value') is not None]
            elif line_id.inequality_operator == '>=':
                benchmark_data = [x.get('value') >= line_id.benchmark_left for x in sql_result if
                                  x.get('value') is not None]
            elif line_id.inequality_operator == '<=':
                benchmark_data = [x.get('value') <= line_id.benchmark_left for x in sql_result if
                                  x.get('value') is not None]
            elif line_id.inequality_operator == 'between':
                benchmark_data = [
                    line_id.benchmark_left < x.get('value') < line_id.benchmark_right for x in sql_result if
                    x.get('value') is not None]
            elif line_id.inequality_operator == 'increase':
                benchmark_data = verify_pairwise_increase(
                    [x.get('value') for x in sql_result if x.get('value') is not None])
            elif line_id.inequality_operator == 'decrease':
                benchmark_data = verify_pairwise_decrease(
                    [x.get('value') for x in sql_result if x.get('value') is not None])
            else:
                benchmark_data = None
            benchmark_result.append({
                'sign': line_id.sign,
                'benchmark_line': line_id.id,
                'data': benchmark_data
            })
        return benchmark_result

    def get_benchmark_result(self, security_code='000001', value_type='vs'):
        sql_result = getattr(self, 'fetch_metric_select_sql_result_{}'.format(value_type))(
            security_code=security_code)
        display_data = self.fetch_display_metric_select_sql_result_value(security_code)
        sql_result.update({
            'display_data': display_data
        })
        benchmark_result = getattr(self, 'verify_benchmark_result_sign_{}'.format(value_type))(sql_result)
        return sql_result, benchmark_result


class CompareBenchmarkLine(models.Model):
    _name = 'stock.compare.benchmark.line'
    _description = 'Benchmark'

    compare_line_id = fields.Many2one('stock.compare.analysis.line')
    inequality_operator = fields.Selection([
        ('>', '大于'),
        ('<', '小于'),
        ('=', '等于'),
        ('>=', '大于等于'),
        ('<=', '小于等于'),
        ('between', '介于'),
        ('increase', '递增'),
        ('decrease', '递减'),
    ], string='比较', required=True)
    benchmark_right = fields.Float('Benchmark')
    benchmark_left = fields.Float('Benchmark')
    sign = fields.Selection([
        ('sun', '阳'),
        ('rain', '阴'),
        ('danger', '雷')
    ], string='Sign')
