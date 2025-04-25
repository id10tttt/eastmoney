# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


def get_10jqka_company_manager_info(stock_code):
    url = f'http://basic.10jqka.com.cn/{stock_code}/company.html'

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    }
    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.content, 'html.parser')

    ml_003 = soup.find_all('div', id='ml_003')
    manage_list = ml_003[0].find_all('table', class_='m_table managelist m_hl')

    manage_all = manage_list[0].find_all('tbody')

    tr_list = manage_all[0].find_all('tr')
    manager_info = []

    def parse_tr_value(tc, tc_name):
        tmp = {}
        try:
            tc_name_soup = BeautifulSoup(tc_name[0], 'html.parser')
        except Exception as e:
            tc_name_soup = tc_name[0]
        tc_name_a1 = tc_name_soup.find_all('a', class_='turnto clientJump')
        tc_name_title1 = tc_name_soup.find_all('td', class_='jobs')
        tc_name_td1 = tc_name_soup.find_all('span', class_='directnum hold')

        if not tc_name_a1:
            return {}

        tc_name_value = tc_name_a1[0].text
        tc_name_url = tc_name_a1[0].get('jumpurl')
        tmp.update({
            'tc': tc,
            'tc_name': tc_name_value,
            'tc_url': tc_name_url,
            'title': tc_name_title1[0].text.replace('\n', '').replace(' ', ''),
            'direct_shr': tc_name_td1[0].text
        })
        return tmp

    for tr_line in tr_list:
        tc1 = tr_line.select('th:nth-child(1)')
        if tc1:
            tc1 = tc1[0].text
        tc_name_1 = tr_line.select('td:nth-child(2)')
        if not tc_name_1:
            continue

        try:
            tmp1 = parse_tr_value(tc1, tc_name_1)
        except Exception as e:
            continue
        td_2 = tr_line.select('td:nth-child(5) > div > span')
        if td_2:
            td2 = td_2[0].text
            tmp1.update({
                'shr': td2
            })
        if tmp1:
            manager_info.append(tmp1)
        tc2 = tr_line.select('th:nth-child(6)')
        if tc2:
            tc2 = tc2[0].text
        tc_name_2 = tr_line.select('td:nth-child(7)')
        if not tc_name_2:
            continue

        try:
            tmp2 = parse_tr_value(tc2, tc_name_2)
        except Exception as e:
            continue
        td_4 = tr_line.select('td:nth-child(10) > div > span')
        if td_4:
            td4 = td_4[0].text
            tmp2.update({
                'shr': td4
            })
        if tmp2:
            manager_info.append(tmp2)
    return manager_info


if __name__ == '__main__':
    stock_code = '002603'
    get_10jqka_company_manager_info(stock_code)
