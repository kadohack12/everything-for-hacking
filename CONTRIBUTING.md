# Contribuer

Merci de passer par ici. Ce dépôt est **ouvert aux contributions** : n'importe qui peut ajouter
un writeup. Il contient aussi des **cours protégés**, pour éviter qu'ils soient altérés au fil
des PR.

> **En bref** : sur un writeup, seuls les **flags en clair** et les **liens morts** bloquent la
> CI — le reste est conseillé. Sur `cours/`, tout est verrouillé : une PR d'un non-mainteneur
> est refusée, et le contenu est vérifié par empreinte.

| Espace | Qui peut modifier | Comment |
| --- | --- | --- |
| [`writeups/`](writeups/) | **tout le monde** | PR directe |
| [`cours/`](cours/) | mainteneurs uniquement | issue « Signaler une erreur », pas de PR |
| [`scripts/`](scripts/), [`.github/`](.github/) | PR bienvenue, relue par un mainteneur | décrire le besoin dans la PR |
| `README.md` racine | mainteneur (ou PR discutée) | issue d'abord |

Sommaire : [Sans terminal](#contribuer-en-2-minutes-sans-terminal-100--sur-githubcom) ·
[1. Récupérer](#1-récupérer-le-dépôt) · [2. Créer le writeup](#2-créer-le-writeup) ·
[3. Nommage](#3-nommage-recommandé) · [4. Frontmatter](#4-frontmatter-recommandé-alimente-lindex) ·
[5. Contenu](#5-contenu-attendu) · [6. Vérifier en local](#6-vérifier-en-local) ·
[7. Ouvrir la PR](#7-ouvrir-la-pr) · [8. Cours](#8-cours--espace-protégé) · [9. Licence](#9-licence)

## Contribuer en 2 minutes sans terminal (100 % sur GitHub.com)

Pas de `git`, pas de Python, pas d'installation : tout se fait dans le navigateur, avec un compte
GitHub gratuit.

### Créer un writeup

1. Ouvre le dossier de la plateforme :
   [Hack The Box](writeups/hackthebox/Machines/) ·
   [TryHackMe](writeups/tryhackme/Rooms/) ·
   [Hackropole](writeups/hackropole.fr/Challenges/).
2. Bouton **Add file** → **Create new file**.
3. Dans le champ du nom, tape le chemin complet — chaque `/` crée un dossier :

   ```text
   writeups/hackthebox/Machines/nom-machine/README.md
   ```

4. **Copie le modèle** : ouvre [`writeups/_template/README.md`](writeups/_template/README.md),
   clique sur **Raw**, copie tout, colle dans l'éditeur.
5. **Remplis l'en-tête** entre les deux `---` : `title`, `platform`, `category`, `difficulty`,
   `date`, `author`, et laisse `status: draft` le temps de rédiger.
6. **Commit changes** → **Create a new branch** → **Propose changes** : la PR s'ouvre toute seule.
7. La CI vérifie les flags et les liens ; un mainteneur relit et merge.

### Ajouter des captures

GitHub ne sait pas créer un dossier vide : utilise **Add file** → **Upload files**, tape
`writeups/hackthebox/Machines/nom-machine/assets/` dans le chemin, dépose tes images, puis
référence-les en relatif :

```markdown
![Scan nmap](assets/01-nmap.png)
```

Évite le glisser-déposer direct dans l'éditeur de texte : GitHub insère alors un lien vers son CDN
(`user-images.githubusercontent.com`) au lieu d'un fichier du dépôt.

### Corriger un writeup existant

Ouvre le fichier, clique sur le **crayon** (*Edit this file*), corrige, puis **Commit changes**.
Pour une faute de frappe, **Propose changes** suffit ; pour un ajout de fond, crée une branche.

### Pour les cours

`cours/` n'accepte pas de PR. Ouvre une issue
[**Améliorer un cours**](https://github.com/kadohack12/everything-for-hacking/issues/new?template=ameliorer-cours.yml) :
module, fichier, ce qui est faux, correction proposée, source.

### Et si je préfère l'outillage local ?

Voir [2. Créer le writeup](#2-créer-le-writeup) : `python3 scripts/new_writeup.py` fait le travail
(dossier, kebab-case, frontmatter pré-rempli).

## 1. Récupérer le dépôt

```bash
git clone https://github.com/<ton-login>/everything-for-hacking.git
cd everything-for-hacking
git remote add upstream https://github.com/kadohack12/everything-for-hacking.git
git switch -c writeup/hackthebox/nom-machine
```

Une branche par writeup, nommée `writeup/<plateforme>/<nom>`. Pas de commit direct sur `main`.

## 2. Créer le writeup

Avec l'assistant — il pose les questions, convertit le nom en kebab-case et pré-remplit le
frontmatter (date du jour, auteur, `status: draft`) :

```bash
python3 scripts/new_writeup.py
```

Ou à la main :

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

## 3. Nommage (recommandé)

- Dossier en **kebab-case minuscule** : `blue`, `a-laise`, `pwn-me-01`.
  Pas d'espace, pas d'accent, pas de majuscule, pas d'underscore : ces noms deviennent des URLs.
- Un dossier = **un** writeup = **un** `README.md`.
- Les captures vont dans `assets/`, nommées et numérotées : `01-nmap.png`, `02-exploit.png`.
- Pas de fichier en vrac à la racine d'un writeup (scripts, dumps) : mets-les dans `assets/`
  seulement s'ils sont utiles au lecteur, sinon décris-les en texte.

## 4. Frontmatter (recommandé, alimente l'index)

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

| Champ | Conseillé | Format | Remarque |
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
- Un `draft` n'apparaît pas dans l'index. La CI le signale sans bloquer : c'est à toi de ne pas
  demander le merge tant que la machine est active.
- Hackropole : les épreuves sont archivées et publiques, tu peux publier directement.

Ces champs ne sont pas vérifiés de façon bloquante : si l'un manque, le writeup reste accepté
mais s'affiche mal (ou pas) dans l'index. Le mainteneur peut compléter au merge.

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
python3 scripts/check_secrets.py       # BLOQUANT : flags en clair, clés, .ovpn
python3 scripts/check_links.py         # BLOQUANT : liens relatifs et images
python3 scripts/check_frontmatter.py   # conseils : structure et frontmatter
python3 scripts/check_drafts.py        # conseils : liste les brouillons
python3 scripts/update_index.py        # régénère les tableaux d'index (à committer)
python3 scripts/new_writeup.py         # assistant : crée un dossier de writeup complet
```

Seuls les deux premiers bloquent une PR. L'index est régénéré depuis le frontmatter : si tu
oublies `update_index.py`, la CI te le signale sans refuser la PR, et le workflow
`update-index.yml` le régénère automatiquement sur `main` après le merge.

Un faux positif du scanner ? Ajoute `secret-scan:ignore` en commentaire sur la ligne concernée.

## 7. Ouvrir la PR

```bash
git add writeups/ && git commit -m "feat(writeups): HTB Blue (SMB, EternalBlue)"
git push -u origin writeup/hackthebox/nom-machine
```

- **Une PR = un writeup** (ou une correction ciblée).
- Remplis le modèle de PR : la checklist évite les allers-retours.
- La CI doit être verte sur les contrôles bloquants (secrets, liens). Les jobs « conseil »
  (structure, brouillons, index) peuvent rester en avertissement sans empêcher le merge.
- Le job « Cours protégés » ne concerne que `cours/`, que tu ne touches pas.
- Review : je relis, je peux demander des précisions ou reformuler. Le merge reste manuel.

**Ce qui fait refuser une PR** : flag en clair, images manquantes, dossier mal nommé, frontmatter
incomplet, index non régénéré, writeup d'une machine encore active, contenu copié sans source,
ou modification de `cours/`.

## 8. Cours : espace protégé

`cours/` est un support pédagogique : il doit rester cohérent, sourcé et sans régression.
C'est pourquoi il n'est **pas ouvert aux PR directes**.

- Pour proposer une correction : ouvre une issue **« Améliorer un cours »** en précisant le
  fichier, ce qui est faux, la correction et une source.
- Le mainteneur intègre la modification lui-même (et te crédite si la contribution est
  substantielle).
- La CI bloque toute PR qui modifie `cours/` sans être d'un mainteneur (liste :
  [`.github/MAINTAINERS`](.github/MAINTAINERS)), et [`.github/CODEOWNERS`](.github/CODEOWNERS)
  demande la revue du mainteneur.
- Chaque fichier de `cours/` est vérifié par empreinte (`cours/MANIFEST.sha256`) : une
  modification silencieuse est détectée, même par un mainteneur. Après une modification
  volontaire, le manifeste doit être régénéré : `python3 scripts/check_cours.py --update`.
- La structure des modules est contrôlée : `NN-Nom-Du-Module`, `README.md` avec `## Objectifs`
  et `## Plan`, module listé dans le programme, extensions autorisées (`.md`, images, `.pdf`).

## 9. Licence

En contribuant, tu acceptes que ton contenu soit publié sous
[CC BY-SA 4.0](LICENSE), comme le reste du dépôt : attribution obligatoire, partage à
l'identique. Tu garantis être l'auteur du contenu ou disposer des droits nécessaires.
