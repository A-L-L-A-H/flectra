# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraAlignment(models.Model):
    """Penyelarasan ayat paralel lintas tradisi (Cross-Tradition Scriptural Alignment)."""
    _name = 'moonwitness.sidra.alignment'
    _description = 'Sidra Cross-Tradition Passage Alignment'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin'
    ]
    _order = 'strength desc, id'

    source_passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Source Passage',
        required=True,
        ondelete='restrict',
        index=True
    )
    target_passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Target Aligned Passage',
        required=True,
        ondelete='restrict',
        index=True
    )
    source_tradition_id = fields.Many2one(
        related='source_passage_id.edition_id.expression_id.work_id.tradition_id',
        string='Source Tradition',
        store=True,
        index=True
    )
    target_tradition_id = fields.Many2one(
        related='target_passage_id.edition_id.expression_id.work_id.tradition_id',
        string='Target Tradition',
        store=True,
        index=True
    )
    alignment_type = fields.Selection([
        ('parallel', 'Thematic / Conceptual Parallel'),
        ('quotation', 'Direct Quotation (Iqtibas / Citation)'),
        ('allusion', 'Typological Echo / Allusion'),
        ('thematic', 'Shared Archetype or Legal Motif'),
        ('structural', 'Shared Literary / Hymnic Structure')
    ], string='Alignment Category', required=True, default='parallel', index=True)
    strength = fields.Float(
        string='Alignment Strength Metric (0.00 - 1.00)',
        default=0.85,
        digits=(4, 3),
        required=True,
        help='Confidence score: values >= 0.70 indicate strong cross-tradition resonance.'
    )
    method = fields.Selection([
        ('manual', 'Scholarly Consensus / Peer-Reviewed'),
        ('auto_embed', 'Dense Vector Cosine Similarity (pgvector)'),
        ('auto_lexical', 'Root & Lemma Overlap'),
        ('auto_motif', 'Shared Narrative Motif Index')
    ], string='Discovery Method', default='manual', required=True)
    notes = fields.Text(string='Comparative Hermeneutic Analysis & Context')

    _sql_constraints = [
        ('distinct_passages', 'CHECK(source_passage_id != target_passage_id)',
         'Source and Target passages in an alignment must be distinct.')
    ]
