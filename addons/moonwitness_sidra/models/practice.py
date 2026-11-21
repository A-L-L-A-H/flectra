# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraPractice(models.Model):
    """Sacred practices, rituals, prayers, fasts, and liturgies prescribed by scripture."""
    _name = 'moonwitness.sidra.practice'
    _description = 'Sidra Sacred Practice & Ritual'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Practice Name', required=True, translate=True)
    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Tradition',
        required=True,
        ondelete='restrict',
        index=True
    )
    lineage_id = fields.Many2one(
        'moonwitness.sidra.lineage',
        string='Lineage / School',
        ondelete='restrict',
        index=True
    )
    practice_type = fields.Selection([
        ('ritual', 'Prescribed Ritual (Ibadah)'),
        ('observance', 'Moral Observance (Sila)'),
        ('prayer', 'Canonical Prayer (Salah / Liturgy)'),
        ('fast', 'Sacred Fasting (Sawm / Vrata)'),
        ('pilgrimage', 'Pilgrimage (Hajj / Yatra / Ziyarah)'),
        ('meditation', 'Meditation / Contemplation (Zikr / Dhyana)'),
        ('chant', 'Sacred Recitation & Chant (Tilawah / Kirtan)')
    ], string='Practice Type', required=True, default='ritual', index=True)
    frequency = fields.Selection([
        ('daily', 'Daily (5 Times / Matins / Sandhya)'),
        ('weekly', 'Weekly (Jumuah / Sabbath / Sunday Liturgy)'),
        ('monthly', 'Monthly / Lunar'),
        ('annual', 'Annual / Seasonal (Ramadan / Easter / Vesak)'),
        ('lifecycle', 'Life-Cycle (Birth, Initiation, Marriage, Funeral)'),
        ('occasional', 'Occasional / Voluntary (Nafilah / Vow)')
    ], string='Frequency & Rhythm', default='daily', required=True)
    description = fields.Text(string='Ritual Form, Requirements & Spiritual Objective')
