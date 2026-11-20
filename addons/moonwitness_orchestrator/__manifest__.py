# -*- coding: utf-8 -*-
{
    'name': 'Moonwitness Orchestrator',
    'summary': 'Flectra client for the Fastify services orchestrator (WhatsApp and future JS-only services)',
    'description': "HTTP client for the moonwitness-orchestrator (Fastify) container. URL/token stored in ir.config_parameter: moonwitness_arsy.orchestrator_url / moonwitness_arsy.orchestrator_token.",
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'Moonwitness',
    'license': 'LGPL-3',
    'depends': ['base', 'moonwitness_base', 'moonwitness_arsy'],
    'data': [
        'data/ir_config_parameters.xml',
        'views/whatsapp_dashboard_views.xml',
        'views/whatsapp_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'moonwitness_orchestrator/static/src/whatsapp_dashboard.js',
        ],
    },
    'application': False,
    'auto_install': False,
    'installable': True,
}
