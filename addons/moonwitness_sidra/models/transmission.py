# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraTransmissionNarrator(models.Model):
    """Biografi perawi sanad dan evaluasi kredibilitas (*Jarh wa Ta'dil*)."""
    _name = 'moonwitness.sidra.transmission.narrator'
    _description = 'Sidra Hadith Transmitter / Narrator (Rijal)'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']
    _order = 'generation_tier, name'

    name = fields.Char(string='Narrator Name (Ism)', required=True, index=True)
    kunya = fields.Char(string='Kunya / Title', help='e.g. Abu Hurairah, Abu Bakr, Umm al-Mu\'minin')
    generation_tier = fields.Selection([
        ('sahaba', 'Companion (Sahabi / رضي الله عنه)'),
        ('tabiin', 'Successor (Tabi\'i / رحمه الله)'),
        ('atba_tabiin', 'Successor of Successors (Tabi\' al-Tabi\'in)'),
        ('later', 'Later Classical Transmitter / Muhaddith')
    ], string='Generational Tier (Tabaqah)', required=True, default='sahaba', index=True)
    death_year_ah = fields.Integer(string='Death Year (AH)', index=True)
    death_year_ce = fields.Integer(string='Death Year (CE)')
    residence = fields.Char(string='Primary City / Region of Residence', help='e.g. Madinah, Kufa, Basra, Damascus')
    reliability = fields.Selection([
        ('thiqah_thabt', 'Thiqah Thabt (Highest Authenticity & Accuracy)'),
        ('thiqah', 'Thiqah (Trustworthy)'),
        ('saduq', 'Saduq (Truthful / Good Memory)'),
        ('maqbul', 'Maqbul (Acceptable with Corroboration)'),
        ('daif', 'Daif (Weak / Questionable Retention)'),
        ('matruk', 'Matruk (Abandoned in Transmission)'),
        ('waddah', 'Waddah (Fabricator / Rejected)')
    ], string='Grading of Credibility (Jarh wa Ta\'dil)', default='thiqah', required=True, index=True)
    biography = fields.Text(string='Biographical Assessment & Critical Notes')


class SidraTransmissionIsnad(models.Model):
    """Jaringan rantai sanad hadits dan ketersambungan transmisi lisan ke tulisan."""
    _name = 'moonwitness.sidra.transmission.isnad'
    _description = 'Sidra Transmission Chain (Isnad Graph)'
    _rec_name = 'urn'
    _inherit = [
        'moonwitness.sidra.base',
        'moonwitness.sidra.provenance.mixin',
        'moonwitness.sidra.epistemic.mixin'
    ]
    _order = 'passage_id, id'

    passage_id = fields.Many2one(
        'moonwitness.sidra.passage',
        string='Associated Hadith Passage',
        required=True,
        ondelete='cascade',
        index=True
    )
    continuity = fields.Selection([
        ('muttashil', 'Muttashil (Continuous Unbroken Chain)'),
        ('munqathi', 'Munqathi (Interrupted / Broken Chain)'),
        ('mursal', 'Mursal (Missing Companion Link)'),
        ('muallaq', 'Muallaq (Suspended Chain Beginning)')
    ], string='Isnad Continuity (Ittishal)', default='muttashil', required=True, index=True)
    overall_grade = fields.Selection([
        ('sahih', 'Sahih (Rigorous Authenticity)'),
        ('hasan', 'Hasan (Good / Fair)'),
        ('daif', 'Daif (Weak)'),
        ('mawdu', 'Mawdu (Fabricated / Forged)')
    ], string='Final Tradition Grade (Hukm)', default='sahih', required=True, index=True)
    evaluator = fields.Char(string='Evaluating Scholar / Standard', default='Imam al-Bukhari')
    narrator_ids = fields.Many2many(
        'moonwitness.sidra.transmission.narrator',
        'sidra_isnad_narrator_rel',
        'isnad_id',
        'narrator_id',
        string='Ordered Narrator Chain (Sanad Transmitters)'
    )
    chain_text = fields.Text(string='Raw Transmitted Sanad Formula (Arabic)')
