---
title: "Kiss · Papyrus"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 300
os: "—"
date: 2026-11-20
author: "W1z4rd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/kiss/papyrus/writeup-papyrus.md"
license: "CC BY-SA 4.0"
status: published
---

# Papyrus — Le téléphone, beth.png et l'angecryption

**Flag** : `HLB2026{CERT-TVS-2026-IR-001}`

## Objectif

Le challenge demande ce que dissimule `beth.png`, fichier retrouvé sur le téléphone
du suspect après application d'une « technique anti-forensique ». Le flag est la
référence du dossier inscrite sur la page de garde du document final.

## État initial

- `beth.png` : 13 775 536 octets, PNG valide de 760 × 460.
- Un chunk privé `aaaa` de 13 756 864 octets précède le chunk `IHDR`.
- Un champ `tEXt` `Comment` de 12 949 octets contient des milliers de fragments
  Base64 de la forme `XX==.` (2 caractères + 2 `=`).
- Chunk `tEXt Software` : `GIMP 2.10`.
- 11 octets après `IEND`.

Les indices annoncent trois étapes et une angecryption : chaque fichier cache,
par stéganographie, la clé qui permet d'obtenir le suivant.

## Étape 1 — les bits de padding du Comment

Le Comment se décode fragment par fragment en un texte lisible : le début de la
RFC 4648 (« The Base16, Base32, and Base64 Data Encodings »). C'est un leurre.

La particularité est ailleurs : chaque fragment `XX==` encode un octet en
Base64, et les 4 bits de poids faible du second caractère sont des bits de
padding. Ils ne sont pas nuls. En les collectant, puis en les regroupant par
deux, on obtient un flux ASCII de 144 lignes Base32 :

```text
IJAU====
KNC3====
EBVD====
...
```

Ces lignes se décodent en un texte sur le BASE jumping (deuxième leurre). Le
même principe s'applique : les bits de padding de chaque ligne Base32
(4 caractères + 4 `=`) contiennent la vraie donnée.

```python
alpha64 = b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
# fragment = 2 chars + '=='
s1, s2 = alpha64.index(c1), alpha64.index(c2)
nibble = s2 & 0xf          # bits de padding Base64
```

Après regroupement des nibbles, on obtient :

```text
K1=<clé AES-128 hexadécimale>;IV1=<IV AES-128 hexadécimal>
```

## Étape 2 — déchiffrer l'image entière

Le chunk `aaaa` seul ne donne rien : ce n'est pas lui qui est chiffré, c'est le
fichier PNG complet qui sert de cryptogramme. Sa taille (13 775 536 octets) est
un multiple exact de 16, ce qui autorise un déchiffrement CBC **sans bourrage** :

```bash
openssl enc -aes-128-cbc -d -nopad \
  -K "$K1" -iv "$IV1" \
  -in beth.png -out step2.bin
```

`step2.bin` est un PNG valide de 700 × 360… en apparence seulement. Son `IHDR`
annonce 360 lignes, mais le flux `IDAT` décompressé contient 470 lignes de
2 101 octets (1 octet de filtre + 700 × 3 octets). L'image « ment sur sa
taille » : les 110 lignes supplémentaires sont sous la zone visible.

En reconstruisant un PNG de 700 × 470 avec le même flux `IDAT`, le bas de
l'image révèle :

```text
STEP3 / AES-128-CBC
K  = <clé AES-128>
IV = <IV AES-128>
```

## Étape 3 — le PDF et la page de garde

On déchiffre de nouveau le fichier complet (`step2.bin`, multiple de 16) avec la
clé et l'IV de l'étape 3 :

```bash
openssl enc -aes-128-cbc -d -nopad \
  -K "$K3" -iv "$IV3" \
  -in step2.bin -out step3.pdf
```

Résultat : un PDF 1.4 de 19 pages. La première page est la page de garde du
document :

- titre : « RAPPORT D'INCIDENTS PROVISOIRE » ;
- opération : « CERT-Tervalis : Opération "Sous le masque numérique" » ;
- équipe : H3lf W1tch3s ;
- date : 23 août 2026 ;
- classification : CONFIDENTIEL, usage interne TCDA ;
- **référence dossier** : la valeur demandée par le challenge.

La référence est celle du tableau de la page de garde ; elle figure en tête de ce document.

## Raisonnement

Le fichier est un polyglotte construit par angecryption :

1. `beth.png` est un PNG valide qui, déchiffré en AES-128-CBC, produit le PNG
   suivant ; la clé est cachée dans les bits de padding Base64 du Comment.
2. Le PNG suivant est valide mais son `IHDR` sous-dimensionne volontairement
   l'image ; les lignes en trop contiennent la clé de l'étape 3. La clé est
   elle-même cachée dans les bits de padding d'un texte Base32.
3. Le dernier déchiffrement produit le PDF ; la page de garde porte la
   référence dossier qui constitue le flag.

## Pistes qui n'ont pas fonctionné

- Déchiffrer uniquement le chunk privé `aaaa` : le résultat est aléatoire, le
  cryptogramme est le fichier PNG entier.
- Les textes en clair (RFC 4648, BASE jumping) sont des leurres : la donnée
  utile est dans leurs bits de padding.
- Les modes AES-CTR, ECB, CFB et OFB sur le chunk ne donnent pas de fichier
  valide ; c'est le CBC sans bourrage sur le fichier complet qui fonctionne.
- Le PNG intermédiaire s'ouvre normalement en 700 × 360 : sans examiner la
  taille réelle du flux `IDAT`, les 110 lignes cachées restent invisibles.

## Validation reproductible

1. Extraire le Comment de `beth.png` et collecter les nibbles de padding des
   fragments Base64.
2. Décoder ces nibbles en Base32, puis collecter à leur tour les nibbles de
   padding des lignes Base32 : on obtient `K1` et `IV1`.
3. `openssl enc -aes-128-cbc -d -nopad -K $K1 -iv $IV1 -in beth.png -out step2.bin`
   doit produire un PNG commençant par la signature PNG et contenant un chunk
   `aaaa`.
4. Décompresser le flux `IDAT` de `step2.bin` : 470 lignes de 2 101 octets pour
   un `IHDR` de 360 lignes. Reconstruire un PNG 700 × 470 pour lire `K3`/`IV3`.
5. `openssl enc -aes-128-cbc -d -nopad -K $K3 -iv $IV3 -in step2.bin -out step3.pdf`
   doit produire un PDF de 19 pages.
6. Ouvrir la page 1 : la référence dossier du tableau correspond au flag du
   challenge.
