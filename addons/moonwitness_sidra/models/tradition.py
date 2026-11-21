# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraTradition(models.Model):
    """Represents one of the 54 world religious, spiritual, or philosophical traditions."""
    _name = 'moonwitness.sidra.tradition'
    _description = 'Sidra World Tradition'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    code = fields.Char(string='Canonical Code', required=True, index=True,
                       help='Unique slug identifying the tradition, e.g. islam, christianity, buddhism')
    name = fields.Char(string='Tradition Name', required=True, translate=True)
    native_name = fields.Char(string='Native Script Name')
    tradition_type = fields.Selection([
        ('major_world_religion', 'Major World Religion'),
        ('indigenous_tradition', 'Indigenous Tradition'),
        ('historical_reconstruction', 'Historical Reconstruction'),
        ('philosophical_school', 'Philosophical School'),
        ('new_religious_movement', 'New Religious Movement')
    ], string='Tradition Type', required=True, default='major_world_religion')
    historical_status = fields.Selection([
        ('living', 'Living Tradition'),
        ('historical', 'Historical Tradition')
    ], string='Historical Status', default='living', required=True)
    geographic_origin = fields.Char(string='Geographic Scope / Origin')
    textuality = fields.Selection([
        ('written_canon', 'Written Canon'),
        ('oral_corpus', 'Oral Corpus'),
        ('mixed', 'Mixed Written & Oral')
    ], string='Textuality Mode', default='written_canon')
    description = fields.Text(string='Description')
    primary_languages = fields.Char(string='Primary Language Codes (ISO 639-3)')
    aliases = fields.Char(string='Aliases (Comma-separated)')
    work_count = fields.Integer(string='Registered Works', compute='_compute_work_count')

    def _compute_work_count(self):
        for rec in self:
            rec.work_count = self.env['moonwitness.sidra.work'].search_count([('tradition_id', '=', rec.id)])
