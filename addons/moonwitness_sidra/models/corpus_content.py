# -*- coding: utf-8 -*-
import re
from flectra import api, fields, models
from flectra.exceptions import ValidationError

# Pre-compiled regex for Semitic diacritic normalization
ARABIC_DIACRITICS = re.compile(r'[\u064B-\u0652\u0670\u0640]')
HEBREW_DIACRITICS = re.compile(r'[\u0591-\u05C7]')


class SidraCorpusContent(models.Model):
    """Verbatim text content payload for a Passage in a specific Expression with indexed FTS."""
    _name = 'moonwitness.sidra.content'
    _description = 'Sidra Corpus Content Payload'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    _order = 'passage_id, is_primary desc'

    passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Parent Passage',
        required=True,
        ondelete='cascade',
        index=True
    )
    expression_id = fields.Many2one(
        'moonwitness.sidra.expression',
        string='Expression',
        required=True,
        ondelete='restrict',
        index=True
    )
    text = fields.Text(string='Verbatim Text Payload', required=True)
    text_search = fields.Text(
        string='FTS Search Vector',
        compute='_compute_text_search',
        store=True,
        help='Indexed full-text vector with Semitic diacritic normalization'
    )
    language = fields.Char(
        related='expression_id.language',
        string='Language Code',
        store=True,
        index=True
    )
    is_primary = fields.Boolean(
        string='Primary Expression Payload',
        default=False,
        help='True if this represents the primary original text payload for the passage'
    )
    char_count = fields.Integer(
        string='Character Count',
        compute='_compute_char_count',
        store=True
    )

    @api.constrains('passage_id', 'expression_id', 'is_primary')
    def _check_unique_primary_content(self):
        for rec in self:
            if rec.is_primary and rec.passage_id and rec.expression_id:
                duplicate = self.search([
                    ('id', '!=', rec.id),
                    ('passage_id', '=', rec.passage_id.id),
                    ('expression_id', '=', rec.expression_id.id),
                    ('is_primary', '=', True),
                ], limit=1)
                if duplicate:
                    raise ValidationError('Only one primary content payload is permitted per passage and expression.')

    @api.depends('text')
    def _compute_char_count(self):
        for rec in self:
            rec.char_count = len(rec.text) if rec.text else 0

    @api.depends('text', 'language')
    def _compute_text_search(self):
        for rec in self:
            if not rec.text:
                rec.text_search = False
                continue
            normalized_text = rec._normalize_for_fts(rec.text, rec.language)
            config = rec._get_ts_config(rec.language)
            try:
                self.env.cr.execute("SELECT to_tsvector(%s, %s)", (config, normalized_text))
                row = self.env.cr.fetchone()
                rec.text_search = row[0] if row else False
            except Exception:
                rec.text_search = normalized_text

    @api.model
    def _normalize_for_fts(self, text, language):
        """Strip vocalization/diacritics for Semitic languages to enable flexible search."""
        if not text:
            return ''
        if language in ('ara', 'ar'):
            return ARABIC_DIACRITICS.sub('', text)
        elif language in ('heb', 'he'):
            return HEBREW_DIACRITICS.sub('', text)
        return text

    @api.model
    def _get_ts_config(self, language):
        """Map ISO 639-1/639-3 language codes to PostgreSQL FTS dictionary configurations."""
        mapping = {
            'ar': 'arabic',
            'ara': 'arabic',
            'he': 'simple',
            'heb': 'simple',
            'grc': 'simple',
            'el': 'simple',
            'pli': 'simple',
            'pi': 'simple',
            'san': 'simple',
            'sa': 'simple',
            'id': 'indonesian',
            'ind': 'indonesian',
            'en': 'english',
            'eng': 'english',
            'fr': 'french',
            'fra': 'french',
            'de': 'german',
            'deu': 'german',
        }
        return mapping.get(language, 'simple')
