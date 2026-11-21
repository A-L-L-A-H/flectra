# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraInstitution(models.Model):
    """Historical and religious institutions (Seminaries, Sanghas, Monasteries, Councils)."""
    _name = 'moonwitness.sidra.institution'
    _description = 'Sidra Religious & Scholarly Institution'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Institution Name', required=True, translate=True)
    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Tradition',
        required=True,
        ondelete='restrict',
        index=True
    )
    lineage_id = fields.Many2one(
        'moonwitness.sidra.lineage',
        string='Governing Lineage / School',
        ondelete='restrict',
        index=True
    )
    institution_type = fields.Selection([
        ('madrasa', 'Madrasa / Islamic Seminary'),
        ('monastery', 'Monastery / Vihara / Ashram'),
        ('church', 'Church / Diocese / Cathedral'),
        ('mosque', 'Mosque / Sanctuary'),
        ('temple', 'Temple / Mandir / Synagogue'),
        ('university', 'University / Academy of Sciences'),
        ('council', 'Ecumenical Council / Synod / Majelis')
    ], string='Institution Type', required=True, default='madrasa', index=True)
    founded_date = fields.Char(string='Founded Date / Era')
    location = fields.Char(string='Location / City')
    description = fields.Text(string='Historical Role & Custodianship')
