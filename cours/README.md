# Cours — Programme

Retour à l'[accueil](../README.md) · Voir les [writeups](../writeups/README.md)

Notes de cours structurées, avec une progression du plus fondamental vers le plus appliqué.
Chaque module a son `README.md` (plan + notes) et un dossier `assets/` pour les schémas.

## Progression

| # | Module | Objectif | Statut |
| --- | --- | --- | --- |
| 01 | [Réseau — Bases](01-Reseau-Bases/README.md) | Lire, comprendre et capturer du trafic | 🚧 en cours |
| 02 | [Linux — Privilege Escalation](02-Linux-Privilege-Escalation/README.md) | Passer d'un shell utilisateur à root | 🚧 en cours |
| 03 | [Web — OWASP](03-Web-OWASP/README.md) | Identifier et exploiter les 10 risques OWASP | 🚧 en cours |

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
- Un dossier de labs jetables — jamais de test hors périmètre autorisé.
