---
title: "Vault 0037 · Feistel8 + AES-KW"
platform: "HackerLab Benin 2026"
category: "crypto"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/crypto/vault0037.md"
tags: [hackerlab-benin-2026, crypto]
status: published
---

# Vault 0037 : Crypto · VH4K Feistel8 + AES-KW + AES-CBC

**Catégorie** : crypto  
**Flag** : `HLB2026{ce0f5ae6e8dd50179d328750875568ac}`

## TL;DR

Le handout contient `master.key`, `vault-0037.enc` et un binaire `vault-tool` qui expose des commandes `info` et `verify` mais pas de déchiffrement. Le crypto est présent dans le binaire sous forme de fonctions non référencées : Feistel8 pour dériver la KEK depuis la master key, AES-KW (RFC 3394) pour déchiffrer la CEK, puis AES-CBC-256 pour le plaintext final.

## Layout de vault-0037.enc

```
offset 0x00 : magic / header (variable)
offset 0x20 : salt       (16 bytes)
offset 0x30 : iv         (16 bytes)
offset 0x40 : wrapped    (40 bytes, CEK chiffrée)
offset 0x68 : hmac       (non vérifié par vault-tool)
offset 0x80 : ciphertext
```

## Reverse du schéma

**Feistel8 → KEK**

La fonction `feistel8_derive` dans le binaire applique 8 tours sur 16 octets avec la master key comme matériel de ronde et le salt comme bloc d'entrée. Une S-box est compilée en dur dans le binaire (récupérée via `objdump`). La KEK fait 32 bytes (deux blocs Feistel concaténés).

**AES-KW → CEK**

Les 40 octets à l'offset `0x40` sont une CEK de 32 bytes encapsulée selon RFC 3394 avec la KEK. `pycryptodome` implémente AES-KW nativement :

```python
from Crypto.Cipher import AES

kek = feistel8_derive(master_key, salt)
cek = AES.new(kek, AES.MODE_SIV).decrypt_and_verify(wrapped[:32], wrapped[32:40])
# ou via Crypto.Protocol.RFC3394
```

**AES-CBC-256 → plaintext**

```python
cipher = AES.new(cek, AES.MODE_CBC, iv)
pt_gz = cipher.decrypt(ciphertext)
```

Le plaintext est un archive tar.gz. Après décompression :

```bash
python3 -c "import gzip,io; open('out.tar','wb').write(gzip.decompress(pt_gz))"
tar xf out.tar
cat ACCESS_TOKEN
```

Le fichier `ACCESS_TOKEN` contient le flag :

```
HLB2026{ce0f5ae6e8dd50179d328750875568ac}
```

## À retenir

Quand un binaire expose des fonctions crypto dans ses symboles mais ne les appelle pas depuis les commandes documentées, c'est souvent la voie intentionnelle. `objdump -t` et `objdump -d` sur les fonctions orphelines suffisent à reconstruire le schéma sans décompilateur.
