# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness Orchestrator',
    'summary': 'Flectra client for the Fastify services orchestrator (WhatsApp and future JS-only services)',
    'description': "HTTP client for the moonwitness-orchestrator (Fastify) container. URL/token stored in ir.config_parameter: moonwitness_orchestrator.url / moonwitness_orchestrator.token (with fallback to moonwitness_arsy.orchestrator_url / moonwitness_arsy.orchestrator_token).",
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
