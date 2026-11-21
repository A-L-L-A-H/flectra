# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraPredicate(models.Model):
    """Controlled vocabulary of semantic predicates connecting entities and assertions."""
    _name = 'moonwitness.sidra.predicate'
    _description = 'Sidra Semantic Predicate'
    _rec_name = 'label'
    _inherit = ['moonwitness.sidra.base']

    label = fields.Char(string='Predicate Label', required=True, help='e.g. mentions, has-role, part-of')
    inverse_label = fields.Char(string='Inverse Predicate Label')
    description = fields.Text(string='Formal Semantics Definition')


class SidraAssertion(models.Model):
    """Scoped doctrinal or scholarly proposition anchored in evidence (WSI Proposition)."""
    _name = 'moonwitness.sidra.assertion'
    _description = 'Sidra Scoped Assertion'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]
    _order = 'tradition_id, assertion_class, id'

    assertion_class = fields.Selection([
        ('explicit_source', 'Explicit Source Fact (Haqiqah)'),
        ('source_summary', 'Source Summary / Synthesis'),
        ('scholarly_interpretation', 'Scholarly Interpretation (Tawil)'),
        ('derived', 'Derived / Inferred Proposition (Istintaj)'),
        ('hypothesis', 'Scholarly Hypothesis (Nazariyyah)')
    ], string='Assertion Class', required=True, default='explicit_source', index=True)

    statement = fields.Text(string='Assertion Proposition Statement', required=True)
    subject_urn = fields.Char(string='Subject URN', required=True, index=True)
    predicate_id = fields.Many2one('moonwitness.sidra.predicate', string='Predicate', ondelete='restrict')
    object_urn = fields.Char(string='Object URN / Value', required=True, index=True)

    # Scoping constraint: NO global theological assertions allowed (RGBL Rule 4)
    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Mandatory Scoped Tradition',
        required=True,
        ondelete='restrict',
        index=True,
        help='The tradition within which this assertion holds truth-value.'
    )
    lineage_id = fields.Many2one(
        'moonwitness.sidra.lineage',
        string='Lineage / School Scope',
        ondelete='restrict',
        index=True
    )
    evidence_ids = fields.One2many('moonwitness.sidra.evidence', 'assertion_id', string='Evidence Links')
    evidence_count = fields.Integer(string='Evidence Count', compute='_compute_evidence_count')

    def _compute_evidence_count(self):
        for rec in self:
            rec.evidence_count = len(rec.evidence_ids)
