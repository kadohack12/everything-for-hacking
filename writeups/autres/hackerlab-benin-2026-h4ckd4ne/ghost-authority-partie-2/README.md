---
title: "Ghost Authority · Ghost Authority (partie 2)"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/ghost-authority/ghost-authority-partie-2/writeup-ghost-authority-2.md"
license: "CC BY-SA 4.0"
status: published
---

# Ghost Authority (partie 2 — le blob chiffré) — Write-up

## Objectif

- **Catégorie** : Forensics
- **Énoncé** : toute la flotte de l'autorité identifiée précédemment (Borealis) dort
  dans un gros export Certificate Transparency (`crtsh-dump.pem`), noyée parmi des
  milliers d'autres. En tirant ce fil, on remonte jusqu'à un blob chiffré ramassé
  sur la flotte : « la marque de l'atelier qui les a tous forgés ».
- **Question** : ouvrir le blob capturé (`blob-capture-c2node.enc`). Que contient-il ?
- **Fichiers fournis** : `blob-capture-c2node.enc` (256 octets), `crtsh-dump.pem`
  (export CT, ~1000 certificats).

## État initial

- `blob-capture-c2node.enc` : 256 octets de données à forte entropie (aucun
  magic), taille exacte d'un ciphertext RSA-2048.
- `crtsh-dump.pem` : 1019 certificats, dont 19 signés par
  `CN=Borealis Certification Authority, O=Borealis Trust Services` (la flotte C2).

## Reconnaissance et interprétation

La flotte = les certificats émis par l'autorité Borealis, tous au nom de
VARELCORP (`*.c2.varelcorp.var`, plus `varelcorp.var` avec l'email de Mateus
Varga). L'énoncé oriente vers une **faiblesse de génération de clés** commune à
toute la flotte : « la marque de l'atelier qui les a tous forgés » = une
empreinte laissée par l'outil qui a créé les clés.

Hypothèse : un générateur de clés défectueux (réutilisation de nombres premiers /
de modules) permettrait de factoriser des clés publiques et de reconstituer une
clé privée, puis de déchiffrer le blob RSA.

## Commandes et observations

### 1. Isoler la flotte Borealis

```bash
csplit -z -f /tmp/crt_ -b "%04d.pem" crtsh-dump.pem '/-----BEGIN CERTIFICATE-----/' '{*}'
for f in /tmp/crt_*.pem; do
  openssl x509 -in "$f" -noout -issuer
done | sort | uniq -c
```

Résultat notable : `19 issuer=... CN=Borealis Certification Authority`.

### 2. Comparer les modules RSA de la flotte

```bash
for f in <19 certs>; do openssl x509 -in "$f" -noout -modulus; done
# puis PGCD deux-à-deux des modules
```

Découvertes clés :

- `c002` et `c007` partagent **le même module 2048 bits** (même clé publique).
- `c003` et `c013` partagent **un facteur premier commun de 1024 bits**.

C'est la « marque de l'atelier » : un générateur de clés qui réutilise des
premiers (et parfois des modules entiers).

### 3. Factoriser et reconstruire des clés privées

Pour `c003` et `c013` (facteur commun `p`, et `q3`, `q13` respectifs) :

```python
import math
p  = math.gcd(n3, n13)
q3 = n3 // p
q13 = n13 // p
# puis reconstruction RSA (d, dmp1, dmq1, iqmp) et export PEM
```

### 4. Déchiffrer le blob

```bash
openssl pkeyutl -decrypt -inkey c013.key -in blob-capture-c2node.enc \
  -pkeyopt rsa_padding_mode:oaep \
  -pkeyopt rsa_oaep_md:sha256 \
  -pkeyopt rsa_mgf1_md:sha256
```

Le blob (chiffré en RSA-OAEP/SHA-256 avec la clé de la flotte) se déchiffre avec
la clé privée reconstruite de `c013` et révèle son contenu : une chaîne de la
forme `nom-outil-X.Y-buildNNNN` (voir ci-dessous, valeur soumise à la plateforme).

> Note : `c003` échoue (le blob a été chiffré avec `c013`, ou l'inverse) ; c'est
> `c013` qui déchiffre correctement.

## Raisonnement menant à la solution

- Le blob fait exactement 256 octets = la taille d'un RSA-2048 → probablement un
  ciphertext RSA.
- La flotte présente une faiblesse cryptographique (premiers réutilisés) qui
  permet de casser des clés publiques → la clé privée d'un nœud de la flotte est
  récupérable.
- Le déchiffrement RSA-OAEP de ce blob avec la clé privée reconstruite produit une
  chaîne `nom-outil-X.Y-buildNNNN` : c'est l'identifiant/version de l'outil
  (« l'atelier ») qui a forgé les certificats de la flotte, et donc le contenu
  demandé par la question.

## Pistes écartées

- Déchiffrer avec les clés privées `c003` / PKCS#1 v1.5 : padding invalide →
  écarté (OAEP requis).
- Chercher une clé/factorisation sur le module partagé `c002`/`c007` : inutile,
  le blob se déchiffre déjà avec la clé de `c013`.

## Validation (reproductible)

1. `csplit` du dump CT, filtrer les certs signés par Borealis.
2. Calculer le PGCD deux-à-deux des modules RSA → détecter le facteur commun.
3. Reconstruire la clé privée de `c013` à partir de `p` et `q13`.
4. `openssl pkeyutl -decrypt ... -pkeyopt rsa_padding_mode:oaep` sur
   `blob-capture-c2node.enc` → obtient la chaîne contenu.

La valeur soumise est le contenu déchiffré du blob, transmise à la plateforme.
