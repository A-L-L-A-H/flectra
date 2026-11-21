# -*- coding: utf-8 -*-
{
    'name': 'MoonWitness Sidra',
    'summary': 'Provenance-first multi-tradition sacred text corpus & knowledge center (49-Level Universal Ontology)',
    'description': """
MoonWitness Sidra Knowledge Center
===================================
A provenance-first multi-tradition sacred literature corpus and knowledge center.
Harmonizes:
- 7 Zones x 7 Levels = 49 Canonical Levels (OX-DX)
- 14-Stage Semantic Pipeline (WSI)
- Arabic-first Epistemic Semantics (AQEL: Haqiqah, Qaidah, Istintaj, Tahaqquq, Isyrah)
- 5-Fold Epistemic Classification (Master-Docs: Shahada, Riwayah, Dirasah, Tawil, Khayal)
- FRBR / LRMoo Sacred Text Hierarchy (Work -> Expression -> Edition -> Passage -> Content)
- 54 Multi-Tradition Datasets (RGBL v0.1)
- Multilingual PostgreSQL Full-Text Search (FTS) with Semitic Diacritic Normalization
- GraphRAG Hybrid Retrieval and Hallucination Auditing
    """,
    'version': '3.0.1.0.0',
    'category': 'Administration',
    'author': 'MoonWitness',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup', 'moonwitness_base'],
    'data': [
        'security/sidra_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameters.xml',
        'data/sidra_traditions_seed.xml',
        'data/sidra_primitives_seed.xml',
        'wizard/corpus_import_wizard_views.xml',
        'views/corpus_views.xml',
        'views/sidra_menus.xml',
    ],
    'application': True,
    'auto_install': False,
    'installable': True,
}
