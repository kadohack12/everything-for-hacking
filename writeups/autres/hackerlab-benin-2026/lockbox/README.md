---
title: "Lockbox · OTP addition digit-wise"
platform: "HackerLab Benin 2026"
category: "crypto"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/crypto/lockbox.md"
tags: [hackerlab-benin-2026, crypto]
status: published
---

# Lockbox : Crypto · OTP addition digit-wise

**Catégorie** : crypto  
**Flag** : `HLB2026{5affddc8187619ef9d7e625982c65197}`

## TL;DR

Le coffre VS-400E utilise une OTP par addition digit-wise sans retenue. Deux paires défi/code dans le brief suffisent à retrouver la clé. On frappe l'API avec le code calculé pour le défi courant.

## Analyse du schéma

Le brief donne deux exemples :

```
défi=314159 → code=732222
défi=271828 → code=699991
```

Pour chaque position `i` sur 6 chiffres : `code[i] = (challenge[i] + key[i]) mod 10` (addition sans retenue, pas de propagation).

On résout la clé position par position :

```
key[0] = (7 - 3) mod 10 = 4
key[1] = (3 - 1) mod 10 = 2
key[2] = (2 - 4) mod 10 = 8   # (mod 10 : 2-4 = -2 ≡ 8)
key[3] = (2 - 1) mod 10 = 1
key[4] = (2 - 5) mod 10 = 7
key[5] = (2 - 9) mod 10 = 3
→ key = 428173
```

Vérification sur le deuxième exemple : `271828 + 428173` digit-wise = `699991`. Correct.

## Exploitation

```python
import urllib.request, json

BASE = "http://172.28.34.2"
KEY = [4, 2, 8, 1, 7, 3]

headers = {"Host": "vault.vdcbank.vld", "Content-Type": "application/json"}

# Récupérer le défi courant
req = urllib.request.Request(BASE + "/api/info", headers=headers)
info = json.loads(urllib.request.urlopen(req).read())
challenge = str(info["challenge"]).zfill(6)

# Calculer le code
code = "".join(str((int(challenge[i]) + KEY[i]) % 10) for i in range(6))

# Soumettre
req = urllib.request.Request(
    BASE + "/api/unlock",
    data=json.dumps({"code": code}).encode(),
    headers=headers,
    method="POST"
)
print(json.loads(urllib.request.urlopen(req).read()))
```

La réponse JSON contient `"status":"open"` et le flag.

## Pièges

Le défi tourne à chaque session : ne pas réutiliser les codes du brief. Après trop d'essais incorrects, `attempts_left` tombe à zéro et le compte est verrouillé. L'animation "capture CAM-VAULT-01" après l'ouverture est purement cosmétique ; le flag est dans la réponse JSON.
