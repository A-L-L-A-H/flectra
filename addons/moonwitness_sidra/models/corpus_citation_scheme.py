# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCitationScheme(models.Model):
    """Canonical citation scheme definition (e.g. CTS URN, surah:ayah, chapter:verse)."""
    _name = 'moonwitness.sidra.citation.scheme'
    _description = 'Sidra Citation Scheme'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Scheme Name', required=True, help='e.g. quran:surah-ayah, bible:chapter-verse')
    delimiter = fields.Char(string='Citation Delimiter', default=':', required=True)
    components_json = fields.Text(string='Components Specification (JSON array of keys & units)')
    example = fields.Char(string='Citation Example', default='2:255')
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', string='Primary Tradition', ondelete='restrict')
