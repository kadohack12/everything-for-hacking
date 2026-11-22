---
title: "Janus · Ghost Ratchet"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/janus/ghost-ratchet/writeup-ghost-ratchet.md"
license: "CC BY-SA 4.0"
status: published
---

# GHOST RATCHET — identité cryptographique de l'officier traitant

**Flag** : `HLB2026{B27569A089CF94378D4FE18A1769AFDA4FB1AAAA}`

## Objectif

L'extraction du terminal Android du Dr Leon Kessler contient l'application
NORDLINK (`nrv.nordlink`). Le protocole GHOST SILENT a effacé l'état courant,
mais il reste une sauvegarde d'initialisation de session, la base des messages
et la bibliothèque crypto. Il faut retrouver l'**identité cryptographique** de
l'officier traitant (le handler) avec qui Kessler communiquait.

## Fichiers fournis

```text
nordlink_device/NordLink.jar
nordlink_device/data/data/nrv.nordlink/files/ratchet_state.dat
nordlink_device/data/data/nrv.nordlink/files/session_init.bak
nordlink_device/data/data/nrv.nordlink/databases/nordlink.db
nordlink_device/data/data/nrv.nordlink/shared_prefs/nrv.nordlink_preferences.xml
```

- `ratchet_state.dat` : témoin d'autodestruction
  (`{"wiped":true,"reason":"GHOST_SILENT",...}`), sans clé.
- `session_init.bak` : JSON avec `dh_private_key`, `root_key` et
  `remote_dh_public`.
- `nordlink.db` : tables `sessions`, `messages`, `contacts`, `app_config`.
- Prefs : `local_identity = GHOST-3`, `remote_identity = SMOKE-OPS-7`,
  `session_id = NLNK-2026-0915-7F2A`.

## Analyse statique de NordLink.jar

Décompilation avec `jadx` :

```bash
jadx -d /tmp/ghost/jadx /tmp/ghost/nordlink_device/NordLink.jar
```

`nrv.nordlink.crypto.NordlinkCrypto` implémente :

- HKDF-SHA256 (`NORDLINK-root-kdf`, `NORDLINK-msg-keys`, `NORDLINK-next-dh`) ;
- X25519 (`KeyAgreement`) ;
- AES-256-CBC/PKCS5 avec IV de 16 octets ;
- HMAC-SHA256 sur `AAD || ciphertext`, avec
  `AAD = msgType || msgNum || prevChainLen || dhPublic` (entiers 32 bits
  big-endian).

`RatchetSession` implémente un Double Ratchet simplifié :

- `kdfRoot(root, DH(priv, remote)) -> (newRoot, chainKey)` ;
- `kdfChain(ck) -> (HMAC(ck, 0x01), HMAC(ck, 0x02))` ;
- `doDhRatchet(remotePub, msgType)` : nouveau `ckRecv`, puis nouvelle paire DH
  (`random` si `msgType == 0`, sinon `deriveNextDh(priv)`), puis nouveau
  `ckSend` ;
- `encrypt` / `receive` avec vérification du MAC avant le déchiffrement.

## Reconstruction du ratchet

La base contient 25 messages, avec pour chacun `direction`, `msg_num`,
`msg_type`, `dh_public`, `ciphertext`, `mac`, `prev_chain_len`.

Le backup donne :

```text
dh_private_key  = <redacted>
root_key        = <redacted>
remote_dh_public= <redacted>
```

La clé publique X25519 dérivée de `dh_private_key` correspond exactement au
`dh_public` des messages 4 à 6. En appliquant `deriveNextDh`, on retrouve ensuite
les clés publiques des chaînes 13–16 puis 20–25. Le backup est donc l'état
**juste avant la réception du message 7** (public distant encore l'ancien,
`e766…`).

Simulation à partir de cet état :

1. message 7 : `dh_public = 247f…` déclenche `doDhRatchet(247f…, 1)` :
   `ckRecv = kdfRoot(root, DH(priv, 247f…))[1]` ;
2. `deriveNextDh(priv)` donne la clé publique `2634…` (chaîne d'envoi
   13–16) ;
3. message 17 : `dh_public = d04b…` déclenche un nouveau ratchet, et
   `deriveNextDh` donne `ecb0…` (chaîne d'envoi 20–25).

Implémentation Python (extrait) :

```python
def kdf_root(root, shared):
    out = hkdf_sha256(shared, root, b"NORDLINK-root-kdf", 64)
    return out[:32], out[32:]

def kdf_chain(ck):
    return hmac_sha256(ck, b"\x01"), hmac_sha256(ck, b"\x02")

def message_keys(ck):
    out = hkdf_sha256(ck, b"", b"NORDLINK-msg-keys", 80)
    return out[:32], out[32:64], out[64:80]

# AAD = struct.pack(">III", msg_type, msg_num, prev_chain_len) + dh_public
# MAC = HMAC-SHA256(mac_key, AAD + ciphertext)
# clair = AES-256-CBC(key, iv).decrypt(ciphertext) puis retrait du padding
```

Tous les MAC des messages 7 à 25 sont vérifiés (`ok True`) et les clairs sont
du français lisible. Les messages 1 à 6 ne sont pas nécessaires pour la
question : la chaîne utile commence au ratchet du message 7.

## Résultat

Le message 18 (reçu le 23 septembre 2026 à 15:09) dit notamment :

```text
Ecoute-moi bien. On migre vers le canal secondaire. Quand NORDLINK sera coupe,
tout passera par dead drop chiffree a l'adresse qu'on a convenue. Pour verifier
que c'est bien moi, utilise l'empreinte PGP <redacted>.
N'importe quel message qui n'est pas signe par cette cle, tu l'ignores et tu
declenches GHOST SILENT dans la foulee. Pas d'exception.
```

L'identité cryptographique demandée est donc l'empreinte PGP de 40 caractères
hexadécimaux fournie dans ce message. C'est le flag du challenge **GHOST RATCHET**, indiqué en tête de ce document.

## Pistes écartées

- `ratchet_state.dat` ne contient que l'état d'autodestruction, aucune clé.
- Les champs `contacts.codename` / `remote_identity = SMOKE-OPS-7` donnent le
  nom d'opération du handler, pas son identité cryptographique.
- Utiliser directement `root_key` ou `dh_private_key` comme chaîne de messages
  ne vérifie aucun MAC : il faut passer par `kdfRoot` / `kdfChain`.
- Démarrer la simulation avant le message 7 échoue sur les chaînes 4–6, car
  leur `ckSend` n'est pas présent dans le backup (seul l'état DH l'est).

## Validation reproductible

1. Extraire `GHOST-RATCHET.zip`.
2. Décompiler `NordLink.jar` et relever les trois infos HKDF, le format AAD et
   l'AES-CBC.
3. Charger `session_init.bak`, vérifier que `pub(dh_private_key)` correspond aux
   messages 4–6.
4. Simuler `doDhRatchet` aux messages 7 et 17 avec les `dh_public` de la base.
5. Vérifier les MAC des messages 7–25, déchiffrer et lire le message 18 :
   l'empreinte PGP qui y figure est la réponse soumise.
