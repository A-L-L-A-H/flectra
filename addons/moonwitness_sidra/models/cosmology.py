# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraUniverse(models.Model):
    """Layer 2: Cosmological framework of reality according to a tradition."""
    _name = 'moonwitness.sidra.universe'
    _description = 'Sidra Cosmological Universe Model'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Cosmology Name', required=True, translate=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    description = fields.Text(string='Cosmological Architecture Overview')
    structure_json = fields.Text(string='Structured Cosmology Graph (JSON)')
    realm_ids = fields.One2many('moonwitness.sidra.realm', 'universe_id', string='Realms & Dimensions')


class SidraRealm(models.Model):
    """Layer 2: Distinct spiritual or material realm within a cosmological model."""
    _name = 'moonwitness.sidra.realm'
    _description = 'Sidra Cosmological Realm'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Realm Name', required=True, translate=True, help='e.g. Jannah, Barzakh, Arsy, Triloka, Pure Land')
    universe_id = fields.Many2one('moonwitness.sidra.universe', required=True, ondelete='cascade', index=True)
    realm_type = fields.Selection([
        ('transcendent', 'Transcendent Throne / Beyond Space (Arsy / Pleroma)'),
        ('heaven', 'Heavenly / Celestial Realm (Jannah / Devaloka)'),
        ('earth', 'Terrestrial World (Dunya / Bhuloka)'),
        ('intermediate', 'Intermediate / Liminal State (Barzakh / Bardo)'),
        ('underworld', 'Infernal / Purgatorial Realm (Jahannam / Naraka)'),
        ('pure_land', 'Pure Land / Awakened Field')
    ], string='Realm Category', required=True, default='heaven', index=True)
    description = fields.Text(string='Realm Description & Attributes')


class SidraEpoch(models.Model):
    """Layer 2: Cosmic era, prophetic dispensation, or historical cycle."""
    _name = 'moonwitness.sidra.epoch'
    _description = 'Sidra Cosmic & Historical Epoch'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    _order = 'tradition_id, sequence, id'

    name = fields.Char(string='Epoch Name', required=True, translate=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    sequence = fields.Integer(string='Chronological Sequence', default=1)
    start_marker = fields.Char(string='Start Event / Date')
    end_marker = fields.Char(string='End Event / Date')
    description = fields.Text(string='Epoch Characteristics')


class SidraGazetteer(models.Model):
    """Layer 2: Sacred geography gazetteer linked to Pleiades coordinates."""
    _name = 'moonwitness.sidra.gazetteer'
    _description = 'Sidra Sacred Geography Gazetteer (Pleiades)'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Place Name', required=True, translate=True, index=True)
    ancient_names = fields.Char(string='Historical / Ancient Names (e.g. Bakkah, Urusalim)')
    pleiades_uri = fields.Char(string='Pleiades Gazetteer URI')
    latitude = fields.Float(string='Latitude', digits=(9, 6))
    longitude = fields.Float(string='Longitude', digits=(9, 6))
    tradition_ids = fields.Many2many('moonwitness.sidra.tradition', 'sidra_gazetteer_tradition_rel', 'place_id', 'tradition_id', string='Associated Traditions')
    description = fields.Text(string='Sacred Significance')
