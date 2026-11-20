# Writeups & Cours — Cybersécurité

[![Writeups](https://img.shields.io/badge/writeups-CTF%20%26%20machines-blue)](writeups/README.md)
[![Cours](https://img.shields.io/badge/cours-fondamentaux-green)](cours/README.md)
[![Licence](https://img.shields.io/badge/licence-CC%20BY--SA%204.0-lightgrey)](https://creativecommons.org/licenses/by-sa/4.0/deed.fr)

Ce dépôt rassemble mes notes de terrain en cybersécurité :

- **[`writeups/`](writeups/README.md)** — solutions détaillées de machines et de challenges CTF.
- **[`cours/`](cours/README.md)** — notes de cours structurées : réseau, Linux, web.

Tout est en Markdown, lisible directement sur GitHub, et les captures d'écran sont versionnées
à côté de chaque writeup (pas de lien externe qui meurt).

## Sommaire

| Dossier | Contenu | Index |
| --- | --- | --- |
| [`writeups/`](writeups/README.md) | Writeups par plateforme | [writeups/README.md](writeups/README.md) |
| [`writeups/hackthebox/`](writeups/hackthebox/) | Machines Hack The Box | [Machines/](writeups/hackthebox/Machines/) |
| [`writeups/tryhackme/`](writeups/tryhackme/) | Rooms TryHackMe | [Rooms/](writeups/tryhackme/Rooms/) |
| [`writeups/hackropole.fr/`](writeups/hackropole.fr/) | Challenges Hackropole (FCSC) | [Challenges/](writeups/hackropole.fr/Challenges/) |
| [`cours/`](cours/README.md) | Programme et notes de cours | [cours/README.md](cours/README.md) |

## Arborescence

```text
.
├── README.md                  # ce fichier
├── writeups/
│   ├── README.md              # sommaire de tous les writeups
│   ├── _template/             # modèle à copier pour un nouveau writeup
│   ├── hackthebox/
│   │   └── Machines/
│   │       └── NomMachine/
│   │           ├── README.md  # le writeup
│   │           └── assets/    # captures (nmap, exploit, flags…)
│   ├── tryhackme/
│   │   └── Rooms/
│   │       └── NomRoom/
│   │           ├── README.md
│   │           └── assets/
│   └── hackropole.fr/
│       └── Challenges/
│           ├── crypto/  web/  reverse/  pwn/
│           └── forensics/  hardware/  misc/
├── cours/
│   ├── README.md              # programme du cours
│   ├── 01-Reseau-Bases/
│   ├── 02-Linux-Privilege-Escalation/
│   └── 03-Web-OWASP/
├── scripts/                   # automatisations (Python, sans dépendance)
│   ├── update_index.py        # régénère les tableaux d'index
│   ├── check_links.py         # liens relatifs et images
│   ├── check_secrets.py       # flags en clair et credentials
│   ├── check_drafts.py        # writeups non publiés
│   └── writeups_lib.py        # code partagé
├── .github/workflows/ci.yml   # CI : liens, secrets, brouillons, index
└── LICENSE                    # CC BY-SA 4.0
```

## Conventions

- Un writeup = un dossier, avec **un seul** `README.md` et un dossier `assets/`.
- Noms de dossiers et de fichiers : **minuscules, sans accents, sans espaces** (`NomMachine` garde la casse
  officielle de la plateforme pour rester reconnaissable).
- Captures nommées et numérotées : `01-nmap-scan.png`, `02-login-bypass.png`…
- Un en-tête YAML en haut de chaque writeup (`platform`, `difficulty`, `os`, `tags`, `status`) pour pouvoir
  générer un site statique plus tard sans retoucher le contenu.
- Statut : `draft` → `published`. Les writeups publiés sont listés dans les tableaux de [`writeups/README.md`](writeups/README.md).

## Nouveau writeup en 30 secondes

```bash
cp -r writeups/_template writeups/hackthebox/Machines/NomMachine
$EDITOR writeups/hackthebox/Machines/NomMachine/README.md
python3 scripts/update_index.py    # publie le writeup dans les index
```

## Vérifications automatiques

La CI (`.github/workflows/ci.yml`) tourne sur chaque push et PR vers `main` :

| Contrôle | Ce qui est vérifié | En local |
| --- | --- | --- |
| Liens & images | chaque lien relatif et image locale existe (hors `_template/`) | `python3 scripts/check_links.py` |
| Flags & secrets | aucun `HTB{…}`, `THM{…}`, `FCSC{…}`, `CTF{…}`, clé privée ou `.ovpn` | `python3 scripts/check_secrets.py` |
| Writeups publiés | aucun `status: draft` sur `main` (avertissement en PR) | `python3 scripts/check_drafts.py` |
| Index à jour | les tableaux ont été régénérés | `python3 scripts/update_index.py --check` |

Les scripts n'utilisent que la bibliothèque standard Python 3. Un faux positif se neutralise
avec un commentaire `secret-scan:ignore` sur la ligne concernée.

## Outils utilisés

`nmap` · `ffuf` / `gobuster` · `Burp Suite` · `sqlmap` · `netcat` · `Ghidra` · `pwntools` ·
`hashcat` · `Wireshark` · `BloodHound` · `linPEAS` / `winPEAS`

## Éthique

Tous les tests ont été réalisés sur des environnements **légaux** : machines louées sur des plateformes
d'entraînement, labs dédiés ou challenges dont les organisateurs autorisent la publication.
Aucune cible réelle, aucun système tiers. Le contenu est publié à but pédagogique.

> Les flags complets peuvent être tronqués (`FCSC{...}`) pour éviter le spoiling direct.

## Licence

Contenu sous [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) sauf mention contraire —
texte intégral dans [`LICENSE`](LICENSE). Réutilisation libre avec attribution et partage à l'identique.
