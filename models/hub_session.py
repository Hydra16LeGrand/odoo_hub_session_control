# -*- coding: utf-8 -*-
from odoo import models, api
import time
import logging

_logger = logging.getLogger(__name__)


class HubSessionCron(models.AbstractModel):
    _name = 'hub.session.cron'
    _description = 'Cron de nettoyage des sessions Hub'

    @api.model
    def _send_hub_callback(self, session_data, reason):
        """Envoie un callback HTTP au Hub pour signaler la déconnexion."""
        hub_url = session_data.get('hub_url', '')
        hub_log_id = session_data.get('hub_log_id', 0)
        login_time = session_data.get('hub_login_time', 0)

        if not hub_url or not hub_log_id:
            return False

        duration_min = int((time.time() - login_time) / 60) if login_time else 0

        try:
            import requests as http_requests
            resp = http_requests.post(
                f"{hub_url}/hub/session/disconnect_callback",
                json={
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'log_id': int(hub_log_id),
                        'reason': reason,
                        'session_duration_minutes': duration_min,
                    },
                },
                timeout=10,
            )
            _logger.info(
                "Callback Hub envoyé (log #%s, raison: %s) → HTTP %s",
                hub_log_id, reason, resp.status_code,
            )
            return resp.status_code == 200
        except Exception as e:
            _logger.warning("Échec callback Hub pour log #%s : %s", hub_log_id, e)
            return False

    @api.model
    def cleanup_expired_hub_sessions(self):
        """Parcourt les sessions via le session store pour purger celles expirées."""
        try:
            from odoo.http import root
            session_store = getattr(root, 'session_store', None)
        except Exception:
            session_store = None

        if not session_store:
            _logger.warning("Session store introuvable. Nettoyage impossible.")
            return

        now = time.time()
        disconnected_count = 0

        try:
            session_ids = list(session_store.list())
        except Exception as e:
            _logger.error("Impossible de lister les sessions : %s", e)
            return

        for session_id in session_ids:
            try:
                session = session_store.get(session_id)
                if not session or not session.get('hub_managed'):
                    continue

                login_time = session.get('hub_login_time', 0)
                max_duration = session.get('session_max_duration', 45 * 60)
                disconnect_ts = session.get('session_disconnect_ts', 0)

                expired_by_duration = (now - login_time) > max_duration
                expired_by_curfew = disconnect_ts and now >= disconnect_ts

                if expired_by_duration or expired_by_curfew:
                    reason = 'curfew' if expired_by_curfew else 'duration'

                    # Callback vers le Hub (centralisé)
                    self._send_hub_callback(session, reason)

                    # Suppression de la session
                    session_store.delete(session)
                    disconnected_count += 1
            except Exception as e:
                _logger.warning("Erreur session %s : %s", session_id, e)

        if disconnected_count:
            _logger.info(
                "Cron Hub : %s session(s) expirée(s) nettoyée(s).",
                disconnected_count,
            )
