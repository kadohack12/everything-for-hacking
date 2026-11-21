---
title: "JANUS Q9 · Hidden Treasure"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/09-hidden-treasure.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q9 · Hidden Treasure (100 pts)

> *« Examinez toutes les preuves restaurées et retrouvez l'information dissimulée. »*

## TL;DR

Dans `requisitoire_ministere_public.pdf` (déchiffré), une string en blanc sur blanc à la fin du doc = base64 inversé → le flag.

**Flag** : `HLB2026{wh1t3_0n_wh1t3_1s_n0t_h1dd3n}`

## Exploration

Après avoir déchiffré tous les uploads du serveur en masse avec la clé JANUS :

```bash
for f in uploads/*.enc; do python3 decrypt.py "$f"; done
```

Tous les PDF sont des documents judiciaires inoffensifs sauf un : `requisitoire_ministere_public.pdf` pèse **1483 octets** alors que les autres font ~700 octets. En l'extrayant via `pdftotext -layout` :

```
REQUISITOIRE DU MINISTERE PUBLIC
Parquet pres le Tribunal de grande instance de Tervalis
...
Fait a Tervalis, le 8 novembre 2026.
Le substitut du procureur de la Republique.




                                   QfuNDZkFDafRHMu91cx81M0FDa39lbw81M0FDa3tnNyAjMCxES
```

La string en bas, invisible à l'œil (couleur blanche dans le PDF) est du base64 **écrit à l'envers**.

## Décodage

```python
import base64
s = "QfuNDZkFDafRHMu91cx81M0FDa39lbw81M0FDa3tnNyAjMCxES"
print(base64.b64decode(s[::-1]))
# b'HLB2026{wh1t3_0n_wh1t3_1s_n0t_h1dd3n}'
```

## Flag

```
HLB2026{wh1t3_0n_wh1t3_1s_n0t_h1dd3n}
```
