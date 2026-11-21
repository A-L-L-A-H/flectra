# -*- coding: utf-8 -*-
from flectra import _, api, fields, models
from flectra.exceptions import AccessError, UserError, ValidationError

from .orchestrator_client import (
    ORCHESTRATOR_TOKEN_PARAM,
    ORCHESTRATOR_URL_PARAM,
    OrchestratorError,
    validate_orchestrator_url,
)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    moonwitness_orchestrator_url = fields.Char(
        string='Orchestrator URL',
        config_parameter=ORCHESTRATOR_URL_PARAM,
        default='http://orchestrator:8090',
    )
    moonwitness_orchestrator_token = fields.Char(
        string='Orchestrator Token',
        config_parameter=ORCHESTRATOR_TOKEN_PARAM,
    )

    @api.constrains('moonwitness_orchestrator_url')
    def _check_moonwitness_orchestrator_url(self):
        for record in self:
            if not record.moonwitness_orchestrator_url:
                continue
            try:
                validate_orchestrator_url(record.moonwitness_orchestrator_url)
            except OrchestratorError as err:
                raise ValidationError(str(err)) from err

    def action_test_moonwitness_orchestrator_connection(self):
        self.ensure_one()
        if not self.env.user.has_group('moonwitness_orchestrator.group_moonwitness_orchestrator'):
            raise AccessError(_('Only MoonWitness Orchestrator administrators can test this connection.'))

        base_url = (self.moonwitness_orchestrator_url or '').strip()
        token = (self.moonwitness_orchestrator_token or '').strip()
        if not base_url or not token:
            raise UserError(_('Orchestrator URL and token must be configured before testing the connection.'))
        try:
            validate_orchestrator_url(base_url)
        except OrchestratorError as err:
            raise UserError(str(err)) from err

        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param(ORCHESTRATOR_URL_PARAM, base_url)
        icp.set_param(ORCHESTRATOR_TOKEN_PARAM, token)

        try:
            status_payload = self.env['moonwitness.orchestrator'].status()
        except OrchestratorError as err:
            raise UserError(str(err)) from err

        status_label = status_payload.get('status') if isinstance(status_payload, dict) else None
        message = (
            _('Connected to MoonWitness Orchestrator (%s).', status_label)
            if status_label
            else _('Connected to MoonWitness Orchestrator successfully.')
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('MoonWitness Orchestrator'),
                'message': message,
                'type': 'success',
                'sticky': False,
            },
        }
