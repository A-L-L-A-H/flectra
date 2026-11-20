# -*- coding: utf-8 -*-
{
    'name': 'Moonwitness Base',
    'summary': 'Base infrastructure shared by moonwitness addons',
    'description': """\nShared abstract models, security groups, and access rules used by moonwitness_arsy and other moonwitness modules.\n""",
    'version': '1.0.0.0.0',
    'category': 'Administration',
    'author': 'Moonwitness',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/moonwitness_base_security.xml',
        'security/ir.model.access.csv',
    ],
    'application': False,
    'auto_install': False,
    'installable': True,
}
