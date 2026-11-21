# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraEpistemicStatus(models.Model):
    """Scoped epistemic attestation and truth classification per tradition/community."""
    _name = 'moonwitness.sidra.epistemic.status'
    _description = 'Sidra Epistemic Status'
    _rec_name = 'urn'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    status = fields.Selection([
        ('attested', 'Attested (Direct Canonical Attestation)'),
        ('inferred', 'Inferred (Scholarly or Algorithmic Proposition)'),
        ('reconstructed', 'Reconstructed (Historical / Textual Critical Reconstruction)'),
        ('contested', 'Contested (Disputed across Traditions or Lineages)'),
        ('rejected', 'Rejected (Excluded / Apocryphal / Syadz)'),
        ('unknown', 'Unknown (Insufficient Evidence to Classify)')
    ], string='Epistemic Category', required=True, default='attested', index=True)

    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Governing Tradition Scope',
        ondelete='restrict',
        index=True,
        help='Tradition within which this epistemic status is normative'
    )
    lineage_scope = fields.Char(
        string='Lineage / Community Boundary',
        help='Sub-tradition boundary (e.g. Sunni, Catholic, Theravada, Mahayana)'
    )
    assessor_id = fields.Many2one(
        'moonwitness.sidra.assessor',
        string='Assessor / Authority',
        ondelete='restrict',
        index=True
    )
    confidence = fields.Float(
        string='Confidence Metric (0.00 - 1.00)',
        default=1.0,
        digits=(4, 3)
    )
    method = fields.Char(string='Assessment Methodology', default='canonical-attestation')
    assessed_at = fields.Datetime(string='Assessment Timestamp', default=fields.Datetime.now, required=True)
    notes = fields.Text(string='Epistemic Context Notes')
