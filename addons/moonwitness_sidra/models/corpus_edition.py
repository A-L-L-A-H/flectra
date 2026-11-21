# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCorpusEdition(models.Model):
    """FRBR Manifestation: Specific physical or digital publication/edition of an Expression."""
    _name = 'moonwitness.sidra.edition'
    _description = 'Sidra Corpus Edition (FRBR Manifestation)'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin'
    ]
    _order = 'expression_id, name'

    name = fields.Char(string='Edition Name', required=True, help='e.g. Tanzil Uthmani 1.1, Nestle-Aland 28')
    expression_id = fields.Many2one(
        'moonwitness.sidra.expression',
        string='Parent Expression',
        required=True,
        ondelete='restrict',
        index=True
    )
    publisher = fields.Char(string='Publisher / Institution')
    publication_date = fields.Date(string='Publication Date')
    publication_place = fields.Char(string='Publication Place')
    license_uri = fields.Char(string='License URI')
    rights_statement = fields.Text(string='Rights & Attribution Statement')
    checksum_sha256 = fields.Char(string='Source SHA-256 Checksum', size=64, index=True)
    format = fields.Selection([
        ('jsonl', 'JSONL Corpus Dataset'),
        ('plain_text', 'Raw Plain Text'),
        ('xml', 'TEI / DTS XML'),
        ('pdf', 'Facsimile / PDF')
    ], string='Storage Format', default='jsonl', required=True)

    passage_ids = fields.One2many('moonwitness.sidra.passage', 'edition_id', string='Passages')
    passage_count = fields.Integer(string='Passage Count', compute='_compute_passage_count')

    def _compute_passage_count(self):
        for rec in self:
            rec.passage_count = len(rec.passage_ids)
