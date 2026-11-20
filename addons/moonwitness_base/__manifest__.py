# -*- coding: utf-8 -*-
{
    'name': 'Moonwitness Base',
    'summary': 'Base infrastructure shared by moonwitness addons',
    'description': "Shared abstract models, security groups, and access rules used by moonwitness_arsy and other moonwitness modules.",
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'Moonwitness',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/moonwitness_base_security.xml',
        'views/moonwitness_base_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
}
