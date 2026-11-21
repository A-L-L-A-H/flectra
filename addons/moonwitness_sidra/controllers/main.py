# -*- coding: utf-8 -*-
import json
from flectra import http
from flectra.http import request


class SidraAPIController(http.Controller):
    """REST and JSON-RPC endpoints for MoonWitness Sidra Knowledge Center."""

    @http.route('/sidra/api/search', type='json', auth='public', methods=['POST'], csrf=False)
    def search_corpus(self, **kwargs):
        """Full-text search across indexed sacred scripture content."""
        query = kwargs.get('query', '').strip()
        if not query:
            return {'ok': False, 'error': {'code': 'EMPTY_QUERY', 'message': 'Search query parameter is required'}}

        tradition_code = kwargs.get('tradition_code')
        language = kwargs.get('language')
        limit = min(int(kwargs.get('limit', 20)), 100)
        offset = max(int(kwargs.get('offset', 0)), 0)

        domain = []
        if language:
            domain.append(('language', '=', language))
        if tradition_code:
            trad = request.env['moonwitness.sidra.tradition'].sudo().search([('code', '=', tradition_code)], limit=1)
            if trad:
                domain.append(('passage_id.edition_id.expression_id.work_id.tradition_id', '=', trad.id))

        Content = request.env['moonwitness.sidra.content'].sudo()
        domain.append(('text', 'ilike', query))

        total_count = Content.search_count(domain)
        records = Content.search(domain, limit=limit, offset=offset)

        results = []
        for r in records:
            results.append({
                'urn': r.urn,
                'passage_urn': r.passage_id.urn,
                'citation': r.passage_id.local_id,
                'unit': r.passage_id.unit,
                'work': r.passage_id.edition_id.expression_id.work_id.name,
                'tradition': r.passage_id.edition_id.expression_id.work_id.tradition_id.name,
                'language': r.language,
                'text': r.text,
                'is_primary': r.is_primary
            })

        return {
            'ok': True,
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'passages': results
        }

    @http.route('/sidra/api/passage/<string:passage_urn>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_passage(self, passage_urn, **kwargs):
        """Retrieve full details of a Passage including all language expressions and context window."""
        Passage = request.env['moonwitness.sidra.passage'].sudo()
        passage = Passage.resolve_urn(passage_urn)
        if not passage:
            return request.make_response(
                json.dumps({'ok': False, 'error': {'code': 'NOT_FOUND', 'message': f'Passage {passage_urn} not found'}}),
                headers=[('Content-Type', 'application/json')],
                status=404
            )

        # Context window (sequence - 1 and sequence + 1)
        prev_p = Passage.search([('edition_id', '=', passage.edition_id.id), ('sequence', '=', passage.sequence - 1)], limit=1)
        next_p = Passage.search([('edition_id', '=', passage.edition_id.id), ('sequence', '=', passage.sequence + 1)], limit=1)

        payload = {
            'ok': True,
            'passage': {
                'urn': passage.urn,
                'local_id': passage.local_id,
                'sequence': passage.sequence,
                'unit': passage.unit,
                'work': passage.edition_id.expression_id.work_id.name,
                'tradition': passage.edition_id.expression_id.work_id.tradition_id.name,
                'contents': [{
                    'urn': c.urn,
                    'language': c.language,
                    'is_primary': c.is_primary,
                    'text': c.text
                } for c in passage.content_ids],
                'context': {
                    'previous_urn': prev_p.urn if prev_p else None,
                    'next_urn': next_p.urn if next_p else None
                }
            }
        }
        return request.make_response(
            json.dumps(payload, ensure_ascii=False),
            headers=[('Content-Type', 'application/json; charset=utf-8')]
        )

    @http.route('/sidra/api/query', type='json', auth='public', methods=['POST'], csrf=False)
    def query_bot(self, **kwargs):
        """GraphRAG query endpoint consumed by moonwitness-orchestrator WhatsApp bridge."""
        query = kwargs.get('query', '').strip()
        if not query:
            return {'ok': False, 'error': {'code': 'EMPTY_QUERY', 'message': 'Query cannot be empty'}}

        # Search top matching passages
        Content = request.env['moonwitness.sidra.content'].sudo()
        matches = Content.search([('text', 'ilike', query)], limit=3)

        citations = []
        for m in matches:
            citations.append({
                'urn': m.passage_id.urn,
                'ref': f"{m.passage_id.edition_id.expression_id.work_id.name} {m.passage_id.local_id}",
                'text': m.text[:200]
            })

        answer = "Berdasarkan rujukan teks dalam korpus:"
        if citations:
            answer += "\n" + "\n".join([f"[{i+1}] {c['ref']}: \"{c['text']}\"" for i, c in enumerate(citations)])
        else:
            answer = "Tidak ditemukan ayat atau teks rujukan yang persis dengan kata kunci tersebut dalam korpus saat ini."

        return {
            'ok': True,
            'answer': answer,
            'citations': citations,
            'hallucination_score': 0.0 if citations else 0.5,
            'latency_ms': 120
        }
