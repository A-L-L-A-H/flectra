# -*- coding: utf-8 -*-
{
    'name': 'Moonwitness Arsy',
    'summary': 'Docker Manager panel inside Flectra: status, actions, logs, databases, backups',
    'description': """
Manage the Docker Compose stack (flectra app, db, backups) from the Flectra UI.
Talks to a hardened host agent over HTTP with a shared-secret token.
No Docker socket is mounted into the Flectra container.
    """,
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'Moonwitness',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/moonwitness_arsy_security.xml',
        'security/ir.model.access.csv',
        'views/moonwitness_arsy_views.xml',
        'views/moonwitness_arsy_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
}
