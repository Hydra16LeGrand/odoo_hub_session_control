# -*- coding: utf-8 -*-
{
    'name': 'Hub Session Control',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Contrôle et limite la durée des sessions pour les connexions OAuth via le Hub',
    'description': """
        Module compagnon de odoo_db_remote_management pour les instances clientes.
        Ce module permet de :
        - Détecter les sessions créées via le Hub centralisé.
        - Imposer une durée maximale de session.
        - Déconnecter automatiquement ces sessions.
        - Avertir les utilisateurs avant la déconnexion et proposer une prolongation.
    """,
    'author': 'Amara Baradji',
    'company': 'Amara Baradji',
    'website': "https://amara-baradji.vercel.app/",
    'depends': ['base', 'web'],
    'data': [
        'data/ir_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_hub_session_control/static/src/js/session_warning.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'auto_install': False,
    'license': 'LGPL-3',
}
