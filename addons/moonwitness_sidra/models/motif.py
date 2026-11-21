# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraMotif(models.Model):
    """Indeks motif naratif sakral dan cerita rakyat peradaban dunia (Thompson / ATU Motif Index)."""
    _name = 'moonwitness.sidra.motif'
    _description = 'Sidra Narrative & Theological Motif'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    _order = 'code, name'

    code = fields.Char(string='Motif Identifier Code', required=True, index=True,
                       help='e.g. A1010 (Deluge / Great Flood), F111 (Journey to Heavenly Realm)')
    name = fields.Char(string='Motif Title', required=True, translate=True)
    motif_index = fields.Selection([
        ('thompson', 'Stith Thompson Motif-Index of Folk-Literature'),
        ('atu', 'Aarne-Thompson-Uther (ATU) Type Index'),
        ('custom', 'MoonWitness Multi-Tradition Sacred Motif Index')
    ], string='Classification Scheme', default='custom', required=True)
    parent_id = fields.Many2one('moonwitness.sidra.motif', string='Parent Motif Category', ondelete='restrict')
    child_ids = fields.One2many('moonwitness.sidra.motif', 'parent_id', string='Sub-motifs')
    description = fields.Text(string='Motif Narrative & Theological Definition')
    passage_ids = fields.Many2many(
        'moonwitness.sidra.passage',
        'sidra_motif_passage_rel',
        'motif_id',
        'passage_id',
        string='Instantiating Passages'
    )
