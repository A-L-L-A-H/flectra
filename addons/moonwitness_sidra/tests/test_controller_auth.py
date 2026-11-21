# -*- coding: utf-8 -*-
from flectra.exceptions import AccessError
from flectra.tests.common import TransactionCase
from ..controllers.main import SidraAPIController


class TestSidraControllerAuth(TransactionCase):
    """Tests _guard_sidra authentication, RBAC group check, and constant-time service token check."""

    def setUp(self):
        super().setUp()
        self.controller = SidraAPIController()
        self.icp = self.env['ir.config_parameter'].sudo()
        self.icp.set_param('moonwitness_sidra.api_token', 'sidra-test-secret-token-2026')
        self.public_user = self.env.ref('base.public_user')
        self.admin_user = self.env.ref('base.user_admin')

    def test_rejects_public_user_without_token(self):
        with self.mock_request_env(self.public_user):
            self.assertFalse(self.controller._is_authorized(headers={}))
            with self.assertRaises(AccessError):
                self.controller._guard_sidra(headers={})

    def test_rejects_public_user_with_invalid_token(self):
        with self.mock_request_env(self.public_user):
            self.assertFalse(self.controller._is_authorized(headers={'x-sidra-token': 'wrong-token'}))
            with self.assertRaises(AccessError):
                self.controller._guard_sidra(headers={'x-sidra-token': 'wrong-token'})

    def test_accepts_valid_sidra_or_orchestrator_token(self):
        with self.mock_request_env(self.public_user):
            self.assertTrue(self.controller._is_authorized(headers={'x-sidra-token': 'sidra-test-secret-token-2026'}))
            self.controller._guard_sidra(headers={'X-Orchestrator-Token': 'sidra-test-secret-token-2026'})

    def test_accepts_authenticated_reader_user_without_token(self):
        with self.mock_request_env(self.admin_user):
            self.assertTrue(self.controller._is_authorized(headers={}))
            self.controller._guard_sidra(headers={})

    def test_rbac_hierarchy_links_base_groups(self):
        base_user_grp = self.env.ref('moonwitness_base.group_moonwitness_base_user')
        base_admin_grp = self.env.ref('moonwitness_base.group_moonwitness_base_admin')
        sidra_reader = self.env.ref('moonwitness_sidra.group_moonwitness_sidra_reader')
        sidra_manager = self.env.ref('moonwitness_sidra.group_moonwitness_sidra_manager')
        self.assertIn(base_user_grp, sidra_reader.trans_implied_ids)
        self.assertIn(sidra_manager, base_admin_grp.trans_implied_ids)

    from contextlib import contextmanager

    @contextmanager
    def mock_request_env(self, user):
        from unittest import mock
        from ..controllers import main as controller_module
        fake_req = mock.MagicMock()
        fake_req.env = self.env(user=user)
        fake_req.httprequest.headers = {}
        with mock.patch.object(controller_module, 'request', fake_req):
            yield fake_req
