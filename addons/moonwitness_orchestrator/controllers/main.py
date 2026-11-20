# -*- coding: utf-8 -*-
from flectra import http
from flectra.http import request


class MoonwitnessOrchestratorController(http.Controller):

    def _guard(self):
        if not request.env.user.has_group('moonwitness_arsy.group_moonwitness_arsy'):
            raise http.AccessError('Orchestrator: admin only')

    @http.route('/moonwitness_orchestrator/wa_status', type='json', auth='user')
    def wa_status(self):
        self._guard()
        return request.env['moonwitness.orchestrator'].whatsapp_status()

    @http.route('/moonwitness_orchestrator/wa_qr', type='json', auth='user')
    def wa_qr(self):
        self._guard()
        return request.env['moonwitness.orchestrator'].whatsapp_qr()

    @http.route('/moonwitness_orchestrator/wa_send', type='json', auth='user')
    def wa_send(self, to, message):
        self._guard()
        return request.env['moonwitness.orchestrator'].whatsapp_send(to, message)

    @http.route('/moonwitness_orchestrator/wa_logout', type='json', auth='user')
    def wa_logout(self):
        self._guard()
        return request.env['moonwitness.orchestrator'].whatsapp_logout()
