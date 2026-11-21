---
title: "JANUS Q1 · Ransomless"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/01-ransomless.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q1 · Ransomless (100 pts)

> *« La hiérarchie informe qu'un fichier d'importance systémique se trouvait sur le serveur compromis lors de l'incident. Les données du serveur ont été intégralement altérées par un ransomware. Récupérez d'une façon ou d'une autre le contenu de ce fichier. »*

## TL;DR

Le ransomware `BURNOUT` (déposé sous le nom `calc.exe`) est une simple implémentation **XTEA en mode CTR** compilée en MinGW. La clé AES est dérivée d'une string obfusquée qu'on peut récupérer statiquement. Un `openssl` à la main sur le `.enc` cible redonne le PDF en clair.

**Flag** : `HLB2026{EXP-2026-JANUS-04}`

## Reconnaissance

L'archive KAPE (1,9 Gio, Mega) contient une collection forensique d'un XAMPP compromis. Le binaire malveillant est à :

```
C:\Users\backup\AppData\calc.exe
```

C'est un **PE64 MinGW** avec des symboles parlants :

```
encrypt_directory  derive_key   xorshift32   ctr_crypt
xtea_encrypt_block  OBFUSCATED_KEY  derived_key.0
```

Les strings révèlent aussi :

```
=== BURNOUT ===
Tous vos fichiers ont été chiffrés.
Les archives du tribunal nous appartiennent.
Les opérations LYNX se poursuivent.
-- Division Cyber FNS
BURNOUT_README.txt
Software\Microsoft\Windows\CurrentVersion\Run
WindowsCalculatorService
```

Le format d'un fichier chiffré est trivialement lisible depuis `encrypt_directory` :

```
[4B "ASH2"]  [8B salt]  [ciphertext]
```

Les 4 premiers octets du « salt » sont en réalité le **counter_low** utilisé par le CTR.

## Reverse du schéma crypto

### 1. OBFUSCATED_KEY

Au démarrage, `WinMain` prépare la clé maître :

```asm
mov    $0x4153484e, %esi  ; seed xorshift32
lea    OBFUSCATED_KEY(%rip), %rsi
loop:
  call  xorshift32
  xor   -0x1(%rsi), %al    ; XOR avec octet obfusqué
  mov   %al, -0x1(%rbx)    ; store clear text
```

28 octets obfusqués XOR avec le flux de `xorshift32(seed = 0x4153484E)` :

```python
def xs32(x):
    x = ((x << 13) ^ x) & 0xFFFFFFFF
    x ^= x >> 17
    x = ((x << 5) ^ x) & 0xFFFFFFFF
    return x

obf = bytes.fromhex("4f3e7c026b93338834a4d3dc6b0eabf3c21e036b560fae3d9e4a6d40")
state = 0x4153484E
out = bytearray()
for b in obf:
    state = xs32(state)
    out.append(b ^ (state & 0xff))
print(out)   # b'LYNX_FNS_ASHEN_TRIBUNAL_2026'
```

### 2. derive_key

Ensuite `derive_key("LYNX_FNS_ASHEN_TRIBUNAL_2026", &master_key)` fabrique 16 octets. C'est une boucle « xorshift + byte input + rotation sur 4 u32 », transcrite tel quel depuis l'asm :

```python
MASK = 0xFFFFFFFF
def derive_key(s):
    state = [0x2650a83f, 0xfa34e6cb, 0x7037bd2a, 0xe41cbd74]
    r9  = 0x4153484e
    r11 = 0x2650a83f
    for i, b in enumerate(s):
        r9 = xs32(r9)
        sb = b if b < 128 else b - 256
        val = (((sb << ((i & 3)*8)) & MASK) ^ r9 ^ r11) & MASK
        state[i & 3] = val
        nxt = (i + 1) & 3
        state[nxt] = (state[nxt] + (val >> 3)) & MASK
        r11 = state[nxt]
    # 64 rondes de mixage final (unrolled)
    ...
    return struct.pack("<IIII", *state)
```

Résultat : `f5d5ea867ed402236e78e156ddf1468d`.

### 3. XTEA custom-delta en CTR

`xtea_encrypt_block` est standard **sauf** :

- `delta = 0x4C594E58` (ASCII « XNYL »)
- La première moitié de chaque ronde utilise `key[0]` statiquement (pas `key[sum & 3]`)
- 32 rondes classiques → terminaison sur `sum == 0x8B29CB00`

`ctr_crypt` fabrique le compteur comme `(block_idx << 32) | counter_low`, chiffre ce bloc avec XTEA et XOR avec le plaintext.

## Exploitation

Le fichier cible : `expertise_technique_JANUS.pdf.enc` (699 octets).

```python
import struct
MASK, DELTA, TERM = 0xFFFFFFFF, 0x4C594E58, 0x8B29CB00

def xtea_block(v0, v1, key):
    s, k0 = 0, key[0]
    while True:
        t = ((((v1 << 4) & MASK) ^ (v1 >> 5)) + v1) & MASK
        t ^= (k0 + s) & MASK
        v0 = (v0 + t) & MASK
        s = (s + DELTA) & MASK
        t = ((((v0 << 4) & MASK) ^ (v0 >> 5)) + v0) & MASK
        t ^= (key[(s >> 11) & 3] + s) & MASK
        v1 = (v1 + t) & MASK
        if s == TERM: return v0, v1

key = list(struct.unpack("<IIII", bytes.fromhex("f5d5ea867ed402236e78e156ddf1468d")))
data = open("expertise_technique_JANUS.pdf.enc","rb").read()
salt, ct = data[4:12], data[12:]
counter_low = struct.unpack("<I", salt[:4])[0]

pt = bytearray()
for b in range((len(ct)+7)//8):
    e0, e1 = xtea_block(counter_low, b, key)
    ks = struct.pack("<II", e0, e1)
    pt.extend(bytes(a^b for a,b in zip(ct[b*8:(b+1)*8], ks)))

open("janus.pdf","wb").write(pt)
```

Le PDF révèle :

```
RAPPORT D'EXPERTISE TECHNIQUE
Analyse des communications interceptees
Reference : EXP-2026-JANUS-04
```

## Flag

```
HLB2026{EXP-2026-JANUS-04}
```
