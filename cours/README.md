# Cours — Programme

Retour à l'[accueil](../README.md) · Voir les [writeups](../writeups/README.md)

> **Espace protégé.** Ce dossier est un support pédagogique : il n'accepte pas de PR directe.
> Une erreur, une imprécision, une source manquante ? Ouvre une issue
> **« Améliorer un cours »** : la correction est relue et intégrée par un mainteneur
> (voir [`CONTRIBUTING.md`](../CONTRIBUTING.md#8-cours--espace-protégé)).
>
> Chaque fichier est vérifié par empreinte dans [`MANIFEST.sha256`](MANIFEST.sha256) : après une
> modification volontaire, régénérer le manifeste avec `python3 scripts/check_cours.py --update`.

Notes de cours structurées, avec une progression du plus fondamental vers le plus appliqué.
Chaque module a son `README.md` (plan + notes) et un dossier `assets/` pour les schémas.

## Progression

| # | Module | Objectif | Statut |
| --- | --- | --- | --- |
| 01 | [Réseau — Bases](01-Reseau-Bases/README.md) | Lire, comprendre et capturer du trafic | 🚧 en cours |
| 02 | [Linux — Privilege Escalation](02-Linux-Privilege-Escalation/README.md) | Passer d'un shell utilisateur à root | 🚧 en cours |
| 03 | [Web — OWASP](03-Web-OWASP/README.md) | Identifier et exploiter les 10 risques OWASP | 🚧 en cours |
| 04 | [Reverse Engineering — CLI](04-Reverse-Engineering-CLI/README.md) | Comprendre un binaire inconnu, sans interface graphique | 🚧 en cours |

Légende : 🚧 en cours · ✅ terminé · ⬜ à venir

## Méthode de travail

1. **Théorie courte** — une notion, un schéma, un exemple.
2. **Pratique** — un lab par chapitre (VM locale, Docker, ou plateforme d'entraînement).
3. **Trace écrite** — commandes, captures, ce qui a coincé.
4. **Révision** — fiche de synthèse en fin de module.

## Arborescence d'un module

```text
0X-Nom-Module/
├── README.md      # plan du module + notes
└── assets/        # schémas, captures
```

## Prérequis généraux

- Une VM Linux (Debian/Parrot/Kali) et une VM Windows pour les labs croisés.
- `Wireshark`, `nmap`, `netcat`, `curl`, `Burp Suite Community`.
- Pour le module 04 : `binutils`, `gdb`, `strace`, `ltrace`, `radare2` — tout en ligne de
  commande, utilisable en SSH (voir la boîte à outils du [module](04-Reverse-Engineering-CLI/README.md#boîte-à-outils-cli)).
- Un dossier de labs jetables — jamais de test hors périmètre autorisé.
