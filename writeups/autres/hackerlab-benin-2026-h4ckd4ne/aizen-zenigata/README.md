---
title: "AIZEN · Zenigata"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/aizen/zenigata/writeup-zenigata.md"
license: "CC BY-SA 4.0"
status: published
---

# Write-up — Zenigata (Forensic Recovery, Vantage Hosting / BOREALIS)

## Objectif

> Lors de l'infiltration du data center Vantage Hosting à Mirova (zone franche
> de Kaltyr), l'équipe terrain a récupéré l'image disque d'un poste de travail
> abandonné dans la salle serveur. L'analyse de ce disque doit permettre de
> déterminer l'origine réelle du data center et de ses opérateurs.

**200 pts** — challenge `Zenigata`, catégorie web (aizen), sous-série « opération
AIZEN ».

Il ne s'agit pas d'exploiter un service, mais de mener une analyse forensique
sur l'image d'un poste de travail afin d'identifier qui est réellement derrière
le data center « Vantage Hosting », et de retrouver le secret associé.

## Instance

| Champ | Valeur |
| --- | --- |
| Cible | `172.28.34.2:8080` — Forensic Recovery |
| Service | SimpleHTTP/0.6 Python/3.11.18, listing de répertoire |

Le serveur expose un seul fichier :

```text
http://172.28.34.2:8080/
    operator-ws.tar.gz
```

## Reconnaissance

Téléchargement et inspection de l'archive :

```bash
curl -sS -o operator-ws.tar.gz http://172.28.34.2:8080/operator-ws.tar.gz
file operator-ws.tar.gz            # gzip, taille décompressée ~215 Ko
shasum -a 256 operator-ws.tar.gz   # 5c4b6654a980a501...
tar tzvf operator-ws.tar.gz
```

L'archive contient le répertoire personnel d'un opérateur (`operator-ws/`),
avec notamment :

- `.ssh/` : `id_ed25519` (+ `.pub`), `id_ed25519_mon` (clé de monitoring),
  `config`, `authorized_keys`, `known_hosts` ;
- `.bash_history` (6 087 octets) ;
- `Documents/` : `maintenance-q3.txt`, `notes-personnelles.txt`,
  `checklist-reseau.txt` ;
- `scripts/` : `monitor-bandwidth.sh`, `check-raid.sh`, `backup-daily.sh` ;
- `work/vh-infra/` : un dépôt git d'infrastructure (ansible, docker, monitoring) ;
- `.mozilla/firefox/…/places.sqlite` (historique du navigateur).

## Indices d'origine — la façade

Le dépôt `work/vh-infra/.git` raconte une histoire propre :

```bash
git log --oneline --all
# 5099ed9 add log rotation script
# 9de3d71 add alerting rules for node monitoring
# efffb43 add prometheus monitoring config
# d07e6c8 add portal and nginx composition
# f32e27f initial infrastructure setup
```

Tous les commits sont signés `admin <admin@vantagehosting.kl>` : la couverture
commerciale « Vantage Hosting ». L'`.ssh/config` et `known_hosts` ne montrent
que des machines de cette couverture (`203.0.113.0/24`) et deux relais
(`nrv-relay-01/02`). C'est l'image que l'opération veut laisser voir.

## Le basculement : objets git inatteignables

Un `git log` ne montre que les commits référencés. Le vrai signal se trouve
dans les objets présents dans `.git/objects` mais plus rattachés à aucune
branche :

```bash
git fsck --full --unreachable --no-reflogs
# objet blob     inatteignable 40d9829f... (op-briefing.gpg)
# objet tree     inatteignable 46493a8c...
# objet blob     inatteignable 8e289d10... (seed-database.py)
# objet commit   inatteignable 16a1bec9...
# objet blob     inatteignable 17f13deb... (.env)
# objet tree     inatteignable 6da6920f...
# objet commit   inatteignable bdbad9ef...
```

Deux commits cachés :

```bash
git cat-file -p 16a1bec9ed764116af47cc80d0445df78f6371d9
# author nrv-ops-42 <ops42@borealis-sec.nv>
#     prep: seed ops database with target attribution data

git cat-file -p bdbad9efbeaa97e3fe49949afd371bfea2ce05d7
# author nrv-ops-42 <ops42@borealis-sec.nv>
#     classified: operation briefing -- eyes only
```

Le vrai opérateur n'est pas `admin@vantagehosting.kl` mais
**`nrv-ops-42 <ops42@borealis-sec.nv>`** — une identité rattachée à
`borealis-sec.nv`. Le suffixe `.nv` et le préfixe `nrv-` pointent vers une
entité « norvethienne » : **Borealis Security**.

## Les trois blobs cachés

Le commit `16a1bec9` (tree `6da6920f`) porte deux fichiers :

- `.env` → `GPG_PASSPHRASE=Borealis-Kaltyr-2026!` et `DB_PATH=/opt/vantage/ops.db`
- `seed-database.py` → script « Stage 2 prep » qui fabrique de faux comptes
  clients (PRONIN, AVC, Ministère…) et de fausses traces d'upload pour faire
  porter la responsabilité à la République de Valdoria. Le docstring est
  explicite : « *Data is designed to implicate Valdoria in unauthorized
  exfiltration* ».

