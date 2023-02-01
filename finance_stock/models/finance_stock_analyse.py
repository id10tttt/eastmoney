# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime


class FinanceStockAnalyse(models.Model):
    _name = 'finance.stock.analyse'
    _description = '数据分析'
    _sql_constraints = [
        ('unique_secucode_report_date', 'unique(secucode, report_date)', '股票代码和时间唯一')
    ]
    _rec_name = 'secucode'

    report_date = fields.Char('REPORT_DATE', index=True)
    secucode = fields.Char('SECUCODE', index=True)
    security_code = fields.Char('SECURITY_CODE')

    stock_id = fields.Many2one('finance.stock.basic', string='股票')
    survey_id = fields.Many2one('finance.stock.company', string='公司信息')
    main_id = fields.Many2one('finance.stock.main.data', string='主要指标')
    business_id = fields.Many2one('finance.stock.business', string='主营构成')
    lrb_id = fields.Many2one('finance.stock.lrb', string='利润表')
    zcfzb_id = fields.Many2one('finance.stock.zcfzb', string='资产负债表')
    report_id = fields.Many2one('finance.stock.report', string='业绩报表')

    xsjll = fields.Char('净利率', related='main_id.xsjll', store=True)
    xsmll = fields.Char('毛利率', related='main_id.xsmll', store=True)
    values = fields.Char('市值', related='stock_id.f116', store=True)
    total_value = fields.Char('总市值', related='stock_id.f277', store=True)
    f84 = fields.Char('总股本', related='stock_id.f84', store=True)
    f85 = fields.Char('流通股', related='stock_id.f85', store=True)
    total_operate_rece = fields.Char('营业总收入', related='main_id.totaloperatereve', store=True)
    trade_ratio = fields.Char('市销率', compute='_compute_trade_ratio', store=True)
    roe_jq = fields.Char('净资产收益率', related='main_id.roejq', store=True)
    zcfzl = fields.Char('资产负债率', related='main_id.zcfzl', store=True)
    mbi_ratio = fields.Char('国际销售占比', related='business_id.mbi_ratio', store=True)
    total_current_liab = fields.Char('流动负债合计', related='zcfzb_id.total_current_liab', store=True)
    total_equity = fields.Char('股东权益合计', related='zcfzb_id.total_equity', store=True)
    interest_expense = fields.Char('利息费用', related='lrb_id.interest_expense', store=True)
    continued_netprofit = fields.Char('净利润', related='lrb_id.continued_netprofit', store=True)
    basic_eps = fields.Char('每股收益率', related='report_id.basic_eps', store=True)
    emp_num = fields.Char('雇员', related='survey_id.emp_num', store=True)
    chzzl = fields.Char('库存周转率', related='main_id.chzzl', store=True)
    peg_car = fields.Char('PEG', related='stock_id.peg_car', store=True)
    pb_mrq = fields.Char('市净率', related='stock_id.pb_mrq', store=True)
    pcf_ocf_tim = fields.Char('市现率', related='stock_id.pcf_ocf_tim', store=True)
    industry_csrc = fields.Char('所属行业', related='survey_id.industry_csrc', store=True)
    hypm = fields.Char('行业排名', related='stock_id.hypm', store=True)

    @api.depends('total_value', 'total_operate_rece')
    def _compute_trade_ratio(self):
        for line_id in self:
            total_value = line_id.stock_id.f277
            total_operate_rece = line_id.main_id.totaloperatereve
            try:
                trade_ratio = float(total_value) / float(total_operate_rece)
            except Exception as e:
                trade_ratio = 0
            line_id.trade_ratio = trade_ratio

    def get_default_period(self, all_period=False):
        search_today = datetime.date.today()
        search_month = search_today.month
        search_year = search_today.year
        search_year = int(search_year)
        search_month = int(search_month)
        search_period = []
        for x in range(search_year - 2, search_year):
            search_period += [f'{x}-03-31 00:00:00', f'{x}-06-30 00:00:00', f'{x}-09-30 00:00:00',
                              f'{x}-12-31 00:00:00']
        if all_period:
            search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                              f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        else:
            if search_month < 3:
                search_period += [f'{search_year}-03-31 00:00:00']
            elif 3 <= search_month < 6:
                search_period += [f'{search_year}-03-31 00:00:00']
            elif 6 <= search_month < 9:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00']
            elif 9 <= search_month < 12:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00']
            else:
                search_period += [f'{search_year}-03-31 00:00:00', f'{search_year}-06-30 00:00:00',
                                  f'{search_year}-09-30 00:00:00', f'{search_year}-12-31 00:00:00']
        return search_period

    def cron_fetch_analyse_report(self):
        all_period = self.get_default_period()
        all_period = all_period[:-4]
        all_analyse_ids = self.env['finance.stock.analyse'].search([])
        all_stock_ids = self.env['finance.stock.basic'].search([('id', 'not in', all_analyse_ids.stock_id.ids)],
                                                               limit=50)
        self.generate_analyse_report(stock_ids=all_stock_ids, report_date=all_period)

    def generate_analyse_report(self, stock_ids=None, report_date=None):
        if report_date:
            all_period = report_date
        else:
            all_period = self.get_default_period()
        if stock_ids:
            all_stock_ids = stock_ids
        else:
            all_stock_ids = self.env['finance.stock.basic'].search([])
        survey_ids = self.env['finance.stock.company'].search([])
        main_ids = self.env['finance.stock.main.data'].search([])
        business_ids = self.env['finance.stock.business'].search([])
        lrb_ids = self.env['finance.stock.lrb'].search([])
        zcfzb_ids = self.env['finance.stock.zcfzb'].search([])
        report_ids = self.env['finance.stock.report'].search([])
        analyse_ids = self.env['finance.stock.analyse'].search([])
        all_data = []
        for stock_id in all_stock_ids:
            for period_date in all_period:
                if analyse_ids.filtered(lambda x: x.secucode == stock_id.ts_code and x.report_date == period_date):
                    continue
                survey_id = survey_ids.filtered(lambda x: x.ts_code == stock_id.ts_code)
                main_id = main_ids.filtered(lambda x: x.secucode == stock_id.ts_code and x.report_date == period_date)
                business_id = business_ids.filtered(
                    lambda x: x.secucode == stock_id.ts_code and
                              x.report_date == period_date and
                              x.mainop_type == 3 and
                              x.rank == 2)
                lrb_id = lrb_ids.filtered(lambda x: x.secucode == stock_id.ts_code and x.report_date == period_date)
                zcfzb_id = zcfzb_ids.filtered(lambda x: x.secucode == stock_id.ts_code and x.report_date == period_date)
                report_id = report_ids.filtered(
                    lambda x: x.secucode == stock_id.ts_code and x.reportdate == period_date)
                # total_value = stock_id.f277
                # total_operate_rece = main_id.totaloperatereve
                # try:
                #     trade_ratio = float(total_value) / float(total_operate_rece)
                # except Exception as e:
                #     trade_ratio = 0
                tmp_data = {
                    'secucode': stock_id.ts_code,
                    'security_code': stock_id.symbol,
                    'report_date': period_date,
                    'stock_id': stock_id.id,
                    'survey_id': survey_id.id,
                    'main_id': main_id.id,
                    'business_id': business_id.id,
                    'lrb_id': lrb_id.id,
                    'zcfzb_id': zcfzb_id.id,
                    'report_id': report_id.id,
                    # 'xsjll': main_id.xsjll,
                    # 'xsmll': main_id.xsmll,
                    # 'values': stock_id.f116,
                    # 'total_value': total_value,
                    # 'f84': stock_id.f84,
                    # 'f85': stock_id.f85,
                    # 'total_operate_rece': total_operate_rece,
                    # 'trade_ratio': trade_ratio,
                    # 'roe_jq': main_id.roejq,
                    # 'zcfzl': main_id.zcfzl,
                    # 'mbi_ratio': business_id.mbi_ratio,
                    # 'total_equity': zcfzb_id.total_equity,
                    # 'total_current_liab': zcfzb_id.total_current_liab,
                    # 'basic_eps': report_id.basic_eps,
                    # 'interest_expense': lrb_id.interest_expense,
                    # 'continued_netprofit': lrb_id.continued_netprofit,
                    # 'emp_num': survey_id.emp_num,
                    # 'chzzl': main_id.chzzl,
                    # 'peg_car': stock_id.peg_car,
                    # 'pb_mrq': stock_id.pb_mrq,
                    # 'pcf_ocf_tim': stock_id.pcf_ocf_tim,
                    # 'industry_csrc': survey_id.industry_csrc,
                    # 'hypm': stock_id.hypm
                }
                all_data.append(tmp_data)
        if all_data:
            self.create(all_data)
