# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraSourceBinding(models.Model):
    """Binds an analysis or entity to specific external source spans and revisions (WSI Stage 1)."""
    _name = 'moonwitness.sidra.source.binding'
    _description = 'Sidra Source Span Binding'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    source_urn = fields.Char(string='Target Source URN', required=True, index=True,
                             help='Reference to external or internal canonical resource URN')
    git_revision = fields.Char(string='Pinned Git Commit SHA', index=True,
                               help='Exact pinned commit SHA in source repository')
    char_start = fields.Integer(string='Character Offset Start')
    char_end = fields.Integer(string='Character Offset End')
    token_start = fields.Integer(string='Token Start Index')
    token_end = fields.Integer(string='Token End Index')
    selector_json = fields.Text(string='Advanced Text Selector (JSON XPath/Offset)')
