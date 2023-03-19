# -*- coding: utf-8 -*-
import json
from odoo import models, fields
import requests
from .finance_stock import headers
import logging

_logger = logging.getLogger(__name__)


class FinanceStockBonus(models.Model):
    _name = 'finance.stock.bonus'
    _description = '分红'
    _sql_constraints = [
        ('unique_secucode_notice_date_impl_plan_profile', 'unique(secucode, notice_date, impl_plan_profile)',
         '股票代码唯一')
    ]

    _req_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/BonusFinancing/PageAjax'

    stock_id = fields.Many2one('finance.stock.basic', string='Stock')
    assign_progress = fields.Char('方案进度')
    secucode = fields.Char('secucode')
    security_code = fields.Char('SECURITY CODE')
    security_name_abbr = fields.Char('SECURITY ABBR')
    impl_plan_profile = fields.Char('分红方案', help='IMPL_PLAN_PROFILE')
    notice_date = fields.Char('公告日期')
    pay_cash_date = fields.Char('派息日')
    equity_record_date = fields.Char('股权登记日')
    ex_dividend_date = fields.Char('除权除息日', help='EX_DIVIDEND_DATE')
    origin_json = fields.Text('Origin json')

    def get_security_code(self, code):
        if code.startswith('6') or code.startswith('5') or code.startswith('9'):
            prefix_code = 'SH'
            sec_id = '1'
        else:
            prefix_code = 'SZ'
            sec_id = '0'
        return prefix_code + code, sec_id + '.' + code

    def cron_fetch_bonus_data(self):
        stock_ids = self.env['finance.stock.basic'].search([])
        for stock_id in stock_ids:
            self.with_delay().get_bonus_data(stock_id)

    def get_bonus_data(self, stock_ids):
        all_data = []
        for stock_id in stock_ids:
            bonus_id = self.env['finance.stock.bonus'].search([
                ('stock_id', '=', stock_id.id)
            ])
            security_code, sec_id = self.get_security_code(stock_id.symbol)
            payload_data = {
                'code': security_code
            }
            res = requests.get(self._req_url, params=payload_data, headers=headers)

            try:
                result = res.json()
            except Exception as e:
                _logger.error('获取数据出错: {}, {}'.format(e, res.text))
                continue

            fhyx_data = result.get('fhyx')

            for fhyx_line in fhyx_data:
                if bonus_id.filtered(lambda b: b.notice_date == fhyx_line.get('NOTICE_DATE')):
                    continue

                data = {
                    'secucode': stock_id.ts_code,
                    'security_code': stock_id.symbol,
                    'stock_id': stock_id.id,
                    'assign_progress': fhyx_line.get('ASSIGN_PROGRESS'),
                    'security_name_abbr': fhyx_line.get('SECURITY_NAME_ABBR'),
                    'impl_plan_profile': fhyx_line.get('IMPL_PLAN_PROFILE'),
                    'notice_date': fhyx_line.get('NOTICE_DATE'),
                    'pay_cash_date': fhyx_line.get('PAY_CASH_DATE'),
                    'equity_record_date': fhyx_line.get('EQUITY_RECORD_DATE'),
                    'ex_dividend_date': fhyx_line.get('EX_DIVIDEND_DATE'),
                    'origin_json': json.dumps(fhyx_line)
                }

                all_data.append(data)
        if all_data:
            res = self.env['finance.stock.bonus'].create(all_data)
            _logger.info('创建分红记录: {}'.format(res))
