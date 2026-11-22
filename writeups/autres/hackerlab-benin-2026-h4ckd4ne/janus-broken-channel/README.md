---
title: "Janus · Broken Channel"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/janus/broken-channel/writeup-broken-channel.md"
license: "CC BY-SA 4.0"
status: published
---

# Broken relay — Q2 « Broken channel »

## Objectif

Le challenge demande l'heure de **première exécution** de `cipher.exe` sur la
machine du suspect (image AD1 `thanos_desktop.ad1`). Le format attendu est
l'heure `HH:MM` dans le conteneur habituel du CTF.

## État initial

- `thanos_desktop.zip` (1,2 Gio) contient une image logique AccessData :
  `thanos_desktop.ad1` (1 264 587 858 octets).
- Le fichier `CIPHER.EXE-134146E6.pf` (Prefetch Windows) est référencé dans
  l'image, mais les données sont compressées : une simple recherche de `SCCA`
  dans l'AD1 ne donne rien.
- Le Prefetch lui-même est un Prefetch Windows 10 **compressé MAM**.

## Reconnaissance

```bash
unzip -t thanos_desktop.zip
# testing: thanos_desktop.ad1   OK

strings -n 6 /tmp/thanos/thanos_desktop.ad1 | grep -i cipher
# CIPHER.EXE-134146E6.pf
# CIPHER~1.PF
# cipher.exe
```

L'entrée de métadonnées du fichier se trouve vers `0x7ec00` :

```text
0007ec00: 0043 4950 4845 522e 4558 452d 3133 3431  .CIPHER.EXE-1341
0007ec10: 3436 4536 2e70 6665 2600 0000 0000 0001  46E6.pfe&.......
```

Juste après cette entrée, à `0x7ec37`, on trouve un flux zlib (`78 9c`).

## Extraction du Prefetch

Le flux zlib se décompresse en un conteneur `MAM` :

```python
import zlib
with open('/tmp/thanos/thanos_desktop.ad1','rb') as f:
    f.seek(0x7ec37)
    data = f.read(300000)
out = zlib.decompressobj().decompress(data)
# out[:8] == b'MAM\x04' + taille little-endian 0x168a (5770)
```

Le contenu `MAM` est un Prefetch Windows 10 compressé (LZXPRESS Huffman).
Avec `dissect.util` :

```python
from dissect.util.compression import lzxpress_huffman
pf = lzxpress_huffman.decompress(out[8:])
open('/tmp/thanos/cipher.pf','wb').write(pf)
```

Résultat : 5 773 octets, en-tête `1e 00 00 00 53 43 43 41`
(version 30, signature `SCCA`), nom `CIPHER.EXE`, hash `0x134146e6`.

## Lecture des timestamps

```bash
sccainfo /tmp/thanos/cipher.pf
```

```text
Format version          : 30
Prefetch hash           : 0x134146e6
Executable filename     : CIPHER.EXE
Run count               : 3
Last run time: 1        : Nov 09, 2026 09:20:11.904974000 UTC
Last run time: 2        : Feb 08, 2026 17:09:03.785681800 UTC
Last run time: 3        : Feb 08, 2026 <redacted HH:MM> UTC
Last run time: 4        : Not set (0)
...
```

Le compteur d'exécutions vaut 3 et les trois timestamps sont cohérents.
La plus ancienne exécution enregistrée est donc celle du **8 février 2026 à
`<redacted HH:MM>` UTC**. C'est la première exécution de `cipher.exe`.

Validation directe des FILETIME à l'offset `0x80` de l'en-tête :

```text
0x80  0x01DD702B85A4AE0C  -> 2026-11-09 09:20:11.904974 UTC
0x88  0x01DC991DA05D8432  -> 2026-02-08 17:09:03.785681 UTC
0x90  0x01DC991AE970C957  -> 2026-02-08 <redacted HH:MM> UTC
```

## Piste fausse (à ne pas reproduire)

Une première recherche de timestamps DOS dans les octets proches du nom avait
produit `2024-02-05 05:50:36` aux offsets `519174`, `522239` et `523091`. Ces
octets sont en réalité les caractères ASCII `R.EX` / `C.EX` du nom
`CIPHER.EXE-134146E6.pf` : la valeur little-endian `0x58452e52` ressemble à une
date DOS, mais ce n'en est pas une. Cette piste a été écartée après extraction
du vrai Prefetch.

## Procédure de validation reproductible

1. Extraire `thanos_desktop.ad1` du zip.
2. Décompresser le flux zlib à `0x7ec37`, puis le bloc `MAM` avec
   `lzxpress_huffman`.
3. Vérifier la signature `SCCA`, le nom `CIPHER.EXE` et le hash `134146e6`.
4. Lire les FILETIME à `0x80`, garder le plus ancien et le formater en `HH:MM`
   UTC : la valeur obtenue est celle soumise (volontairement non recopiée ici).

## Réponse

La réponse soumise est l'heure `HH:MM` de la plus ancienne exécution, reportée
à la plateforme sous le challenge **Broken channel**. La valeur exacte est volontairement
absente de ce document.
