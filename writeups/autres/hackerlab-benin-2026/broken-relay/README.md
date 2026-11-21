---
title: "Broken Relay · AD1 + relay.db"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 0
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/forensics/hl-broken-relay.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# Broken Relay : Forensics · Analyse AD1 + déchiffrement relay.db

**Catégorie** : forensics  
**Flag Q1** : `http://relay-chat.nrv:8088/`  
**Flag Q3** : `HLB2026{#n0rv3th_c1ph3r_1s_br0k3n}`

## TL;DR

Une image forensique AD1 d'une machine Windows compromise. Q1 : retrouver l'URL d'une plateforme secrète dans les artefacts browser. Q3 : déchiffrer 24 messages d'un salon de chat chiffré AES-256-GCM, puis décoder une couche de chiffrement maison sur le message final.

## Q1 : URL de RELAY

L'artefact AD1 (~1.2 GB sur Mega) contient un profil Windows. Après extraction et décompression des chunks zlib, on grep les URLs :

```bash
grep -oa 'https\?://[^ "]*relay[^ "]*' extracted/ 
```

L'URL apparaît dans plusieurs emplacements du profil Edge :
- Top-sites shortcut avec le titre `RELAY`
- `logins.json` Firefox
- Cookies avec `partitionKey` correspondant

```
http://relay-chat.nrv:8088/
```

## Q3 : Conspiracy

Sur le bureau de l'utilisateur `thanos` : `channel.pdf` (verrouillé avec le mot de passe `nisrina`) et `cipher.exe`.

`channel.pdf` déverrouillé contient trois codes de salon :

```
7V3E-VT8E-JC4W  → general
4DAX-QX7S-NPQX  → infra
676K-VBDM-56AZ  → archive
```

La base `relay.db` est dans le rootfs extrait de l'image. Chaque salon a un `key_salt` et un `key_check` ; les messages sont chiffrés AES-256-GCM avec le contexte AAD `relay:message:<channel_id>:<author>`. La clé est dérivée via scrypt sur le code de salon.

Le contenu de chaque message est lui-même encodé avec un schéma custom de `cipher.exe` : marqueur `ENC1:`, custom base64 sur un alphabet non-standard, puis XOR avec un flux xorshift32 et rotation de bits.

Le message 19 de `VanDerLin` une fois décodé :

```
#n0rv3th_c1ph3r_1s_br0k3n
```

Le flag est `HLB2026{#n0rv3th_c1ph3r_1s_br0k3n}`.

## Script

```python
#!/usr/bin/env python3
import hashlib, sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DB = Path(__file__).parent / "q3/rootfs/data/relay.db"
ALPHABET = b"Zm9Kx2QaLp7VfT0cRw4YhN1sJd8GuB3eXo6IkP5tCyAqWn-_ErSvHgMlDjUbOiFz"
HASH_TABLE = bytes.fromhex("985e20f945eadd6639e0209529d05c87")
FNV = 0x01000193
PAD = bytes.fromhex("28bf4e5e4e758a4164004e56fffa01082e2e00b6d0683e802f0ca9fe6453697a")

def derive(code, salt):
    return hashlib.scrypt(code.encode(), salt=salt, n=2**15, r=8, p=1,
                          maxmem=64 * 1024 * 1024, dklen=32)

def custom_b64_decode(s):
    vals = {c: i for i, c in enumerate(ALPHABET)}
    acc = bits = 0
    out = bytearray()
    for c in s.encode():
        acc = (acc << 6) | vals[c]
        bits += 6
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xff)
    return bytes(out)

def seed_hash(seed):
    h = 0x811C9DC5
    d = 0xFFFFFFA7
    for b in HASH_TABLE:
        h = ((h ^ ((b ^ d) & 0xff)) * FNV) & 0xffffffff
        d = (d + 0x1d) & 0xffffffff
    for b in seed:
        h = (((b ^ h) & 0xffffffff) * FNV) & 0xffffffff
    return h

def ror8(v, n):
    n %= 8
    return v if n == 0 else ((v >> n) | (v << (8 - n))) & 0xff

def cipher_decode(text):
    if text.startswith("ENC1:"):
        text = text[5:]
    raw = custom_b64_decode(text)
    state = seed_hash(raw[:4])
    previous = raw[3]
    plain = bytearray()
    for current in raw[4:]:
        state ^= (state << 13) & 0xffffffff
        state &= 0xffffffff
        state ^= state >> 17
        state ^= (state << 5) & 0xffffffff
        state &= 0xffffffff
        value = ror8((current - previous) & 0xff, state >> 8)
        plain.append(value ^ (state & 0xff))
        previous = current
    if (sum(plain[:-1]) & 0xff) != plain[-1]:
        raise ValueError("checksum mismatch")
    return bytes(plain[:-1]).decode()

def main():
    db = sqlite3.connect(DB)
    channels = {r[0]: r for r in db.execute(
        "select id,name,key_salt,key_check from channels")}
    codes = {1: "7V3E-VT8E-JC4W", 2: "4DAX-QX7S-NPQX", 3: "676K-VBDM-56AZ"}
    keys = {}
    for cid, code in codes.items():
        _id, _name, salt, check = channels[cid]
        key = derive(code, salt)
        AESGCM(key).decrypt(check[:12], check[12:], f"relay:check:{cid}".encode())
        keys[cid] = key
        print(f"channel {cid}: {_name} unlocked")
    for mid, cid, author, body in db.execute(
            "select id,channel_id,author,body from messages order by id"):
        key = keys[cid]
        text = AESGCM(key).decrypt(body[:12], body[12:],
                                   f"relay:message:{cid}:{author}".encode()).decode()
        print(f"[{mid}] #{channels[cid][1]} <{author}>: {cipher_decode(text)}")

if __name__ == "__main__":
    main()
```

## À retenir

Le dernier caractère du flag (`3` dans `br0k3n`) est un chiffre, pas la lettre `e`. La transcription rapide depuis la sortie brute peut induire en erreur. Toujours copier depuis la sortie du script, pas depuis une lecture à la volée.
