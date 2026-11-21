# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness Corpus',
    'version': '3.0.1.0.0',
    'category': 'Productivity/Knowledge',
    'summary': 'Read-only search and catalog access to the MoonWitness Corpus API',
    'description': """
MoonWitness Corpus is a provenance-first, multi-tradition text corpus.

This connector lets Flectra users browse synchronized work and tradition
metadata and run read-only searches against a configured MoonWitness Corpus
REST API. Canonical corpus content stays in MoonWitness; this addon does not
import, edit, score, or republish source text.
    """,
    'author': 'A-L-L-A-H',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/corpus_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
