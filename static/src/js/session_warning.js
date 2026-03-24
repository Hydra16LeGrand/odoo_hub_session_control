/** @odoo-module **/

import { session } from "@web/session";
import { browser } from "@web/core/browser/browser";

/**
 * Hub Session Warning
 *
 * Double vérification :
 *  1. Durée max de session (ex: 45 min)
 *  2. Couvre-feu horaire (ex: 18h00)
 * La popup apparaît `warnBefore` secondes avant le PREMIER des deux déclencheurs.
 */

if (session.hub_managed) {

    let loginTime = session.hub_login_time;
    let maxDuration = session.session_max_duration;
    let warnBefore = session.session_warn_before || 300;
    let disconnectTs = session.session_disconnect_ts || 0;   // timestamp UTC, 0 = désactivé
    let extCount = session.hub_extensions_count || 0;
    let dismissed = false;

    // ── Helpers ─────────────────────────────────────────────────────
    const fmtTime = (s) => {
        const m = Math.floor(s / 60);
        const sec = Math.floor(s % 60);
        return `${m}:${sec < 10 ? "0" : ""}${sec}`;
    };

    const removeModal = () => {
        const el = document.getElementById("hub-session-warning-modal");
        if (el) el.remove();
    };

    /** Calcule le temps restant en secondes (min entre durée et couvre-feu). */
    const getTimeLeft = () => {
        const now = Date.now() / 1000;
        const byDuration = (loginTime + maxDuration) - now;
        const byCurfew = disconnectTs ? (disconnectTs - now) : Infinity;
        return Math.min(byDuration, byCurfew);
    };

    /** Détermine la raison de la déconnexion la plus proche. */
    const getExpiryReason = () => {
        const now = Date.now() / 1000;
        const byDuration = (loginTime + maxDuration) - now;
        const byCurfew = disconnectTs ? (disconnectTs - now) : Infinity;
        return byCurfew <= byDuration ? "couvre-feu" : "durée";
    };

    // ── Popup d'avertissement ───────────────────────────────────────
    const showWarning = (timeLeft) => {
        const existing = document.getElementById("hub-session-warning-modal");
        if (existing) {
            const span = document.getElementById("hub-session-time-left");
            if (span) span.textContent = fmtTime(timeLeft);
            // Mettre à jour le label de raison
            const reasonEl = document.getElementById("hub-session-reason");
            if (reasonEl) reasonEl.textContent = getExpiryReason() === "couvre-feu"
                ? "Raison : couvre-feu horaire" : "Raison : durée maximale";
            return;
        }

        const extensionsLeft = 2 - extCount;
        const reason = getExpiryReason();
        const reasonLabel = reason === "couvre-feu"
            ? "Raison : couvre-feu horaire" : "Raison : durée maximale";

        const html = `
        <div id="hub-session-warning-modal"
             style="position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:99999;
                    display:flex;align-items:center;justify-content:center;">
          <div style="background:#fff;padding:28px 32px;border-radius:12px;
                      box-shadow:0 12px 32px rgba(0,0,0,.25);max-width:420px;
                      text-align:center;font-family:system-ui,sans-serif;position:relative;">

            <button id="btn-hub-dismiss"
                    style="position:absolute;top:8px;right:12px;background:none;border:none;
                           font-size:1.4rem;color:#999;cursor:pointer;line-height:1;"
                    title="Ignorer">&times;</button>

            <h3 style="color:#c0392b;margin:0 0 12px;font-size:1.4rem;">
                Session expirant bientot
            </h3>
            <p style="font-size:1.05rem;margin-bottom:8px;">
                Votre session Hub se terminera dans
                <strong id="hub-session-time-left"
                        style="color:#c0392b;font-size:1.25rem;">
                    ${fmtTime(timeLeft)}
                </strong>.
            </p>
            <p id="hub-session-reason"
               style="color:#e67e22;font-size:.85rem;margin-bottom:12px;font-style:italic;">
                ${reasonLabel}
            </p>
            <p style="color:#777;font-size:.85rem;margin-bottom:20px;">
                Prolongations utilisées : ${extCount} / 2
            </p>
            <div style="display:flex;gap:10px;">
              <button id="btn-hub-logout"
                      style="flex:1;padding:10px;background:#f1f1f1;border:1px solid #ccc;
                             border-radius:6px;cursor:pointer;font-weight:600;color:#333;">
                  Se déconnecter
              </button>
              <button id="btn-hub-extend"
                      style="flex:1;padding:10px;border:none;border-radius:6px;
                             font-weight:600;color:#fff;
                             background:${extensionsLeft ? "#2980b9" : "#999"};
                             cursor:${extensionsLeft ? "pointer" : "not-allowed"};"
                      ${extensionsLeft ? "" : "disabled"}>
                  Prolonger la session
              </button>
            </div>
          </div>
        </div>`;

        document.body.insertAdjacentHTML("beforeend", html);

        document.getElementById("btn-hub-dismiss").addEventListener("click", () => {
            dismissed = true;
            removeModal();
        });

        document.getElementById("btn-hub-logout").addEventListener("click", () => {
            browser.location.href = "/web/session/logout?redirect=/web/login";
        });

        document.getElementById("btn-hub-extend").addEventListener("click", async () => {
            if (!extensionsLeft) return;
            try {
                const resp = await fetch("/hub/session/extend", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: {} }),
                });
                const data = await resp.json();

                if (data.result && data.result.success) {
                    loginTime = data.result.new_login_time;
                    extCount = 2 - data.result.extensions_left;
                    dismissed = false;
                    removeModal();
                } else {
                    const errMsg = data.result ? data.result.error : "Erreur inconnue";
                    alert(errMsg);
                }
            } catch (err) {
                console.error("Erreur extension session Hub", err);
            }
        });
    };

    // ── Boucle de vérification (1 s) ────────────────────────────────
    setInterval(() => {
        const timeLeft = getTimeLeft();

        if (timeLeft <= 0) {
            browser.location.href = "/web/session/logout?redirect=/web/login";
        } else if (timeLeft <= warnBefore && !dismissed) {
            showWarning(timeLeft);
        } else {
            removeModal();
        }
    }, 1000);
}
