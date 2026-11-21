# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCorpusExpression(models.Model):
    """FRBR Expression: Specific realization of a Work in a given language, script, and version."""
    _name = 'moonwitness.sidra.expression'
    _description = 'Sidra Corpus Expression (FRBR Expression)'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]
    _order = 'work_id, language, content_type'

    name = fields.Char(string='Expression Title', required=True)
    work_id = fields.Many2one(
        'moonwitness.sidra.work',
        string='Parent Work',
        required=True,
        ondelete='restrict',
        index=True
    )
    language = fields.Char(string='Language Code (ISO 639-3)', required=True, size=3, index=True)
    script = fields.Char(string='Script Code (ISO 15924)', required=True, size=4, default='Latn', index=True)
    content_type = fields.Selection([
        ('source', 'Original Source Text'),
        ('translation', 'Translation'),
        ('transliteration', 'Transliteration'),
        ('commentary', 'Commentary / Paraphrase')
    ], string='Content Type', required=True, default='source', index=True)
    translation_of = fields.Many2one(
        'moonwitness.sidra.expression',
        string='Translation Of (Source Expression)',
        ondelete='restrict',
        index=True,
        help='Points to the original source expression if this is a translation'
    )
    editor = fields.Char(string='Editor, Translator, or Reciter')
    edition_ids = fields.One2many('moonwitness.sidra.edition', 'expression_id', string='Editions / Manifestations')
    edition_count = fields.Integer(string='Edition Count', compute='_compute_edition_count')

    def _compute_edition_count(self):
        for rec in self:
            rec.edition_count = len(rec.edition_ids)
