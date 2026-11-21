---
title: "Memento Q1 · Under Seal"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/memento/01-under-seal.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# The Fall of Memento : Q1 · Under Seal (200 pts)

> *« On a forcé la planque d'Henri Mertens. Ce qu'il a tenté de détruire est sous scellés. Trouvez le flag dans le dossier. »*

## TL;DR

Le flag est dans `scelle-P7.enc` (clé USB chiffrée, 64 octets OpenSSL salted). La clé de déchiffrement est cachée dans **le code-barres PDF417 de la carte d'embarquement** (`exhibit-A.png`) :

```
KEY 6a897fb46ce9efe09e4a24c3
```

**Flag** : `HLB2026{9a8fa0c62ffbbb957e051a3f1918b823}`

## Dump des pièces

Le portail expose un `data.js` + 9 assets (`exhibit-A..I`). Le fichier chiffré :

```
scelle-P7.enc (64 B)  =  Salted__ (8) | salt (8) | ciphertext (48)
```

## Décodage du PDF417

Les outils zbar ne gèrent pas PDF417. `pdf417decoder` oui :

```python
from PIL import Image
from pdf417decoder import PDF417Decoder

im = Image.open("exhibit-A.png").convert("RGB")
d = PDF417Decoder(im)
d.decode()
print(d.barcode_data_index_to_string(0))
```

Sortie :

```
M3MERTENS/HENRI       EQR4T9Z VLDKTYVA 0117 137J003A0042 01A>6 UPG WL
PAX REF VARGA   QR4T9Z KTYKVXVA 0231 137J011C0043 01A>6 BAG 1PC/23 SEQ ACCEPTED
QR4T9Z KVXKDRKA 0088 137Y014C0044 043>6 RBK KVX>KDR KA088/137
OPR KALAIR // KEY 6a897fb46ce9efe09e4a24c3
```

Deux choses :
- **La 3e étape cachée** : KA 0088 KVX → KDR jour 137 (le charter, conforme au post-it « charter KA0.. pas la ligne »).
- **La clé** : `6a897fb46ce9efe09e4a24c3` (24 hex → 12 octets).

## Déchiffrement du scellé

Les 24 hex servent de **passphrase** pour OpenSSL (pas de clé brute) :

```bash
openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:6a897fb46ce9efe09e4a24c3 \
            -in scelle-P7.enc -out flag.txt
cat flag.txt
```

## Flag

```
HLB2026{9a8fa0c62ffbbb957e051a3f1918b823}
```
