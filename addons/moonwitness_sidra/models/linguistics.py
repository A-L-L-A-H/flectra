# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraLexicon(models.Model):
    """W3C OntoLex-Lemon sacred language lexicon (Arabic, Hebrew, Greek, Pali, Sanskrit)."""
    _name = 'moonwitness.sidra.lexicon'
    _description = 'Sidra Sacred Lexicon (OntoLex-Lemon)'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    name = fields.Char(string='Lexicon Name', required=True)
    language = fields.Char(string='Language Code (ISO 639-1/3)', required=True, size=3, index=True)
    script = fields.Char(string='Script Code (ISO 15924)', required=True, size=4, default='Arab')
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', string='Primary Tradition', ondelete='restrict')
    version = fields.Char(string='Lexicon Version')
    source_uri = fields.Char(string='Upstream URI')
    word_ids = fields.One2many('moonwitness.sidra.word', 'lexicon_id', string='Lexical Entries')
    entry_count = fields.Integer(string='Entry Count', compute='_compute_entry_count')

    def _compute_entry_count(self):
        for rec in self:
            rec.entry_count = len(rec.word_ids)


class SidraWord(models.Model):
    """Token/lemma-level lexical unit with Semitic root / Sanskrit dhatu and UD v2 POS."""
    _name = 'moonwitness.sidra.word'
    _description = 'Sidra Lexical Word / Token'
    _rec_name = 'form'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']
    _order = 'passage_id, token_index, id'

    lexicon_id = fields.Many2one('moonwitness.sidra.lexicon', string='Lexicon', required=True, ondelete='restrict', index=True)
    passage_id = fields.Many2one('moonwitness.sidra.passage', string='Source Passage', ondelete='cascade', index=True)
    token_index = fields.Integer(string='Token Position', default=0, index=True)
    form = fields.Char(string='Surface Form', required=True, index=True)
    vocalization = fields.Char(string='Vocalized Form')
    lemma = fields.Char(string='Lemma', index=True)
    root = fields.Char(string='Root / Dhatu', index=True, help='Semitic triliteral root (e.g. ر-ح-م) or Sanskrit dhatu')
    pattern = fields.Char(string='Morphological Pattern (Wazn)')
    pos = fields.Selection([
        ('NOUN', 'Noun'), ('PROPN', 'Proper Noun'), ('VERB', 'Verb'), ('ADJ', 'Adjective'),
        ('ADV', 'Adverb'), ('PRON', 'Pronoun'), ('ADP', 'Adposition / Preposition'),
        ('CONJ', 'Conjunction'), ('CCONJ', 'Coordinating Conjunction'), ('SCONJ', 'Subordinating Conjunction'),
        ('DET', 'Determiner'), ('PART', 'Particle'), ('NUM', 'Numeral'), ('INTJ', 'Interjection'),
        ('AUX', 'Auxiliary'), ('PUNCT', 'Punctuation'), ('X', 'Other / Unclassified')
    ], string='Part of Speech (UD v2)', index=True)
    morph_features = fields.Text(string='Morphological Features (JSON UD v2)')
    gloss = fields.Char(string='Concise Gloss / Meaning')
    frequency = fields.Integer(string='Corpus Frequency', default=1)


class SidraMorphology(models.Model):
    """Inflectional paradigm tables for sacred language lemmas."""
    _name = 'moonwitness.sidra.morphology'
    _description = 'Sidra Morphological Paradigm'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    lexicon_id = fields.Many2one('moonwitness.sidra.lexicon', required=True, ondelete='restrict', index=True)
    lemma = fields.Char(string='Lemma', required=True, index=True)
    paradigm_type = fields.Selection([
        ('noun', 'Noun Declension'), ('verb', 'Verb Conjugation'),
        ('adj', 'Adjective'), ('pron', 'Pronoun'), ('num', 'Numeral')
    ], string='Paradigm Type', required=True, default='verb')
    paradigm_json = fields.Text(string='Inflectional Forms (JSON)', required=True)
    irregular = fields.Boolean(string='Irregular Paradigm', default=False)


class SidraTranslationUnit(models.Model):
    """Segment-level aligned translation unit comparing source and translated passages."""
    _name = 'moonwitness.sidra.translation.unit'
    _description = 'Sidra Parallel Translation Unit'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']

    source_passage_id = fields.Many2one('moonwitness.sidra.passage', string='Source Passage', required=True, ondelete='cascade', index=True)
    target_expression_id = fields.Many2one('moonwitness.sidra.expression', string='Target Translation Expression', required=True, ondelete='restrict', index=True)
    source_segment = fields.Text(string='Source Segment Text', required=True)
    target_segment = fields.Text(string='Translated Segment Text', required=True)
    alignment_score = fields.Float(string='Alignment Score (0-1)', default=1.0, digits=(4, 3))
    aligner = fields.Selection([
        ('manual', 'Manual Scholar Alignment'),
        ('eflomal', 'Eflomal Statistical Aligner'),
        ('awesome_align', 'Awesome-Align Neural'),
        ('simalign', 'SimAlign')
    ], string='Alignment Method', default='manual', required=True)
