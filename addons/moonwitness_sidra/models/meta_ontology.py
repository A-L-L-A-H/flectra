# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraMetaCategory(models.Model):
    """Layer -2: Upper ontology categories (BFO / DOLCE / OX-DX 7 Zones x 7 Levels)."""
    _name = 'moonwitness.sidra.meta.category'
    _description = 'Sidra Upper Ontology Meta-Category'
    _inherit = ['moonwitness.sidra.base']
    _order = 'oxdx_zone, oxdx_level, code'

    code = fields.Char(string='Category Code', required=True, index=True)
    name = fields.Char(string='Category Name', required=True, translate=True)
    upper_framework = fields.Selection([
        ('oxdx', 'OX-DX Universal Ontology (49 Levels)'),
        ('bfo', 'Basic Formal Ontology (BFO 2020)'),
        ('dolce', 'DOLCE Descriptive Ontology'),
        ('cidoc', 'CIDOC-CRM / LRMoo'),
    ], string='Upper Ontology Standard', required=True, default='oxdx')
    oxdx_zone = fields.Selection([
        ('1', 'Zone 1: Existence (L01-L07)'),
        ('2', 'Zone 2: Context (L08-L14)'),
        ('3', 'Zone 3: Intent (L15-L21)'),
        ('4', 'Zone 4: Structure (L22-L28)'),
        ('5', 'Zone 5: Semantic (L29-L35)'),
        ('6', 'Zone 6: Dynamic (L36-L42)'),
        ('7', 'Zone 7: Representation (L43-L49)'),
    ], string='OX-DX Zone')
    oxdx_level = fields.Integer(string='OX-DX Canonical Level (1-49)')
    parent_id = fields.Many2one('moonwitness.sidra.meta.category', string='Parent Category', ondelete='restrict')
    description = fields.Text(string='Formal Definition')


class SidraMetaScheme(models.Model):
    """Layer -2: External classification scheme registry (SKOS, Thompson, Quranic Ontology, UD v2)."""
    _name = 'moonwitness.sidra.meta.scheme'
    _description = 'Sidra External Classification Scheme'
    _inherit = ['moonwitness.sidra.base']

    code = fields.Char(string='Scheme Code', required=True, index=True)
    name = fields.Char(string='Scheme Title', required=True)
    namespace_uri = fields.Char(string='Namespace URI')
    version = fields.Char(string='Version')
    description = fields.Text(string='Scope & Mapping Notes')
