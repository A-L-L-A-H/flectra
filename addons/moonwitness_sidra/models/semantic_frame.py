# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraSemanticFrame(models.Model):
    """WSI Stage 5: Core semantic proposition / frame extracted from scriptural discourse."""
    _name = 'moonwitness.sidra.semantic.frame'
    _description = 'Sidra WSI Semantic Frame / Proposition'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]

    name = fields.Char(string='Frame Label', required=True, index=True)
    passage_id = fields.Many2one('moonwitness.sidra.passage', string='Source Passage', required=True, ondelete='cascade', index=True)
    source_binding_id = fields.Many2one('moonwitness.sidra.source.binding', string='Span Binding', ondelete='set null')
    frame_type = fields.Selection([
        ('command', 'Command / Prescription (Amr)'),
        ('prohibition', 'Prohibition (Nahy)'),
        ('declaration', 'Ontological / Theological Declaration (Khabar)'),
        ('promise', 'Promise / Glad Tidings (Wa\'d / Bisharah)'),
        ('warning', 'Warning / Admonition (Wa\'id / Indhar)'),
        ('narrative', 'Historical / Parable Event (Qasas)'),
        ('supplication', 'Supplication / Praise (Du\'a / Tasbih)'),
        ('question', 'Rhetorical / Dialogic Inquiry (Istifham)')
    ], string='Speech Act / Frame Type', required=True, default='declaration', index=True)
    polarity = fields.Selection([
        ('affirmative', 'Affirmative'), ('negative', 'Negative'), ('conditional', 'Conditional')
    ], string='Polarity', default='affirmative', required=True)
    modality = fields.Selection([
        ('certain', 'Certain / Categorical'), ('obligatory', 'Obligatory (Deontic)'),
        ('permissible', 'Permissible'), ('possible', 'Possible / Epistemic'), ('counterfactual', 'Counterfactual')
    ], string='Modality', default='certain')
    proposition_text = fields.Text(string='Normalized Proposition Summary', required=True)
    participant_ids = fields.One2many('moonwitness.sidra.discourse.participant', 'frame_id', string='Discourse Participants')
    witness_pattern_ids = fields.One2many('moonwitness.sidra.witness.pattern', 'frame_id', string='Derived Witness Patterns')


class SidraDiscourseParticipant(models.Model):
    """WSI Stage 4: Communicative & semantic role participants within a Frame."""
    _name = 'moonwitness.sidra.discourse.participant'
    _description = 'Sidra WSI Discourse Participant'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    frame_id = fields.Many2one('moonwitness.sidra.semantic.frame', string='Semantic Frame', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Participant Label', required=True)
    entity_urn = fields.Char(string='Linked Entity URN', index=True)
    semantic_role = fields.Selection([
        ('speaker', 'Speaker / Revealer (Mutakallim)'),
        ('addressee', 'Addressee (Mukhatab)'),
        ('agent', 'Agent / Actor (Fa\'il)'),
        ('patient', 'Patient / Object (Maf\'ul)'),
        ('beneficiary', 'Beneficiary'),
        ('witness', 'Witness (Shahid)'),
        ('instrument', 'Instrument / Medium'),
        ('location', 'Spatial / Cosmological Setting')
    ], string='Semantic Role', required=True, default='agent', index=True)


class SidraWitnessPattern(models.Model):
    """WSI Final Stages: Derived Witness Pattern & Positive Direction without altering source meaning."""
    _name = 'moonwitness.sidra.witness.pattern'
    _description = 'Sidra WSI Witness Pattern'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']

    frame_id = fields.Many2one('moonwitness.sidra.semantic.frame', string='Source Semantic Frame', required=True, ondelete='cascade', index=True)
    pattern_label = fields.Char(string='Witness Pattern Label', required=True, translate=True)
    positive_direction = fields.Text(string='Positive Direction / Constructive Guidance', required=True)
    review_state = fields.Selection([
        ('candidate', 'Candidate (Unreviewed)'),
        ('reviewed', 'Scholar Reviewed'),
        ('canonical', 'Approved Witness Pattern'),
        ('rejected', 'Rejected')
    ], string='Review State', default='candidate', required=True, index=True)