Le commit `bdbad9ef` (tree `46493a8c`) porte un unique fichier :
`op-briefing.gpg`, chiffré en GPG symétrique AES-256.

## Déchiffrement du briefing

L'`.bash_history` confirme la méthode de chiffrement utilisée par l'opérateur :

```bash
gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-file ~/.keys/bp op-briefing.txt
rm -f op-briefing.txt
```

La passphrase n'est plus sur disque (`~/.keys/bp` absent de l'image), mais elle
subsiste dans le blob `.env` inatteignable. Déchiffrement :

```bash
git cat-file blob 40d9829f8e4dd24d115235a6fcd6081455ee8378 > op-briefing.gpg
gpg --batch --yes --pinentry-mode loopback \
    --passphrase 'Borealis-Kaltyr-2026!' --decrypt op-briefing.gpg
```

Le briefing (classification `TOP SECRET // BOREALIS // NOFORN`, rédigé par
CDR M. Lindqvist) confirme l'origine : la cellule **BOREALIS** a monté le data
center fictif « Vantage Hosting Group » dans la zone franche de Mirova pour
faire croire à Tervalis que Valdoria y héberge des données volées, puis
collecter les preuves de l'intrusion tervalienne comme levier diplomatique.

La section 8 du briefing contient le token de communication de la cellule,
sous la forme :

```text
AUTH_TOKEN = <jeton>
```

C'est le secret attendu par le challenge.

## Mise en œuvre

Le solveur `solveur.py` livré reproduit toute la chaîne sans dépendre du CLI
git (lecture directe des objets lâches en Python + déchiffrement via `gpg`) :

```bash
python3 solveur.py                    # instance par défaut
python3 solveur.py 172.28.34.2 8080   # hôte + port explicites
python3 solveur.py --mask             # jeton masqué
python3 solveur.py --docs             # briefing déchiffré (masqué)
python3 solveur.py --local            # archive locale operator-ws.tar.gz
```

Sortie (valeurs sensibles masquées) :

```text
source     : http://172.28.34.2:8080
artefact   : operator-ws.tar.gz
objet blob GPG : déchiffré (AES-256, passphrase récupérée des objets git)
origine    : Borealis Security (nrv-ops-42, ops42@borealis-sec.nv)

AUTH_TOKEN = [masqué]
```

## Chemins qui ont échoué / leurres

1. **S'arrêter au `git log`.** L'historique référencé est propre et entièrement
   signé `admin@vantagehosting.kl` : il n'apprend rien sur l'origine réelle.
2. **Chercher un secret dans les Documents.** `maintenance-q3.txt`,
   `checklist-reseau.txt` et `notes-personnelles.txt` sont du remplissage de
   couverture (badges, wifi visiteur, téléphones locaux, bus…). Aucun flag.
3. **Explorer les clés SSH / l'historique navigateur comme fin en soi.** Ils
   confirment l'identité (`nrv-ops-42@borealis-ws`) mais ne contiennent pas le
   secret ; ce sont des indices, pas la réponse.
4. **Croire la passphrase perdue.** Elle n'est plus dans `~/.keys/bp` (supprimé),
   mais elle a fui dans le blob `.env` inatteignable du dépôt git : c'est la
   clé de voûte de la chaîne.

## Validation reproductible, sans le secret

1. `shasum -a 256 operator-ws.tar.gz` commence par `5c4b6654a980a501`.
2. `python3 solveur.py --mask` affiche `origine : Borealis Security (nrv-ops-42,
   ops42@borealis-sec.nv)` et `AUTH_TOKEN = [masqué]`.
3. Contrôles structurels indépendants :
   - `git fsck --unreachable` liste les 7 objets inatteignables ;
   - les commits cachés sont signés `ops42@borealis-sec.nv` ;
   - le blob `.env` contient `GPG_PASSPHRASE=` ;
   - le blob `op-briefing.gpg` commence par `8c 0d` (paquet OpenPGP
     « Symmetric-Key Encrypted Session Key ») ;
   - le déchiffrement gpg aboutit et le texte contient la section 8
     `AUTH_TOKEN =`.
4. Le jeton suit le format d'événement habituel (préfixe + accolades) et
   n'est jamais reproduit ici.

## Leçons

- En forensique git, `git log` ne montre que ce qui est référencé : les commits
  supprimés/amendés survivent dans `.git/objects` et se récupèrent via
  `git fsck --unreachable` ou en lisant directement les objets lâches.
- Un document chiffré dont la clé « a disparu » cache souvent la clé dans un
  artefact voisin (ici le blob `.env` oublié d'un commit détruit).
- Les leurres de couverture (notes, badges, historique réseau) sont volumineux
  et plausibles, mais c'est la couche non référencée du dépôt qui révèle
  l'origine.

## Nettoyage

Aucun processus ni listener laissé actif. Le solveur travaille dans un
répertoire temporaire (`tempfile`) qu'il supprime en fin d'exécution ; aucun
fichier dérivé n'est écrit dans le répertoire du challenge. Seuls `solveur.py`,
`operator-ws.tar.gz` (handout) et ce write-up persistent.
