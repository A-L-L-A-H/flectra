# -*- coding: utf-8 -*-
from unittest import mock

from flectra.exceptions import AccessError, UserError, ValidationError
from flectra.tests.common import TransactionCase

from ..models import orchestrator_client as client_module


class TestOrchestratorResConfigSettings(TransactionCase):
    """Unit tests for MoonWitness Orchestrator res.config.settings."""

    def setUp(self):
        super().setUp()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.admin_group = self.env.ref('moonwitness_orchestrator.group_moonwitness_orchestrator')
        self.admin_user = self.env['res.users'].create({
            'name': 'Orchestrator Admin',
            'login': 'orch_settings_admin',
            'email': 'orch_settings_admin@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_system').id, self.admin_group.id])],
        })
        self.non_admin_user = self.env['res.users'].create({
            'name': 'Regular User',
            'login': 'orch_settings_user',
            'email': 'orch_settings_user@example.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_execute_persists_settings_under_moonwitness_orchestrator_params(self):
        settings = self.env['res.config.settings'].with_user(self.admin_user).create({
            'moonwitness_orchestrator_url': 'https://orchestrator.internal:8443',
            'moonwitness_orchestrator_token': 'super-secret-token',
        })
        settings.execute()

        self.assertEqual(
            self.icp.get_param(client_module.ORCHESTRATOR_URL_PARAM),
            'https://orchestrator.internal:8443',
        )
        self.assertEqual(
            self.icp.get_param(client_module.ORCHESTRATOR_TOKEN_PARAM),
            'super-secret-token',
        )

    def test_invalid_url_constraint_rejects_bad_urls(self):
        for bad_url in ('ftp://orchestrator:8090', '/relative', 'orchestrator:8090'):
            with self.subTest(bad_url=bad_url):
                with self.assertRaises(ValidationError):
                    self.env['res.config.settings'].with_user(self.admin_user).create({
                        'moonwitness_orchestrator_url': bad_url,
                    })

    def test_action_test_connection_requires_orchestrator_admin_group(self):
        settings = self.env['res.config.settings'].sudo().create({
            'moonwitness_orchestrator_url': 'http://orchestrator:8090',
            'moonwitness_orchestrator_token': 'secret-token',
        })
        with self.assertRaises(AccessError):
            settings.with_user(self.non_admin_user).action_test_moonwitness_orchestrator_connection()

    def test_action_test_connection_requires_token_and_returns_notification(self):
        missing_token_settings = self.env['res.config.settings'].with_user(self.admin_user).create({
            'moonwitness_orchestrator_url': 'http://orchestrator:8090',
            'moonwitness_orchestrator_token': '',
        })
        with self.assertRaises(UserError):
            missing_token_settings.action_test_moonwitness_orchestrator_connection()

        settings = self.env['res.config.settings'].with_user(self.admin_user).create({
            'moonwitness_orchestrator_url': 'http://orchestrator:8090',
            'moonwitness_orchestrator_token': 'secret-token-value',
        })
        with mock.patch.object(
            type(self.env['moonwitness.orchestrator']),
            'status',
            return_value={'status': 'ok'},
        ) as mock_status:
            action = settings.action_test_moonwitness_orchestrator_connection()

        mock_status.assert_called_once_with()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')
        self.assertNotIn('secret-token-value', str(action))
