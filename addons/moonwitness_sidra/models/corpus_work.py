# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCorpusWork(models.Model):
    """FRBR Work: Abstract intellectual and sacred creation (e.g. Quran, Tipitaka, Gospel of John)."""
    _name = 'moonwitness.sidra.work'
    _description = 'Sidra Corpus Work (FRBR Work)'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]
    _order = 'name'

    name = fields.Char(string='Canonical Title', required=True, translate=True)
    title_multilang = fields.Text(string='Multilingual Titles (JSON preferred/alternate labels)')
    kind = fields.Selection([
        ('scripture', 'Sacred Scripture'),
        ('hadith', 'Hadith Compendium'),
        ('sutra', 'Sutra / Discourse'),
        ('gospel', 'Gospel'),
        ('commentary', 'Exegesis / Commentary'),
        ('creed', 'Creed / Doctrinal Statement'),
        ('liturgy', 'Liturgy / Sacred Prayer'),
        ('law', 'Sacred Law / Jurisprudence'),
        ('poetry', 'Sacred Poetry / Hymn'),
        ('philosophical', 'Philosophical Treatise')
    ], string='Genre / Work Type', required=True, index=True)
    tradition_id = fields.Many2one(
        'moonwitness.sidra.tradition',
        string='Tradition',
        required=True,
        ondelete='restrict',
        index=True
    )
    description = fields.Text(string='Work Overview & History')
    date_composed = fields.Char(string='Composition Era / Date', help='e.g. 610-632 CE, c. 5th century BCE')
    language_original = fields.Char(string='Original Language (ISO 639-3)', size=3, index=True)

    expression_ids = fields.One2many('moonwitness.sidra.expression', 'work_id', string='Expressions')
    expression_count = fields.Integer(string='Expression Count', compute='_compute_expression_count')

    def _compute_expression_count(self):
        for rec in self:
            rec.expression_count = len(rec.expression_ids)
