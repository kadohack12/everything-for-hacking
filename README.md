# Everything For Hacking

[![Writeups](https://img.shields.io/badge/writeups-CTF%20%26%20machines-blue)](writeups/README.md)
[![Cours](https://img.shields.io/badge/cours-fondamentaux-green)](cours/README.md)
[![Contributions](https://img.shields.io/badge/contributions-ouvertes-brightgreen)](CONTRIBUTING.md)
[![Licence](https://img.shields.io/badge/licence-CC%20BY--SA%204.0-lightgrey)](LICENSE)

Dépôt **collaboratif** de writeups et de cours de cybersécurité :

- **[`writeups/`](writeups/README.md)** — solutions détaillées de machines et de challenges CTF,
  ouvertes à toutes les contributions : ajoute le tien, il apparaît dans l'index avec ton nom.
- **[`cours/`](cours/README.md)** — notes de cours structurées (réseau, Linux, web).
  Espace **protégé** : les corrections passent par une issue, pas par une PR.

Tout est en Markdown, lisible directement sur GitHub, et les captures d'écran sont versionnées
à côté de chaque writeup (pas de lien externe qui meurt).

## Sommaire

| Dossier | Contenu | Index |
| --- | --- | --- |
| [`writeups/`](writeups/README.md) | Writeups par plateforme, contributions ouvertes | [writeups/README.md](writeups/README.md) |
| [`writeups/hackthebox/`](writeups/hackthebox/) | Machines Hack The Box | [Machines/](writeups/hackthebox/Machines/) |
| [`writeups/tryhackme/`](writeups/tryhackme/) | Rooms TryHackMe | [Rooms/](writeups/tryhackme/Rooms/) |
| [`writeups/hackropole.fr/`](writeups/hackropole.fr/) | Challenges Hackropole (FCSC) | [Challenges/](writeups/hackropole.fr/Challenges/) |
| [`cours/`](cours/README.md) | Programme et notes de cours (protégé) | [cours/README.md](cours/README.md) |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Comment contribuer, structure, frontmatter | — |

## Arborescence

```text
.
├── README.md                  # ce fichier
├── CONTRIBUTING.md            # règles de contribution (à lire avant une PR)
├── CODE_OF_CONDUCT.md
├── LICENSE                    # CC BY-SA 4.0
├── writeups/                  # ouvert aux contributions
│   ├── README.md              # sommaire généré depuis le frontmatter
│   ├── _template/             # modèle à copier
│   ├── hackthebox/
│   │   └── Machines/<nom>/{README.md, assets/}
│   ├── tryhackme/
│   │   └── Rooms/<nom>/{README.md, assets/}
│   └── hackropole.fr/
│       └── Challenges/<catégorie>/<nom>/{README.md, assets/}
├── cours/                     # protégé : mainteneurs uniquement
│   ├── README.md              # programme du cours
│   ├── 01-Reseau-Bases/
│   ├── 02-Linux-Privilege-Escalation/
│   └── 03-Web-OWASP/
├── scripts/                   # automatisations (Python, sans dépendance)
│   ├── update_index.py        # régénère les tableaux d'index
│   ├── check_frontmatter.py   # conseils : structure et frontmatter
│   ├── check_cours.py         # cours : structure + empreintes (manifeste)
│   ├── check_links.py         # liens relatifs et images
│   ├── check_secrets.py       # flags en clair et credentials
│   ├── check_drafts.py        # writeups non publiés
│   ├── check_cours_protection.py  # cours/ réservé aux mainteneurs
│   └── writeups_lib.py        # code partagé
└── .github/
    ├── workflows/ci.yml       # CI : 6 contrôles
    ├── CODEOWNERS             # revue obligatoire sur cours/
    ├── MAINTAINERS            # logins autorisés à modifier cours/
    ├── PULL_REQUEST_TEMPLATE.md
    └── ISSUE_TEMPLATE/
```

## Conventions

Deux niveaux : ce qui **bloque** la CI, et ce qui est **conseillé** (signalé, jamais refusé).

**Bloquant**

- Aucun flag en clair (`FCSC{...}`, `HTB{...}`), aucune clé privée, aucun fichier de credentials.
- Les liens relatifs et les images locales doivent exister.
- `cours/` n'est modifiable que par un mainteneur.

**Conseillé** — la CI le signale sans bloquer la contribution

- Un writeup = un dossier avec un seul `README.md` et un dossier `assets/`.
- Dossier en kebab-case minuscule (`blue`, `a-laise`) : plus simple à citer dans une URL.
- Captures numérotées : `01-nmap-scan.png`, `02-login-bypass.png`…
- Frontmatter `title`, `platform`, `category`, `difficulty`, `date`, `author`, `status`
  (+ `author_github`, `tags`) : c'est lui qui alimente l'index et affiche ton nom.
- `status: published` quand le contenu est publiable, `draft` tant que la machine est active.
- Détail et checklist : [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Nouveau writeup en 30 secondes

```bash
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
$EDITOR writeups/hackthebox/Machines/nom-machine/README.md
python3 scripts/update_index.py      # publie le writeup dans les index
```

## Contribuer

- **Writeup** : PR directe, une par writeup, sans formalisme particulier. La structure et le
  frontmatter sont conseillés, pas imposés : [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Cours** : `cours/` est un support pédagogique protégé. Propose une correction via une issue
  « Signaler une erreur » ; la CI bloque toute PR qui touche `cours/` sans être d'un mainteneur.
- **Outillage** : les PR sur `scripts/` et `.github/` sont bienvenues, relues par un mainteneur.

## Vérifications automatiques

La CI (`.github/workflows/ci.yml`) tourne sur chaque push et PR vers `main` :

| Contrôle | Bloquant | Ce qui est vérifié | En local |
| --- | --- | --- | --- |
| Flags & secrets | **oui** | aucun `HTB{…}`, `THM{…}`, `FCSC{…}`, `CTF{…}`, clé privée ou `.ovpn` | `python3 scripts/check_secrets.py` |
| Liens & images | **oui** | chaque lien relatif et image locale existe (hors `_template/`) | `python3 scripts/check_links.py` |
| Cours protégés | **oui** (PR) | une PR ne modifie pas `cours/` hors mainteneur | `python3 scripts/check_cours_protection.py --actor <login> --base origin/main` |
| Intégrité des cours | **oui** | modules conformes + empreintes `cours/MANIFEST.sha256` | `python3 scripts/check_cours.py` |
| Structure des writeups | non | dossier, frontmatter, arborescence par plateforme | `python3 scripts/check_frontmatter.py` |
| Writeups publiés | non | liste les `status: draft` restants | `python3 scripts/check_drafts.py` |
| Index des writeups | non | les tableaux sont régénérés | `python3 scripts/update_index.py --check` |

Les trois derniers jobs sont en `continue-on-error` : ils **conseillent** sans bloquer une PR.
Pour un passage de contrôle strict avant merge, ajoute `--strict` à `check_frontmatter.py` ou
`check_drafts.py`.

Les scripts n'utilisent que la bibliothèque standard Python 3 (3.9+). Un faux positif du scanner
se neutralise avec un commentaire `secret-scan:ignore` sur la ligne concernée.

## Outils utilisés

`nmap` · `ffuf` / `gobuster` · `Burp Suite` · `sqlmap` · `netcat` · `Ghidra` · `pwntools` ·
`hashcat` · `Wireshark` · `BloodHound` · `linPEAS` / `winPEAS`

## Éthique

Tous les tests ont été réalisés sur des environnements **légaux** : machines louées sur des plateformes
d'entraînement, labs dédiés ou challenges dont les organisateurs autorisent la publication.
Aucune cible réelle, aucun système tiers. Le contenu est publié à but pédagogique.

> Les flags complets ne sont jamais recopiés (`FCSC{...}`) : la CI refuse les flags en clair, pour
> éviter le spoiling et pour ne pas apparaître dans les dumps de flags.

## Licence

Contenu sous [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr) sauf mention contraire —
texte intégral dans [`LICENSE`](LICENSE). Les contributions sont publiées sous la même licence :
attribution obligatoire, partage à l'identique.
