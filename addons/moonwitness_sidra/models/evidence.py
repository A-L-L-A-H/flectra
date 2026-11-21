# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraEvidence(models.Model):
    """Anchors an Assertion to a specific scriptural Passage with a verified semantic relation."""
    _name = 'moonwitness.sidra.evidence'
    _description = 'Sidra Scriptural Evidence Anchor'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    _order = 'assertion_id, passage_id'

    assertion_id = fields.Many2one(
        'moonwitness.sidra.assertion',
        string='Target Assertion',
        required=True,
        ondelete='cascade',
        index=True
    )
    passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Evidence Passage',
        required=True,
        ondelete='restrict',
        index=True
    )
    relation = fields.Selection([
        ('supports', 'Supports Proposition (Yashhadu lahu)'),
        ('contradicts', 'Contradicts Proposition (Yukhalifuhu)'),
        ('mentions', 'Mentions Subject/Object Directly'),
        ('quotes', 'Directly Quotes Text (Iqtibas)'),
        ('paraphrases', 'Paraphrases Meaning'),
        ('interprets', 'Interprets or Explains Passage (Tafsir)'),
        ('contextualizes', 'Provides Historical Context (Sabab an-Nuzul)'),
        ('parallels', 'Parallels Another Tradition Passage'),
        ('alludes_to', 'Alludes To / Typological Echo (Isharah)')
    ], string='Evidence Relation', required=True, default='supports', index=True)

    excerpt = fields.Text(string='Passage Excerpt')
    char_start = fields.Integer(string='Character Offset Start')
    char_end = fields.Integer(string='Character Offset End')
    note = fields.Text(string='Scholarly Exegetical Annotation')
