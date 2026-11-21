# -*- coding: utf-8 -*-
from flectra import api, fields, models


class SidraStory(models.Model):
    """Layer 7: Sacred narrative arc linking ordered passages, protagonists, and motifs."""
    _name = 'moonwitness.sidra.story'
    _description = 'Sidra Sacred Story / Narrative Arc'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.aqel.mixin']

    name = fields.Char(string='Story Title', required=True, translate=True, index=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    narrative_type = fields.Selection([
        ('history', 'Prophetic / Sacred History (Qasas)'),
        ('parable', 'Parable / Similitude (Mathal)'),
        ('myth', 'Cosmogonic / Primordial Account'),
        ('vision', 'Apocalyptic / Visionary Experience'),
        ('genealogy', 'Genealogy / Lineage Account'),
        ('law', 'Legal Narrative Context'),
        ('hymn', 'Hymnic / Devotional Narrative')
    ], string='Narrative Genre', required=True, default='history', index=True)
    summary = fields.Text(string='Narrative Arc Summary')
    passage_ids = fields.Many2many('moonwitness.sidra.passage', 'sidra_story_passage_rel', 'story_id', 'passage_id', string='Ordered Passages')
    motif_ids = fields.Many2many('moonwitness.sidra.motif', 'sidra_story_motif_rel', 'story_id', 'motif_id', string='Associated Motifs')
    participation_ids = fields.One2many('moonwitness.sidra.character.participation', 'story_id', string='Character Participations')


class SidraCharacter(models.Model):
    """Layer 7: Narrative & historical figure modeled with GOLEM ontology (endurant/perdurant/role)."""
    _name = 'moonwitness.sidra.character'
    _description = 'Sidra Sacred Character (GOLEM Ontology)'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']

    name = fields.Char(string='Character Name', required=True, translate=True, index=True)
    tradition_id = fields.Many2one('moonwitness.sidra.tradition', required=True, ondelete='restrict', index=True)
    epithets = fields.Char(string='Honorifics & Epithets (e.g. Kalimullah, Bodhisattva)')
    character_type = fields.Selection([
        ('human', 'Human / Prophet / Sage / Historical Figure'),
        ('divine', 'Divine Figure'),
        ('angel', 'Angelic / Celestial Being (Malak / Deva)'),
        ('jinn', 'Jinn / Spirit / Subtle Being'),
        ('animal', 'Symbolic / Narrative Animal'),
        ('object', 'Sacred Object / Artifact (e.g. Ark, Staff)'),
        ('abstract', 'Personified Abstract Principle')
    ], string='Character Type', required=True, default='human', index=True)
    ontological_status = fields.Selection([
        ('endurant', 'Endurant (Persisting Entity)'),
        ('perdurant', 'Perdurant (Process / Event-bound)'),
        ('quality', 'Quality / Attribute'),
        ('role', 'Social / Prophetic Role')
    ], string='GOLEM Ontological Status', required=True, default='endurant', index=True)
    divinity_id = fields.Many2one('moonwitness.sidra.divinity', string='Linked Divinity (if applicable)', ondelete='set null')
    attributes_json = fields.Text(string='Character Attributes (JSON)')
    experience_ids = fields.One2many('moonwitness.sidra.experience', 'character_id', string='Phenomenological Experiences')


class SidraCharacterParticipation(models.Model):
    """Layer 7: Event participation role of a Character inside a Story passage."""
    _name = 'moonwitness.sidra.character.participation'
    _description = 'Sidra Character Event Participation'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    character_id = fields.Many2one('moonwitness.sidra.character', required=True, ondelete='cascade', index=True)
    story_id = fields.Many2one('moonwitness.sidra.story', required=True, ondelete='cascade', index=True)
    event_passage_id = fields.Many2one('moonwitness.sidra.passage', string='Event Passage', required=True, ondelete='restrict', index=True)
    role = fields.Selection([
        ('agent', 'Agent (Initiator)'),
        ('patient', 'Patient (Affected)'),
        ('experiencer', 'Experiencer (Perceiver)'),
        ('beneficiary', 'Beneficiary'),
        ('instrument', 'Instrument'),
        ('location', 'Location'),
        ('witness', 'Witness')
    ], string='Event Role', required=True, default='agent')
    tense = fields.Selection([
        ('past', 'Past'), ('present', 'Present'), ('future', 'Future / Eschatological'), ('timeless', 'Timeless / Eternal')
    ], string='Temporal Tense', default='past', required=True)


class SidraExperience(models.Model):
    """Layer 7: Qualitative phenomenological account of spiritual or existential experience in text."""
    _name = 'moonwitness.sidra.experience'
    _description = 'Sidra Phenomenological Spiritual Experience'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin', 'moonwitness.sidra.epistemic.mixin']

    character_id = fields.Many2one('moonwitness.sidra.character', required=True, ondelete='cascade', index=True)
    passage_id = fields.Many2one('moonwitness.sidra.passage', required=True, ondelete='restrict', index=True)
    experience_type = fields.Selection([
        ('mystical', 'Mystical / Numinous Encounter (Mysterium Tremendum)'),
        ('perceptual', 'Perceptual / Visionary'),
        ('emotional', 'Emotional / Affective (Awe, Sorrow, Gratitude)'),
        ('cognitive', 'Cognitive / Illumination / Realization'),
        ('volitional', 'Volitional / Submission / Resolve')
    ], string='Experience Type', required=True, default='mystical', index=True)
    valence = fields.Selection([
        ('positive', 'Positive'), ('negative', 'Negative'), ('neutral', 'Neutral'), ('mixed', 'Mixed / Awe-Fear')
    ], string='Valence', default='positive', required=True)
    intensity = fields.Integer(string='Intensity (1-10)', default=8)
    description = fields.Text(string='Phenomenological Description')
