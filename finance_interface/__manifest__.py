{
    'name': 'Finance Interface',
    'summary': 'Finance Interface',
    'category': 'Tools',
    'author': '1di0t',
    'license': 'LGPL-3',
    'installable': True,
    'depends': ['base', 'queue_job', 'crm', 'sale', 'finance_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/crm_team.xml',
        'data/payment_seq.xml',
        'data/wx_config.xml',
        # 'data/wx_payment_data.xml',
        'views/menu.xml',
        'views/wx_config_view.xml',
        'views/wx_user_view.xml',
        'views/wx_payment_view.xml',
        'views/wx_subscribe_view.xml',

        'wizards/wx_confirm_view.xml',
    ],
}
