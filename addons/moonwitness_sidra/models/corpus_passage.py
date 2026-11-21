# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraCorpusPassage(models.Model):
    """LRMoo Passage: Discrete canonical addressable unit of sacred text (Ayah, Verse, Sutta, Hadith)."""
    _name = 'moonwitness.sidra.passage'
    _description = 'Sidra Corpus Passage (LRMoo Passage)'
    _rec_name = 'urn'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin',
        'moonwitness.sidra.aqel.mixin'
    ]
    _order = 'edition_id, sequence, id'

    local_id = fields.Char(
        string='Local Citation Identifier',
        required=True,
        index=True,
        help='Reference string within edition, e.g. 1:1, 2:255, bukhari:1'
    )
    sequence = fields.Integer(
        string='Global Ordinal Sequence',
        required=True,
        index=True,
        help='Sequential position within the edition'
    )
    unit = fields.Selection([
        ('surah', 'Surah'),
        ('ayah', 'Ayah'),
        ('hadith', 'Hadith'),
        ('book', 'Book'),
        ('chapter', 'Chapter'),
        ('verse', 'Verse'),
        ('sutta', 'Sutta'),
        ('vagga', 'Vagga / Group'),
        ('section', 'Section / Paragraph')
    ], string='Textual Unit Type', required=True, index=True)

    edition_id = fields.Many2one(
        'moonwitness.sidra.edition',
        string='Parent Edition',
        required=True,
        ondelete='restrict',
        index=True
    )
    citation_scheme_id = fields.Many2one(
        'moonwitness.sidra.citation.scheme',
        string='Citation Scheme',
        ondelete='restrict'
    )
    container_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Parent Container Passage',
        ondelete='restrict',
        index=True,
        help='Hierarchy container (e.g. Surah 2 contains Ayah 255)'
    )
    child_passage_ids = fields.One2many(
        'moonwitness.sidra.passage',
        'container_id',
        string='Sub-passages'
    )
    content_ids = fields.One2many(
        'moonwitness.sidra.content',
        'passage_id',
        string='Verbatim Text Payloads'
    )
    primary_text = fields.Text(
        string='Primary Verbatim Text',
        compute='_compute_primary_text',
        store=True
    )

    @api.depends('content_ids.text', 'content_ids.is_primary')
    def _compute_primary_text(self):
        for rec in self:
            primary = rec.content_ids.filtered(lambda c: c.is_primary)
            if primary:
                rec.primary_text = primary[0].text
            elif rec.content_ids:
                rec.primary_text = rec.content_ids[0].text
            else:
                rec.primary_text = False
