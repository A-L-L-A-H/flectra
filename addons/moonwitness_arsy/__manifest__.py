# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness ARSY',
    'summary': 'Native operations console for containers, logs, databases, and backups',
    'description': """
Operate the MoonWitness runtime through the ARSY operations workspace.
Communicates with the isolated host agent over authenticated HTTP.
The application container never receives direct access to the Docker socket.
    """,
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'MoonWitness',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup', 'moonwitness_base'],
    'data': [
        'security/moonwitness_arsy_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameters.xml',
        'views/moonwitness_arsy_views.xml',
        'views/moonwitness_arsy_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
}
