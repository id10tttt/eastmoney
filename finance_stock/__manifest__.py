{
    'name': 'Finance Stock Analyse',
    'summary': 'Finance Stock Analyse',
    'category': 'Tools',
    'author': '1di0t',
    'license': 'LGPL-3',
    'installable': True,
    'depends': ['base'],
    'external_dependencies': {
        'python': ['tushare'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/finance_stock.xml',
        'views/stock_main_data.xml',
        'views/stock_zcfzb.xml',
        'views/stock_report.xml',
        'views/stock_business.xml',
        'views/stock_analyse.xml',
        'views/finance_settings.xml',
        'views/finance_settings.xml',
    ],
}
