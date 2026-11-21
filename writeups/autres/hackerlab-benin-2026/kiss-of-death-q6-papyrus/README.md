---
title: "Kiss of Death Q6 · Papyrus"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 300
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/kiss-of-death/06-papyrus.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# Kiss of Death : Q6 · Papyrus (300 pts)

> *« La dernière notification du téléphone parle de : "Technique anti-forensique appliquée au fichier sensible." Retrouvez le fichier beth.png et identifiez ce qu'il dissimule. Flag = référence du dossier sur la page de garde. »*

## TL;DR

`beth.png` est un fichier polyglotte **angecryption** à trois étages :

1. Les bits de padding du chunk tEXt (base64 → base32) cachent `K1/IV1`.
2. `AES-128-CBC -nopad` sur le fichier entier → un second PNG dont l'IHDR ment sur sa hauteur ; les lignes cachées sous l'image révèlent `K3/IV3`.
3. Deuxième déchiffrement → un PDF de 19 pages dont la page de garde contient la référence.

## Étape 1 : `K1/IV1` dans les bits de padding

Analyse initiale de `beth.png` :

- PNG valide 760 × 460, ~13,8 Mio.
- Un chunk privé `aaaa` de ~13,7 Mio précède IHDR.
- Chunk `tEXt Comment` de ~13 ko plein de fragments `XX==`.

Chaque fragment `XX==` encode un octet. En base64 standard, la paire `XX` encode 12 bits dont seuls 8 sont utilisés : **les 4 bits de poids faible du second char sont des bits de padding**. Ici ils ne sont pas nuls.

```python
alpha64 = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
nibbles = []
for frag in comment.split():        # chaque "XX=="
    c1, c2 = frag[0], frag[1]
    nibbles.append(alpha64.index(c2) & 0xf)
# regroupement 2-par-2 → octets → texte Base32
```

Le flux obtenu est du Base32 (`IJAU====`, `KNC3====`, …). On ré-applique la même astuce : chaque ligne Base32 (`4 chars + 4 =`) a ses bits de padding réellement utiles.

Après regroupement final :

```
K1=<hex AES-128>;IV1=<hex AES-128>
```

## Étape 2 : déchiffrement global

Le fichier `beth.png` fait exactement un multiple de 16 (13 775 536 octets) → cryptogramme *brut* en CBC sans bourrage :

```bash
openssl enc -aes-128-cbc -d -nopad \
    -K "$K1" -iv "$IV1" \
    -in beth.png -out step2.bin
```

`step2.bin` est un PNG valide **de 700 × 360** en apparence. Mais le flux IDAT décompressé fait **470 lignes** de 2101 octets au lieu de 360 → 110 lignes cachées sous la zone visible.

On reconstruit un PNG avec IHDR patché à `700 × 470` :

```python
import struct, zlib
d = open("step2.bin","rb").read()
# patch IHDR height
hdr = d[8:8+4+4+13+4]
w, h = struct.unpack(">II", hdr[8:16])
new_hdr = hdr[:12] + struct.pack(">II", w, 470) + hdr[20:25]
new_crc = zlib.crc32(new_hdr[4:21]).to_bytes(4, "big")
patched = d[:8] + new_hdr[:-4] + new_crc + d[8+len(hdr):]
open("step2_fixed.png","wb").write(patched)
```

Les 110 lignes cachées affichent en clair :

```
STEP3 / AES-128-CBC
K  = <hex>
IV = <hex>
```

## Étape 3 : PDF

```bash
openssl enc -aes-128-cbc -d -nopad \
    -K "$K3" -iv "$IV3" \
    -in step2.bin -out step3.pdf
```

PDF 1.4 de 19 pages. La **page de garde** est un tableau d'intitulés (titre, opération, équipe, date, classification) dont la ligne **Référence dossier** = **flag**.

## Flag

```
HLB2026{<reference-dossier>}
```

> La référence est celle du tableau de la page de garde : par convention non recopiée ici (unique à l'instance).

## Pistes qui n'ont PAS marché

- Déchiffrer seulement le chunk privé `aaaa` → sortie aléatoire. C'est le fichier **entier** qui est chiffré.
- Lire bêtement le texte du `Comment` : c'est un extrait de la RFC 4648 : c'est un leurre.
- Mode CTR/ECB/CFB : seul CBC `-nopad` sur le PNG complet fonctionne.
- Ouvrir le step2 avec un viewer : l'image s'affiche en 700×360 sans rien montrer tant qu'on ne corrige pas l'IHDR.
