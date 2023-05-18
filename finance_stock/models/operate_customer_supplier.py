# -*- coding: utf-8 -*-
from odoo import models, fields, api
import requests
from bs4 import BeautifulSoup
import json
import logging
_logger = logging.getLogger(__name__)


class OperateCustomerSupplier(models.Model):
    _name = 'operate.customer.supplier'
    _description = '主要客户及供应商'
    _sql_constraints = [
        ('unique_stock_id_name_report_date', 'unique(stock_id, name, report_date, type)', '股票代码和时间唯一')
    ]

    stock_id = fields.Many2one('finance.stock.basic', string='Stock', required=1)
    symbol = fields.Char('Stock', related='stock_id.symbol')
    type = fields.Char('类型')
    name = fields.Char('排名')
    value = fields.Float('销售额')
    report_date_char = fields.Char('Date')
    report_date = fields.Date('日期', required=1)
    rate = fields.Float('Rate', compute='_compute_operate_rate', store=True)
    sequence = fields.Integer(u'排序')

    @api.depends('name', 'value', 'report_date')
    def _compute_operate_rate(self):
        for operate_id in self:
            total_operate = self.env['operate.customer.supplier'].sudo().search([
                ('stock_id', '=', operate_id.stock_id.id),
                ('type', '=', operate_id.type)
            ])
            total_operate = total_operate.filtered(lambda o: o.report_date == operate_id.report_date)

            total_value = sum(x.value for x in total_operate)
            if total_value == 0:
                continue
            operate_id.rate = (operate_id.value / total_value) * 100

    def fetch_operate_cs_value(self, stock_id):
        operate_cs_ids = stock_id.operate_cs_ids
        _logger.info('主要客户及供应商, 开始获取: {}'.format(stock_id.symbol))
        url = 'http://basic.10jqka.com.cn/{}/operate.html'.format(stock_id.symbol)
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers)

        soup = BeautifulSoup(res.content, 'html.parser')
        provider_flash = soup.find('div', id='providerflash')
        try:
            provider_flash_value = json.loads(provider_flash.text)
        except Exception as e:
            _logger.error('出现了错误咯。。。{}'.format(e))
            return False

        data = []
        for provider_key in provider_flash_value.keys():
            provider_line = provider_flash_value.get(provider_key)
            report_date = provider_key
            if not provider_line:
                continue
            customer = provider_line.get('customer')
            supplier = provider_line.get('supplier')
            tmp = []
            if customer:
                for index_c, line_id in enumerate(customer):
                    tmp.append({
                        'stock_id': stock_id.id,
                        'name': line_id.get('name'),
                        'value': line_id.get('y'),
                        'type': 'customer',
                        'report_date_char': report_date,
                        'report_date': report_date,
                        'sequence': index_c
                    })
            if supplier:
                for index_s, line_id in enumerate(supplier):
                    tmp.append({
                        'stock_id': stock_id.id,
                        'name': line_id.get('name'),
                        'value': line_id.get('y'),
                        'type': 'supplier',
                        'report_date_char': report_date,
                        'report_date': report_date,
                        'sequence': index_s
                    })
            for line_data in tmp:
                # 筛选重复项
                if operate_cs_ids.filtered(
                        lambda o: o.type == line_data.get('type') and
                                  o.report_date_char == line_data.get('report_date_char') and
                                  o.name == line_data.get('name')):
                    continue
                data.append((0, 0, line_data))
        if data:
            _logger.info('主要客户及供应商, 开始保存: {}'.format(len(data)))
            stock_id.write({
                'operate_cs_ids': data
            })

    def cron_fetch_operate_cs_value(self):
        stock_ids = self.env['finance.stock.basic'].search([])
        for stock_id in stock_ids:
            self.with_delay().fetch_operate_cs_value(stock_id)
