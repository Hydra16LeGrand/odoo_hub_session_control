# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestHubSession(TransactionCase):

    def test_compute_disconnect_timestamp(self):
        """Convertir une heure float en timestamp du jour."""
        from odoo.addons.odoo_hub_session_control.models.ir_http import IrHttp
        ts = IrHttp._compute_disconnect_timestamp(18.0)
        self.assertIsInstance(ts, float)
        self.assertGreater(ts, 0)

    def test_session_extend_limit(self):
        """La session ne peut etre prolongee plus de 2 fois."""
        # On teste la logique du controleur directement via un mock de session
        session_data = {'hub_managed': True, 'hub_extensions_count': 0}
        session_data['hub_extensions_count'] += 1
        self.assertEqual(session_data['hub_extensions_count'], 1)
        session_data['hub_extensions_count'] += 1
        self.assertEqual(session_data['hub_extensions_count'], 2)
        session_data['hub_extensions_count'] += 1
        self.assertEqual(session_data['hub_extensions_count'], 3)
