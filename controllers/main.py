# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import time
import logging

_logger = logging.getLogger(__name__)


class HubSessionController(http.Controller):

    @http.route('/hub/session/extend', type='json', auth='user')
    def extend_session(self):
        """Prolonge la session Hub (max 2 prolongations)."""
        if not request.session.get('hub_managed'):
            return {'success': False, 'error': 'Session non gérée par le Hub.'}

        ext_count = request.session.get('hub_extensions_count', 0)
        if ext_count >= 2:
            return {'success': False, 'error': 'Limite de prolongations atteinte (2/2).'}

        new_time = time.time()
        request.session['hub_login_time'] = new_time
        request.session['hub_extensions_count'] = ext_count + 1

        extensions_left = 2 - (ext_count + 1)
        _logger.info(
            "Session Hub prolongée pour UID %s (%s prolongation(s) restante(s)).",
            request.session.uid, extensions_left,
        )
        return {
            'success': True,
            'extensions_left': extensions_left,
            'new_login_time': new_time,
        }
