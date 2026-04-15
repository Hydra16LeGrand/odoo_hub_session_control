# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestIrHttp(TransactionCase):

    def test_session_info_hub_managed(self):
        """session_info doit retourner les cles Hub quand la session est marquee."""
        # Simuler une session marquee hub_managed
        import odoo.http
        original_uid = odoo.http.request.session.uid
        odoo.http.request.session.uid = self.env.user.id
        odoo.http.request.session['hub_managed'] = True
        odoo.http.request.session['hub_login_time'] = 1234567890
        odoo.http.request.session['session_max_duration'] = 45 * 60
        odoo.http.request.session['session_warn_before'] = 5 * 60
        odoo.http.request.session['hub_extensions_count'] = 1
        odoo.http.request.session['session_disconnect_ts'] = 0
        info = self.env['ir.http'].session_info()
        self.assertTrue(info.get('hub_managed'))
        self.assertEqual(info.get('hub_login_time'), 1234567890)
        # cleanup
        del odoo.http.request.session['hub_managed']
        odoo.http.request.session.uid = original_uid
