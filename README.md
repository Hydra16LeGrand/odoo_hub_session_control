# Odoo Hub Session Control

**[Français](#francais) | [English](#english)**

---

<a name="francais"></a>
## Français

### Résumé

Ce module compagnon s'installe sur les instances clientes pour contrôler et limiter les sessions créées depuis le Hub (`odoo_db_remote_management`). Il impose une durée maximale de connexion, un couvre-feu horaire, et notifie le Hub lors de la déconnexion.

### Fonctionnalités

- **Détection des sessions Hub** : identification des sessions créées via le Hub grâce à un paramètre `hub_managed` dans la session
- **Déconnexion automatique** : termine la session lorsque la durée maximale est atteinte ou lorsque l'heure de couvre-feu est passée
- **Avertissement utilisateur** : popup JavaScript affichée avant l'expiration, indiquant le temps restant et la raison (durée ou couvre-feu)
- **Prolongation de session** : possibilité de prolonger la session jusqu'à 2 fois via un bouton dans la popup
- **Callback vers le Hub** : notification HTTP au Hub lors de la déconnexion pour mettre à jour le journal d'accès
- **Nettoyage par cron** : tâche planifiée toutes les 5 minutes pour purger les sessions expirées en fallback

### Installation

1. Installer le module `odoo_hub_session_control` sur l'instance cliente.
2. S'assurer que `auth_oauth` est configuré pour pointer vers le Hub.
3. Aucune configuration supplémentaire n'est requise ; les paramètres sont transmis automatiquement lors de la connexion depuis le Hub.

### Architecture technique

Le module fonctionne en trois couches :

1. **Override `ir.http._authenticate`** : détecte le paramètre `hub_managed=1` dans l'URL lors de la connexion OAuth et initialise les flags de session (`session_max_duration`, `session_disconnect_ts`, `hub_log_id`, `hub_url`). À chaque requête subséquente, vérifie si la session a expiré et déclenche la déconnexion.

2. **Popup JavaScript** (`session_warning.js`) : s'exécute côté client, lit les flags depuis l'objet `session`, calcule le temps restant avant expiration, et affiche une popup d'avertissement `warn_before` secondes avant la fin. Permet de se déconnecter ou de prolonger la session.

3. **Cron `hub.session.cron`** : parcourt le session store pour identifier les sessions Hub expirées (durée ou couvre-feu), envoie le callback au Hub, et supprime la session.

### Dépendances

- [odoo_db_remote_management](https://github.com/Hydra16LeGrand/odoo_db_remote_management) (Hub) : module fournissant le mécanisme de connexion distante

---

<a name="english"></a>
## English

### Summary

This companion module is installed on client instances to control and limit sessions created from the Hub (`odoo_db_remote_management`). It enforces a maximum session duration, a curfew time, and notifies the Hub on disconnect.

### Features

- **Hub session detection**: identifies sessions created via the Hub using a `hub_managed` flag in the session
- **Auto-disconnect**: terminates the session when the maximum duration is reached or when the curfew time has passed
- **User warning**: JavaScript popup displayed before expiry, showing remaining time and reason (duration or curfew)
- **Session extension**: ability to extend the session up to 2 times via a button in the popup
- **Hub callback**: HTTP notification to the Hub on disconnect to update the access log
- **Cron cleanup**: scheduled task every 5 minutes to purge expired sessions as a fallback

### Installation

1. Install the `odoo_hub_session_control` module on the client instance.
2. Ensure `auth_oauth` is configured to point to the Hub.
3. No additional configuration is required; parameters are passed automatically when connecting from the Hub.

### Technical Architecture

The module works in three layers:

1. **`ir.http._authenticate` override**: detects the `hub_managed=1` parameter in the URL during OAuth login and initializes session flags (`session_max_duration`, `session_disconnect_ts`, `hub_log_id`, `hub_url`). On every subsequent request, it checks if the session has expired and triggers logout.

2. **JavaScript popup** (`session_warning.js`): runs client-side, reads flags from the `session` object, calculates remaining time before expiry, and displays a warning popup `warn_before` seconds before the end. Allows logout or session extension.

3. **`hub.session.cron`**: scans the session store to identify expired Hub sessions (duration or curfew), sends the callback to the Hub, and deletes the session.

### Dependencies

- [odoo_db_remote_management](https://github.com/Hydra16LeGrand/odoo_db_remote_management) (Hub): module providing the remote connection mechanism

---

## License

LGPL-3

## Author

Amara Baradji
