# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraPrimitive(models.Model):
    """Foundational metaphysical categories (Being, Consciousness, Will, Knowledge, Power, Life, Speech, Ineffable)."""
    _name = 'moonwitness.sidra.primitive'
    _description = 'Sidra Metaphysical Primitive'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    code = fields.Char(string='Primitive Code', required=True, index=True)
    name = fields.Char(string='Primitive Name', required=True, translate=True)
    definition = fields.Text(string='Formal Definition')
    apophatic_note = fields.Text(string='Apophatic Negation (Via Negativa)')
    kataphatic_note = fields.Text(string='Kataphatic Affirmation (Via Positiva)')
