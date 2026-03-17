# -*- coding: utf-8 -*-
from odoo import models, SUPERUSER_ID
from odoo.http import request
import time
import logging
import urllib.parse
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if request.session.uid and request.session.get('hub_managed'):
            result['hub_managed'] = True
            result['hub_login_time'] = request.session.get('hub_login_time', 0)
            result['session_max_duration'] = request.session.get('session_max_duration', 45 * 60)
            result['session_warn_before'] = request.session.get('session_warn_before', 5 * 60)
            result['hub_extensions_count'] = request.session.get('hub_extensions_count', 0)
            result['session_disconnect_ts'] = request.session.get('session_disconnect_ts', 0)
        return result

    @classmethod
    def _compute_disconnect_timestamp(cls, disconnect_time_float):
        """Convertit l'heure float (ex: 18.0) en timestamp UTC du jour."""
        now = datetime.now(timezone.utc)
        hours = int(disconnect_time_float)
        minutes = int((disconnect_time_float - hours) * 60)
        target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        return target.timestamp()

    @classmethod
    def _send_hub_callback(cls, session_data, reason):
        """Envoie un callback HTTP au Hub pour notifier la déconnexion."""
        hub_url = session_data.get('hub_url', '')
        hub_log_id = session_data.get('hub_log_id', 0)
        login_time = session_data.get('hub_login_time', 0)

        if not hub_url or not hub_log_id:
            return

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
                "Callback Hub envoyé (log #%s, raison: %s, durée: %s min) → %s",
                hub_log_id, reason, duration_min, resp.status_code,
            )
        except Exception as e:
            _logger.warning("Échec callback Hub pour log #%s : %s", hub_log_id, e)

    @classmethod
    def _authenticate(cls, endpoint):
        result = super()._authenticate(endpoint)

        # ── 1. Détection initiale ──────────────────────────────────────
        if (request.session.uid
                and not request.session.get('hub_managed')
                and request.httprequest.args.get('hub_managed') == '1'):
            try:
                max_dur = int(request.httprequest.args.get('session_max_duration', 45))
                warn_before = int(request.httprequest.args.get('session_warn_before', 5))

                request.session['hub_managed'] = True
                request.session['hub_login_time'] = time.time()
                request.session['session_max_duration'] = max_dur * 60
                request.session['session_warn_before'] = warn_before * 60
                request.session['hub_extensions_count'] = 0

                # Hub callback info
                request.session['hub_url'] = request.httprequest.args.get('hub_url', '')
                request.session['hub_log_id'] = request.httprequest.args.get('hub_log_id', 0)

                # Couvre-feu horaire
                disconnect_time_str = request.httprequest.args.get('session_disconnect_time')
                if disconnect_time_str:
                    disconnect_time = float(disconnect_time_str)
                    request.session['session_disconnect_ts'] = cls._compute_disconnect_timestamp(disconnect_time)
                    _logger.info(
                        "Session Hub marquée pour UID %s (durée max : %s min, couvre-feu : %s).",
                        request.session.uid, max_dur, disconnect_time_str,
                    )
                else:
                    request.session['session_disconnect_ts'] = 0
                    _logger.info(
                        "Session Hub marquée pour UID %s (durée max : %s min).",
                        request.session.uid, max_dur,
                    )
            except Exception as e:
                _logger.warning("Erreur parsing paramètres hub_managed : %s", e)

        # ── 2. Vérification d'expiration à chaque requête ──────────────
        if (request.session.uid
                and request.session.uid != SUPERUSER_ID
                and request.session.get('hub_managed')):

            now = time.time()
            login_time = request.session.get('hub_login_time', 0)
            max_duration = request.session.get('session_max_duration', 45 * 60)
            disconnect_ts = request.session.get('session_disconnect_ts', 0)

            expired_by_duration = (now - login_time) > max_duration
            expired_by_curfew = disconnect_ts and now >= disconnect_ts

            if expired_by_duration or expired_by_curfew:
                reason = 'curfew' if expired_by_curfew else 'duration'
                _logger.info(
                    "Session Hub expirée pour UID %s (%s). Déconnexion.",
                    request.session.uid, reason,
                )
                # Envoyer le callback au Hub AVANT le logout
                cls._send_hub_callback(request.session, reason)
                request.session.logout(keep_db=True)

        return result
