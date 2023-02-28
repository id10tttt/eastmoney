{
    'name': 'Finance Interface',
    'summary': 'Finance Interface',
    'category': 'Tools',
    'author': '1di0t',
    'license': 'LGPL-3',
    'installable': True,
    'depends': ['base', 'queue_job', 'finance_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_seq.xml',
        'views/menu.xml',
        'views/wxa_user_view.xml',
        'views/wxa_payment_view.xml',
        'views/wxa_subscribe_view.xml',
    ],
}
