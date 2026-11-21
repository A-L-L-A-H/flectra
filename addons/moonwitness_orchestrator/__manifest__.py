# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness Orchestrator',
    'summary': 'Native workspace for connected services and messaging integrations',
    'description': """
Configuration and authenticated client for the MoonWitness service runtime.
Service endpoint and access token are stored in system parameters:
moonwitness_orchestrator.url and moonwitness_orchestrator.token.
Legacy parameter aliases remain supported for existing deployments.
    """,
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'MoonWitness',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup', 'moonwitness_base'],
    'data': [
        'security/orchestrator_security.xml',
        'data/ir_config_parameters.xml',
        'views/res_config_settings_views.xml',
        'views/whatsapp_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'moonwitness_orchestrator/static/src/whatsapp_dashboard.js',
            'moonwitness_orchestrator/static/src/**/*.xml',
        ],
    },
    'application': False,
    'auto_install': False,
    'installable': True,
}
