# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCanon(models.Model):
    """Scoped scriptural canon defined by a specific tradition or lineage."""
    _name = 'moonwitness.sidra.canon'
    _description = 'Sidra Scriptural Canon'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Canon Name', required=True, help='e.g. Sunni Hadith Canon, Pali Tipitaka, Catholic Bible')
    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Tradition',
        required=True,
        ondelete='restrict',
        index=True
    )
    lineage_id = fields.Many2one(
        'moonwitness.sidra.lineage',
        string='Lineage / Council Boundary',
        ondelete='restrict',
        index=True
    )
    scope = fields.Selection([
        ('scripture', 'Sacred Scripture'),
        ('law', 'Sacred Law / Halakha / Fiqh'),
        ('liturgy', 'Liturgy / Hymnody'),
        ('commentary', 'Authoritative Commentary / Exegesis')
    ], string='Canon Domain Scope', required=True, default='scripture', index=True)
    authority_level = fields.Selection([
        ('binding', 'Binding / Infallible Authority'),
        ('authoritative', 'Authoritative Standard'),
        ('influential', 'Influential Reference'),
        ('disputed', 'Disputed Status')
    ], string='Authority Level', required=True, default='binding', index=True)
    attestation_date = fields.Char(string='Historical Attestation Era')
    description = fields.Text(string='Canonicity Criteria & History')

    canon_work_ids = fields.One2many('moonwitness.sidra.canon.work', 'canon_id', string='Canon Memberships')


class SidraCanonWork(models.Model):
    """Relates a Work to a Canon with its specific scoped authority status."""
    _name = 'moonwitness.sidra.canon.work'
    _description = 'Sidra Canon Work Membership'
    _order = 'canon_id, work_id'

    canon_id = fields.Many2one('moonwitness.sidra.canon', required=True, ondelete='cascade', index=True)
    work_id = fields.Many2one('moonwitness.sidra.work', required=True, ondelete='restrict', index=True)
    status = fields.Selection([
        ('canonical', 'Canonical / Primary Canon'),
        ('deuterocanonical', 'Deuterocanonical / Secondary'),
        ('disputed', 'Disputed (Antilegomena)'),
        ('apocryphal', 'Apocryphal / Outside Canon'),
        ('rejected', 'Rejected / Excluded / Syadz')
    ], string='Canonicity Status', required=True, default='canonical', index=True)
    authority_note = fields.Text(string='Authority & Historical Notes')

    _sql_constraints = [
        ('canon_work_unique', 'UNIQUE(canon_id, work_id)', 'A work can only be declared once per canon.')
    ]
