# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness Base',
    'summary': 'Base infrastructure shared by MoonWitness addons',
    'description': "Shared abstract models, security groups, and access rules used by moonwitness_arsy and other MoonWitness modules.",
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'MoonWitness',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'moonwitness_base/static/src/scss/brand.scss',
        ],
    },
    'data': [
        'security/moonwitness_base_security.xml',
        'views/moonwitness_base_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
}
