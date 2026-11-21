# -*- coding: utf-8 -*-
import json
import logging
from flectra import api, fields, models

_logger = logging.getLogger(__name__)


class SidraKGNode(models.Model):
    """Layer 8: Unified Knowledge Graph Node spanning all Sidra layers."""
    _name = 'moonwitness.sidra.kg.node'
    _description = 'Sidra Knowledge Graph Node'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    entity_urn = fields.Char(string='Target Entity URN', required=True, index=True)
    entity_type = fields.Selection([
        ('tradition', 'Tradition'), ('work', 'Work'), ('passage', 'Passage'),
        ('primitive', 'Primitive'), ('divinity', 'Divinity'), ('realm', 'Realm'),
        ('character', 'Character'), ('story', 'Story'), ('motif', 'Motif'),
        ('concept', 'Concept'), ('assertion', 'Assertion')
    ], string='Node Type', required=True, index=True)
    label = fields.Char(string='Display Label', required=True, index=True)
    properties_json = fields.Text(string='Properties (JSON)')
    outgoing_edge_ids = fields.One2many('moonwitness.sidra.kg.edge', 'source_id', string='Outgoing Edges')
    incoming_edge_ids = fields.One2many('moonwitness.sidra.kg.edge', 'target_id', string='Incoming Edges')


class SidraKGEdge(models.Model):
    """Layer 8: Weighted directed semantic edge for native PostgreSQL Recursive CTE GraphRAG."""
    _name = 'moonwitness.sidra.kg.edge'
    _description = 'Sidra Knowledge Graph Edge'
    _inherit = ['moonwitness.sidra.base', 'moonwitness.sidra.provenance.mixin']

    source_id = fields.Many2one('moonwitness.sidra.kg.node', string='Source Node', required=True, ondelete='cascade', index=True)
    target_id = fields.Many2one('moonwitness.sidra.kg.node', string='Target Node', required=True, ondelete='cascade', index=True)
    relation_type = fields.Char(string='Relation Type', required=True, index=True,
                                help='e.g. contains, references, manifests, aligns_with, supports, participates_in')
    weight = fields.Float(string='Edge Weight (0.00-1.00)', default=1.0, digits=(4, 3))
    properties_json = fields.Text(string='Edge Metadata (JSON)')


class SidraEmbedding(models.Model):
    """Layer 8: Dense vector embedding storage linked to Content payloads (pgvector ready)."""
    _name = 'moonwitness.sidra.embedding'
    _description = 'Sidra Dense Vector Embedding'
    _inherit = ['moonwitness.sidra.base']

    content_id = fields.Many2one('moonwitness.sidra.content', string='Content Payload', required=True, ondelete='cascade', index=True)
    model_name = fields.Char(string='Embedding Model', required=True, default='bge-m3', index=True)
    dimensions = fields.Integer(string='Vector Dimensions', default=1024, required=True)
    vector_json = fields.Text(string='Vector Payload (JSON float array)', required=True)

    def _register_hook(self):
        super(SidraEmbedding, self)._register_hook()
        try:
            self.env.cr.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
            if self.env.cr.fetchone():
                self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception as exc:
            _logger.warning("pgvector extension check skipped: %s", exc)


class SidraQueryLog(models.Model):
    """Layer 8: Immutable GraphRAG Query Audit & Hallucination Detector Log."""
    _name = 'moonwitness.sidra.query.log'
    _description = 'Sidra GraphRAG Query & Hallucination Audit Log'
    _order = 'create_date desc, id desc'

    session_id = fields.Char(string='Session / WhatsApp Thread ID', index=True)
    query_text = fields.Text(string='User Query', required=True)
    strategy = fields.Selection([
        ('fts', 'Full-Text Search Only'),
        ('hybrid', 'Hybrid GraphRAG (FTS + KG CTE + Vector RRF)')
    ], string='Retrieval Strategy', default='hybrid', required=True)
    retrieved_passage_ids = fields.Many2many('moonwitness.sidra.passage', 'sidra_query_log_passage_rel', 'log_id', 'passage_id', string='Retrieved Passages')
    generated_answer = fields.Text(string='Generated Answer')
    citations_json = fields.Text(string='Verified Citations (JSON)')
    hallucination_score = fields.Float(
        string='Hallucination Risk Score (0.00-1.00)',
        default=0.0,
        digits=(4, 3),
        help='0.0 = 100% grounded in verified corpus citations; >0.5 = ungrounded / flagged'
    )
    verified_citations_count = fields.Integer(string='Verified Citations Count', default=0)
    unverified_citations_count = fields.Integer(string='Unverified Citations Count', default=0)
    user_feedback = fields.Selection([
        ('accurate', 'Accurate & Grounded'),
        ('partial', 'Partially Accurate'),
        ('hallucinated', 'Hallucinated / Ungrounded'),
        ('harmful', 'Doctrinally Misleading / Harmful')
    ], string='Human Review Feedback')
    latency_ms = fields.Integer(string='Execution Latency (ms)')
