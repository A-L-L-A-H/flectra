# -*- coding: utf-8 -*-
import hashlib
import json
import re
from flectra import api, models

HEX64_REGEX = re.compile(r'^[0-9a-f]{64}$')


class SidraValidatorService(models.AbstractModel):
    """P1-006 Semantic Invariant Engine validating RGBL v0.1 corpus integrity."""
    _name = 'moonwitness.sidra.validator.service'
    _description = 'Sidra P1-006 Semantic Validator Service'

    @api.model
    def validate_all(self):
        """Run all P1-006 validation passes and return list of finding dictionaries."""
        findings = []
        findings.extend(self.check_record_family_id_kind())
        findings.extend(self.check_nonblank_kind())
        findings.extend(self.check_provenance_required())
        findings.extend(self.check_translation_identity())
        findings.extend(self.check_deterministic_ids())
        return findings

    @api.model
    def check_record_family_id_kind(self):
        """Rule: Canonical URN prefix must match the record family."""
        findings = []
        families = {
            'moonwitness.sidra.provenance': 'mw:provenance:',
            'moonwitness.sidra.epistemic.status': 'mw:epistemic:'
        }
        for model_name, expected_prefix in families.items():
            if model_name not in self.env:
                continue
            records = self.env[model_name].search([])
            for rec in records:
                if rec.urn and not rec.urn.startswith(expected_prefix):
                    findings.append({
                        'code': 'record-family-id-kind',
                        'level': 'ERROR',
                        'model': model_name,
                        'res_id': rec.id,
                        'urn': rec.urn,
                        'message': f"URN '{rec.urn}' does not start with expected family prefix '{expected_prefix}'"
                    })
        return findings

    @api.model
    def check_nonblank_kind(self):
        """Rule: Classification fields must not be blank or whitespace."""
        findings = []
        # Check Works
        if 'moonwitness.sidra.work' in self.env:
            for work in self.env['moonwitness.sidra.work'].search([]):
                if not work.kind or not str(work.kind).strip():
                    findings.append({
                        'code': 'nonblank-kind',
                        'level': 'ERROR',
                        'model': 'moonwitness.sidra.work',
                        'res_id': work.id,
                        'urn': work.urn,
                        'message': 'Work.kind must not be blank'
                    })
        # Check Expressions
        if 'moonwitness.sidra.expression' in self.env:
            for expr in self.env['moonwitness.sidra.expression'].search([]):
                if not expr.content_type or not str(expr.content_type).strip():
                    findings.append({
                        'code': 'nonblank-kind',
                        'level': 'ERROR',
                        'model': 'moonwitness.sidra.expression',
                        'res_id': expr.id,
                        'urn': expr.urn,
                        'message': 'Expression.content_type must not be blank'
                    })
        return findings

    @api.model
    def check_provenance_required(self):
        """Rule: Every entity must link to a valid provenance record."""
        findings = []
        provenance_models = [
            'moonwitness.sidra.work',
            'moonwitness.sidra.expression',
            'moonwitness.sidra.edition',
            'moonwitness.sidra.passage',
            'moonwitness.sidra.content',
            'moonwitness.sidra.tradition'
        ]
        for model_name in provenance_models:
            if model_name not in self.env:
                continue
            unlinked = self.env[model_name].search([('provenance_id', '=', False)])
            for rec in unlinked:
                findings.append({
                    'code': 'provenance-required',
                    'level': 'ERROR',
                    'model': model_name,
                    'res_id': rec.id,
                    'urn': getattr(rec, 'urn', False),
                    'message': f"Record in {model_name} lacks mandatory provenance_id link."
                })
        return findings

    @api.model
    def check_translation_identity(self):
        """Rule 2: Translation must not overwrite source; must link to source expression."""
        findings = []
        if 'moonwitness.sidra.expression' not in self.env:
            return findings
        translations = self.env['moonwitness.sidra.expression'].search([('content_type', '=', 'translation')])
        for expr in translations:
            if not expr.translation_of:
                findings.append({
                    'code': 'translation-identity',
                    'level': 'ERROR',
                    'model': 'moonwitness.sidra.expression',
                    'res_id': expr.id,
                    'urn': expr.urn,
                    'message': f"Translation expression '{expr.name}' must declare 'translation_of' pointing to source expression."
                })
        return findings

    @api.model
    def check_deterministic_ids(self):
        """Rule: For mw:<type>:v1:sha256:<digest>, verify 64-hex format."""
        findings = []
        for model_name in ['moonwitness.sidra.work', 'moonwitness.sidra.passage', 'moonwitness.sidra.content']:
            if model_name not in self.env:
                continue
            for rec in self.env[model_name].search([]):
                if rec.urn and ':v1:sha256:' in rec.urn:
                    parts = rec.urn.split(':v1:sha256:')
                    if len(parts) != 2 or not HEX64_REGEX.match(parts[1]):
                        findings.append({
                            'code': 'malformed-deterministic-id',
                            'level': 'ERROR',
                            'model': model_name,
                            'res_id': rec.id,
                            'urn': rec.urn,
                            'message': f"Deterministic URN '{rec.urn}' contains an invalid 64-character lowercase hex digest."
                        })
        return findings
