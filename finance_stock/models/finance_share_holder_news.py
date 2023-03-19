# -*- coding: utf-8 -*-
import json
from odoo import models, fields
import requests
from .finance_stock import headers
import logging

_logger = logging.getLogger(__name__)


class FinanceStockBonus(models.Model):
    _name = 'finance.stock.share.holder.news'
    _description = '高管持股变动'
    _sql_constraints = [
        ('unique_secucode_change_date_person_name', 'unique(secucode, change_date, person_name)',
         '股票代码唯一')
    ]

    _req_url = 'https://emweb.securities.eastmoney.com/PC_HSF10/CompanyBigNews/PageAjax'

    stock_id = fields.Many2one('finance.stock.basic', string='Stock')
    secucode = fields.Char('secucode')
    security_code = fields.Char('SECURITY CODE')
    change_date = fields.Char('日期')
    person_name = fields.Char('变动人')
    change_shares = fields.Char('变动数量(股)')
    change_after_holdnum = fields.Char('结存股票(股)')
    average_price = fields.Char('交易均价(元)')
    position_name = fields.Char('董监高管')
    position_des_relation = fields.Char('与高管关系')
    change_reason = fields.Char('股份变动途径')
    origin_json = fields.Text('Origin json')

    def get_security_code(self, code):
        if code.startswith('6') or code.startswith('5') or code.startswith('9'):
            prefix_code = 'SH'
            sec_id = '1'
        else:
            prefix_code = 'SZ'
            sec_id = '0'
        return prefix_code + code, sec_id + '.' + code

    def cron_fetch_share_holder_news(self):
        stock_ids = self.env['finance.stock.basic'].search([])
        for stock_id in stock_ids:
            self.with_delay().get_share_holder_news(stock_id)

    def get_share_holder_news(self, stock_ids):
        all_data = []
        for stock_id in stock_ids:
            share_news_ids = self.env['finance.stock.share.holder.news'].search([
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

            ggcgbd_data = result.get('ggcgbd')

            for ggcgbd_line in ggcgbd_data:
                if share_news_ids.filtered(lambda b: b.change_date == ggcgbd_line.get('CHANGE_DATE')):
                    continue

                data = {
                    'secucode': stock_id.ts_code,
                    'security_code': stock_id.symbol,
                    'stock_id': stock_id.id,
                    'change_date': ggcgbd_line.get('CHANGE_DATE'),
                    'person_name': ggcgbd_line.get('PERSON_NAME'),
                    'change_shares': ggcgbd_line.get('CHANGE_SHARES'),
                    'change_after_holdnum': ggcgbd_line.get('CHANGE_AFTER_HOLDNUM'),
                    'average_price': ggcgbd_line.get('AVERAGE_PRICE'),
                    'position_name': ggcgbd_line.get('POSITION_NAME'),
                    'position_des_relation': ggcgbd_line.get('PERSON_DSE_RELATION'),
                    'change_reason': ggcgbd_line.get('CHANGE_REASON'),
                    'origin_json': json.dumps(ggcgbd_line)
                }

                all_data.append(data)
        if all_data:
            res = self.env['finance.stock.share.holder.news'].create(all_data)
            _logger.info('创建高管持股变动: {}'.format(res))
