<div align="center">

# Everything For Hacking

**Writeups CTF et cours de cybersécurité, en français, en Markdown, sans paywall.**

[![Site](https://img.shields.io/badge/site-en%20ligne-2ea44f?logo=materialformkdocs&logoColor=white)](https://kadohack12.github.io/everything-for-hacking/)
[![CI](https://github.com/kadohack12/everything-for-hacking/actions/workflows/ci.yml/badge.svg)](https://github.com/kadohack12/everything-for-hacking/actions/workflows/ci.yml)
[![Writeups](https://img.shields.io/badge/writeups-83-blue)](writeups/README.md)
[![Cours](https://img.shields.io/badge/cours-5%20modules-orange)](cours/README.md)
[![Licence](https://img.shields.io/badge/licence-CC%20BY--SA%204.0-lightgrey)](LICENSE)
[![PRs](https://img.shields.io/badge/PRs-bienvenues-brightgreen)](CONTRIBUTING.md)

[**Parcourir le site**](https://kadohack12.github.io/everything-for-hacking/) ·
[**Writeups**](writeups/README.md) ·
[**Cours**](cours/README.md) ·
[**Ressources**](RESSOURCES.md) ·
[**Contribuer**](CONTRIBUTING.md)

</div>

> **TL;DR (EN)** — 83 French CTF writeups (TryHackMe, Hackropole/FCSC, King of the Hill, VulnHub,
> PortSwigger, PicoCTF) and 5 structured courses (networking & Wireshark, Linux privilege
> escalation, OWASP Top 10, reverse engineering CLI, pwntools). Plain Markdown, auto-indexed,
> CI-checked. Contributions welcome.

## Pourquoi ce dépôt

La plupart des writeups sont des captures d'écran suivies d'un `cat flag.txt`. Ici, chaque writeup
explique **le raisonnement** : pourquoi ce port, pourquoi cette hypothèse, pourquoi ça a échoué.
Les cours, eux, sont écrits pour être **rejoués** : chaque commande a été exécutée avant d'être
publiée, et les sorties affichées sont les vraies.

Trois principes :

- **reproductible** — commandes complètes, versions, sorties réelles ;
- **honnête** — ce qui n'a pas marché est écrit aussi ;
- **accessible** — tout est en Markdown, lisible sur GitHub comme sur le site, sans compte.

## Ce que tu trouveras

| Section | Contenu | Volume |
| --- | --- | --- |
| [TryHackMe](writeups/tryhackme/README.md) | Rooms guidées, dont un **King of the Hill** avec la partie défensive | 3 rooms |
| [Hackropole / FCSC](writeups/hackropole.fr/README.md) | Challenges crypto, web, reverse, pwn, forensics | 12 challenges |
| [Autres plateformes](writeups/autres/README.md) | VulnHub, PortSwigger, PicoCTF, OverTheWire, CTFs (dont hackerlab Bénin 2026) | 68 challenges |
| [Hack The Box](writeups/hackthebox/) | Section ouverte : **la place est libre** | 0 machine |
| [Cours](cours/README.md) | Réseau (11 chapitres), Linux privesc, OWASP, reverse CLI, pwntools | 5 modules |

## À la une

- **[panda — King of the Hill (TryHackMe)](writeups/tryhackme/Rooms/panda/)** — RCE web, `sudo ftp`,
  puis toute la défense : `king.txt` en bind-mount read-only, cron root piégé corrigé, PwnKit bloqué.
- **[Réseau : les bases](cours/01-Reseau-Bases/README.md)** — 11 chapitres, du modèle OSI à
  Wireshark, avec captures ARP, DHCP, TCP, DNS, TLS et labs exécutés.
- **[Pwntools](cours/05-Pwntools/README.md)** — 10 chapitres : tubes, ELF, cyclic, ret2win,
  ret2libc, format strings, gabarit de solve.
- **[Hackropole / FCSC](writeups/hackropole.fr/README.md)** — 12 challenges résolus, du crypto au pwn.

## Démarrer

```bash
git clone https://github.com/kadohack12/everything-for-hacking.git
cd everything-for-hacking
$EDITOR writeups/tryhackme/Rooms/panda/README.md   # ou n'importe quelle page
```

Sans rien installer : le [site](https://kadohack12.github.io/everything-for-hacking/) a la recherche
intégrée, et chaque dossier se lit directement sur GitHub.

## Sommaire

| Dossier | Contenu | Index |
| --- | --- | --- |
| [`writeups/`](writeups/README.md) | Writeups par plateforme, contributions ouvertes | [writeups/README.md](writeups/README.md) |
| [`writeups/hackthebox/`](writeups/hackthebox/) | Machines Hack The Box | [Machines/](writeups/hackthebox/Machines/) |
| [`writeups/tryhackme/`](writeups/tryhackme/) | Rooms TryHackMe | [Rooms/](writeups/tryhackme/Rooms/) |
| [`writeups/hackropole.fr/`](writeups/hackropole.fr/) | Challenges Hackropole (FCSC) | [Challenges/](writeups/hackropole.fr/Challenges/) |
| [`writeups/autres/`](writeups/autres/) | PicoCTF, PortSwigger, OverTheWire, VulnHub, CTFs archivés | [autres/README.md](writeups/autres/README.md) |
| [`cours/`](cours/README.md) | Programme et notes de cours (protégé) | [cours/README.md](cours/README.md) |
| [`RESSOURCES.md`](RESSOURCES.md) | Sélection d'outils, plateformes et références externes | [RESSOURCES.md](RESSOURCES.md) |
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
│   ├── hackropole.fr/
│   │   └── Challenges/<catégorie>/<nom>/{README.md, assets/}
│   └── autres/                # PicoCTF, PortSwigger, 404CTF… (épreuves terminées)
│       └── <plateforme>/<nom-du-challenge>/{README.md, assets/}
├── cours/                     # protégé : mainteneurs uniquement
│   ├── README.md              # programme du cours
│   ├── 01-Reseau-Bases/
│   ├── 02-Linux-Privilege-Escalation/
│   ├── 03-Web-OWASP/
│   ├── 04-Reverse-Engineering-CLI/   # tout en CLI, utilisable en SSH
│   └── 05-Pwntools/
├── scripts/                   # automatisations (Python, sans dépendance)
│   ├── new_writeup.py         # assistant : crée un writeup complet
│   ├── update_index.py        # régénère les tableaux d'index
│   ├── build_docs.py          # assemble le site statique (mkdocs)
│   ├── check_frontmatter.py   # conseils : structure et frontmatter
│   ├── check_cours.py         # cours : structure + empreintes (manifeste)
│   ├── check_links.py         # liens relatifs et images
│   ├── check_secrets.py       # flags en clair et credentials
│   ├── check_drafts.py        # writeups non publiés
│   ├── check_cours_protection.py  # cours/ réservé aux mainteneurs
│   └── writeups_lib.py        # code partagé
└── .github/
    ├── workflows/ci.yml       # CI : contrôles bloquants + conseils
    ├── workflows/pages.yml    # site statique sur GitHub Pages
    ├── workflows/update-index.yml  # régénère l'index après merge
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
python3 scripts/new_writeup.py       # assistant : dossier + frontmatter pré-rempli
# ou à la main
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
python3 scripts/update_index.py      # publie le writeup dans les index
```

Sans terminal ? Tout se fait sur GitHub.com : voir
[« Contribuer en 2 minutes »](CONTRIBUTING.md#contribuer-en-2-minutes-sans-terminal-100--sur-githubcom).

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

Un septième workflow, [`update-index.yml`](.github/workflows/update-index.yml), régénère l'index
après chaque merge touchant `writeups/` : un contributeur n'a pas à y penser.

Un huitième, [`pages.yml`](.github/workflows/pages.yml), reconstruit le site statique
(mkdocs-material : recherche, navigation, `sitemap.xml`) à chaque modification de Markdown.
Prévisualisation locale :

```bash
pip install mkdocs-material
python3 scripts/build_docs.py
mkdocs serve -f build/mkdocs.yml      # http://127.0.0.1:8000
```

Les trois jobs « conseil » sont en `continue-on-error` : ils **conseillent** sans bloquer une PR.
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

## Partager

Si un writeup t'a débloqué, l'étoile coûte un clic et aide les suivants à le trouver :

[![Star](https://img.shields.io/github/stars/kadohack12/everything-for-hacking?style=social)](https://github.com/kadohack12/everything-for-hacking/stargazers)

## Mots-clés

Writeups CTF en français · Hack The Box · TryHackMe · Hackropole / FCSC · King of the Hill (KoTH) ·
VulnHub · PortSwigger · PicoCTF · OverTheWire · privilege escalation Linux · reverse engineering ·
pwn / exploitation binaire · pwntools · OWASP Top 10 · réseau et Wireshark · analyse de trames ·
nmap · ffuf · Burp Suite · Ghidra · cours de cybersécurité · apprentissage par la pratique.
