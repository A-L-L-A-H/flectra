# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCommentary(models.Model):
    """Rantai tafsir, syarah, dan eksegesis bertingkat (Hermeneutic Stratigraphy)."""
    _name = 'moonwitness.sidra.commentary'
    _description = 'Sidra Exegetical Commentary'
    _rec_name = 'urn'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']
    _order = 'passage_id, layer, id'

    passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Commented Passage',
        required=True,
        ondelete='cascade',
        index=True
    )
    author = fields.Char(string='Commentator / Exegete', required=True,
                         help='e.g. Ibn Kathir, At-Tabari, Rashi, Sangharakshita, Origen, Shankara')
    school = fields.Char(string='Exegetical School / Orientation')
    commentary_type = fields.Selection([
        ('tafsir_matsur', 'Tafsir bi al-Ma\'tsur (Tradition-anchored)'),
        ('tafsir_ray', 'Tafsir bi ar-Ra\'y (Reason-anchored)'),
        ('peshat', 'Peshat (Literal / Historical-Grammatical)'),
        ('remez', 'Remez (Allegorical / Philosophical)'),
        ('derash', 'Derash (Midrashic / Homiletical)'),
        ('sod', 'Sod (Mystical / Kabbalistic / Sufic)'),
        ('patristic', 'Patristic / Historical Ecclesiastical Exegesis')
    ], string='Hermeneutic Method', default='tafsir_matsur', required=True, index=True)
    layer = fields.Integer(string='Hermeneutic Layer Depth', default=1,
                           help='1=Primary commentary on text; 2=Super-commentary (Hashiyah); 3=Gloss (Taliqah)')
    text = fields.Text(string='Commentary Text Payload', required=True)
    source_ref = fields.Char(string='Original Work Citation / Book Reference')
