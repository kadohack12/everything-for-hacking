# Contribuer

Merci de passer par ici. Ce dépôt est **ouvert aux contributions** : n'importe qui peut ajouter
un writeup. Il contient aussi des **cours protégés**, pour éviter qu'ils soient altérés au fil
des PR.

| Espace | Qui peut modifier | Comment |
| --- | --- | --- |
| [`writeups/`](writeups/) | **tout le monde** | PR directe |
| [`cours/`](cours/) | mainteneurs uniquement | issue « Signaler une erreur », pas de PR |
| [`scripts/`](scripts/), [`.github/`](.github/) | PR bienvenue, relue par un mainteneur | décrire le besoin dans la PR |
| `README.md` racine | mainteneur (ou PR discutée) | issue d'abord |

Sommaire : [1. Récupérer](#1-récupérer-le-dépôt) · [2. Créer le writeup](#2-créer-le-writeup) ·
[3. Nommage](#3-nommage-règles-strictes) · [4. Frontmatter](#4-frontmatter-obligatoire) ·
[5. Contenu](#5-contenu-attendu) · [6. Vérifier en local](#6-vérifier-en-local) ·
[7. Ouvrir la PR](#7-ouvrir-la-pr) · [8. Cours](#8-cours--espace-protégé) · [9. Licence](#9-licence)

## 1. Récupérer le dépôt

```bash
git clone https://github.com/<ton-login>/all-tout-hack.git
cd all-tout-hack
git remote add upstream https://github.com/kadohack12/all-tout-hack.git
git switch -c writeup/hackthebox/nom-machine
```

Une branche par writeup, nommée `writeup/<plateforme>/<nom>`. Pas de commit direct sur `main`.

## 2. Créer le writeup

```bash
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
```

Le chemin dépend de la plateforme :

| Plateforme | Chemin | `platform` |
| --- | --- | --- |
| Hack The Box | `writeups/hackthebox/Machines/<nom>/` | `Hack The Box` |
| TryHackMe | `writeups/tryhackme/Rooms/<nom>/` | `TryHackMe` |
| Hackropole (FCSC) | `writeups/hackropole.fr/Challenges/<catégorie>/<nom>/` | `Hackropole` |

Catégories Hackropole : `crypto`, `web`, `reverse`, `pwn`, `forensics`, `hardware`, `misc`.
Pour une nouvelle plateforme, crée `writeups/<plateforme>/<type>/<nom>/` et signale-le dans la PR
(l'index utilisera des colonnes par défaut).

## 3. Nommage (règles strictes)

- Dossier en **kebab-case minuscule** : `blue`, `a-laise`, `pwn-me-01`.
  Pas d'espace, pas d'accent, pas de majuscule, pas d'underscore : ces noms deviennent des URLs.
- Un dossier = **un** writeup = **un** `README.md`.
- Les captures vont dans `assets/`, nommées et numérotées : `01-nmap.png`, `02-exploit.png`.
- Pas de fichier en vrac à la racine d'un writeup (scripts, dumps) : mets-les dans `assets/`
  seulement s'ils sont utiles au lecteur, sinon décris-les en texte.

## 4. Frontmatter obligatoire

En tête du `README.md`, entre deux `---` :

```yaml
---
title: "Blue"
platform: "Hack The Box"
category: "Machine"
os: "Windows"
difficulty: "Easy"
date: 2026-05-01
author: "Ton pseudo"
author_github: "ton-login"
tags: [smb, eternalblue, metasploit]
status: published
---
```

| Champ | Obligatoire | Format | Remarque |
| --- | --- | --- | --- |
| `title` | oui | texte | nom officiel de la machine / du challenge |
| `platform` | oui | texte | doit correspondre au dossier (tableau ci-dessus) |
| `category` | oui | texte | `Machine`, `Room`, ou la catégorie Hackropole |
| `difficulty` | oui | texte | `Intro`, `Easy`, `Medium`, `Hard`, `Insane`… |
| `date` | oui | `AAAA-MM-JJ` | date de rédaction / publication du writeup |
| `author` | oui | texte | ton nom ou pseudo |
| `author_github` | non | login | ajoute un lien vers ton profil dans l'index |
| `tags` | non | `[a, b]` | techniques clés |
| `status` | oui | `draft` \| `published` | voir ci-dessous |

**`draft` ou `published` ?**

- `published` : le contenu est publiable (épreuve terminée, machine retirée de l'actif).
- `draft` : travail en cours, ou **machine encore active** sur la plateforme — publier son writeup
  pendant qu'elle est active casse le jeu pour les autres.
- Un `draft` peut vivre dans une PR (la CI avertit sans bloquer), mais **`main` refuse les
  brouillons** : ne demande le merge qu'une fois le writeup passé en `published`.
- Hackropole : les épreuves sont archivées et publiques, tu peux publier directement.

## 5. Contenu attendu

Sections du modèle : **TL;DR**, Reconnaissance, Énumération, Accès initial, Élévation de
privilèges, Flags, Leçons.

- Des **commandes complètes et copiables**, pas des extraits tronqués.
- Des captures **versionnées** dans `assets/` (pas de lien vers un hébergeur externe).
- Le **raisonnement**, pas seulement la solution : ce que tu as tenté, ce qui a échoué.
- **Aucun flag en clair** : écris `FCSC{...}`, `HTB{...}`, `THM{...}`. La CI refuse les flags
  complets (le dépôt ne doit pas apparaître dans les dumps de flags).
- **Aucune cible réelle**, aucun scan hors périmètre, aucune donnée personnelle.
- Un ton factuel ; les corrections de style peuvent être demandées en review.

## 6. Vérifier en local

Python 3.9+ suffit, aucune dépendance à installer.

```bash
python3 scripts/check_frontmatter.py   # structure + frontmatter
python3 scripts/check_links.py         # liens relatifs et images
python3 scripts/check_secrets.py       # flags en clair, clés, .ovpn
python3 scripts/update_index.py        # régénère les tableaux d'index (à committer)
python3 scripts/check_drafts.py        # liste les brouillons (doit être vide si tu publies)
```

`update_index.py` est **obligatoire** : l'index est généré depuis le frontmatter, une PR qui
l'oublie fait échouer la CI (`--check`).

Un faux positif du scanner ? Ajoute `secret-scan:ignore` en commentaire sur la ligne concernée.

## 7. Ouvrir la PR

```bash
git add writeups/ && git commit -m "feat(writeups): HTB Blue (SMB, EternalBlue)"
git push -u origin writeup/hackthebox/nom-machine
```

- **Une PR = un writeup** (ou une correction ciblée).
- Remplis le modèle de PR : la checklist évite les allers-retours.
- La CI doit être verte : structure, liens, secrets, index. Le job « Cours protégés » ne concerne
  que `cours/`, que tu ne touches pas.
- Review : je relis, je peux demander des précisions ou reformuler. Le merge reste manuel.

**Ce qui fait refuser une PR** : flag en clair, images manquantes, dossier mal nommé, frontmatter
incomplet, index non régénéré, writeup d'une machine encore active, contenu copié sans source,
ou modification de `cours/`.

## 8. Cours : espace protégé

`cours/` est un support pédagogique : il doit rester cohérent, sourcé et sans régression.
C'est pourquoi il n'est **pas ouvert aux PR directes**.

- Pour proposer une correction : ouvre une issue **« Signaler une erreur »** en précisant le
  fichier, ce qui est faux, la correction et une source.
- Le mainteneur intègre la modification lui-même (et te crédite si la contribution est
  substantielle).
- La CI bloque toute PR qui modifie `cours/` sans être d'un mainteneur (liste :
  [`.github/MAINTAINERS`](.github/MAINTAINERS)), et [`.github/CODEOWNERS`](.github/CODEOWNERS)
  demande la revue du mainteneur.

## 9. Licence

En contribuant, tu acceptes que ton contenu soit publié sous
[CC BY-SA 4.0](LICENSE), comme le reste du dépôt : attribution obligatoire, partage à
l'identique. Tu garantis être l'auteur du contenu ou disposer des droits nécessaires.
