# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraDivinity(models.Model):
    """Layer 1: Divinity entity with explicit Kataphatic (affirmative) and Apophatic (via negativa) attributes."""
    _name = 'moonwitness.sidra.divinity'
    _description = 'Sidra Divinity & Ultimate Reality Entity'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]

    name = fields.Char(string='Sacred Name', required=True, translate=True, index=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', string='Governing Tradition Scope', required=True, ondelete='restrict', index=True)
    epithets = fields.Text(string='Divine Epithets / Names (e.g. Asmaul Husna, JSON/lines)')
    kataphatic_attributes = fields.Text(string='Kataphatic Attributes (Via Positiva — Affirmed by Tradition)')
    apophatic_attributes = fields.Text(string='Apophatic Attributes (Via Negativa / Tanzih — Explicitly Denied)')
    primitive_ids = fields.Many2many(
        'moonwitness.sidra.primitive',
        'sidra_divinity_primitive_rel',
        'divinity_id',
        'primitive_id',
        string='Participated Metaphysical Primitives'
    )
    consciousness_mode_ids = fields.One2many('moonwitness.sidra.consciousness.mode', 'divinity_id', string='Revelation & Consciousness Modes')
    manifestation_ids = fields.One2many('moonwitness.sidra.manifestation', 'divinity_id', string='Manifestations / Theophanies')


class SidraConsciousnessMode(models.Model):
    """Layer 1: Mode through which the transcendent addresses human consciousness (Wahy, Ilham, Samadhi, Gnosis)."""
    _name = 'moonwitness.sidra.consciousness.mode'
    _description = 'Sidra Consciousness & Revelation Mode'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Mode Name', required=True, help='e.g. Wahy, Ilham, Ru\'ya, Samadhi, Prophecy, Gnosis')
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    divinity_id = fields.Many2one('moonwitness.sidra.divinity', ondelete='set null')
    description = fields.Text(string='Phenomenological & Epistemic Description')


class SidraManifestation(models.Model):
    """Layer 1: Mode of divine disclosure in space-time (Logos, Theophany, Avatar, Ruh)."""
    _name = 'moonwitness.sidra.manifestation'
    _description = 'Sidra Divine Manifestation / Theophany'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Manifestation Name', required=True)
    divinity_id = fields.Many2one('moonwitness.sidra.divinity', required=True, ondelete='cascade', index=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    form_description = fields.Text(string='Description of Disclosure')
    passage_ids = fields.Many2many('moonwitness.sidra.passage', 'sidra_manifestation_passage_rel', 'manifestation_id', 'passage_id', string='Attesting Passages')
