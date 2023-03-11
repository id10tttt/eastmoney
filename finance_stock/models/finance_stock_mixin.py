# -*- coding: utf-8 -*-
from odoo import models
import datetime


class FinanceStockMixin(models.AbstractModel):
    _name = 'finance.stock.mixin'
    _description = 'mixin'

    def get_default_period(self, default_year=5, all_period=False):
        search_today = datetime.date.today()
        search_month = search_today.month
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

    def get_default_period_date(self, default_year=5, all_period=False):
        """
        获取两年的所有期间
        """
        search_today = datetime.date.today()
        search_month = search_today.month
        search_year = search_today.year
        search_year = int(search_year)
        search_month = int(search_month)
        search_period = []
        for x in range(search_year - default_year, search_year):
            search_period += [f'{x}-03-31', f'{x}-06-30', f'{x}-09-30',
                              f'{x}-12-31']
        if all_period:
            search_period += [f'{search_year}-03-31', f'{search_year}-06-30',
                              f'{search_year}-09-30', f'{search_year}-12-31']
        else:
            if search_month < 3:
                search_period += [f'{search_year}-03-31']
            elif 3 <= search_month < 6:
                search_period += [f'{search_year}-03-31']
            elif 6 <= search_month < 9:
                search_period += [f'{search_year}-03-31', f'{search_year}-06-30']
            elif 9 <= search_month < 12:
                search_period += [f'{search_year}-03-31', f'{search_year}-06-30',
                                  f'{search_year}-09-30']
            else:
                search_period += [f'{search_year}-03-31', f'{search_year}-06-30',
                                  f'{search_year}-09-30', f'{search_year}-12-31']
        return search_period
