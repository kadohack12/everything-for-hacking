---
title: "AIZEN · Fujiko Mine"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web-crypto"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/aizen/fujiko-mine/writeup-fujiko-mine.md"
license: "CC BY-SA 4.0"
status: published
---

# Fujiko Mine — Vault 0037 (write-up du run)

## Objectif

- **Catégorie** : Web / Crypto / 200 pts
- **Cible** : `172.28.23.2:8080` — « Vault Handout »
- **Contexte** : le vault 0037 a été récupéré avec la clé maîtresse (épisode
  précédent), mais `vault-tool` refuse de fonctionner sans module HSM. Il faut
  reproduire le déchiffrement hors HSM.

## Artefacts récupérés

```bash
for f in master.key vault-0037.enc vault-tool; do
  curl -s -O "http://172.28.23.2:8080/$f"
done
```

- `master.key` : 65 octets, clé maîtresse en hexadécimal.
- `vault-0037.enc` : ~49 Ko, conteneur `VH4K-FEISTEL8-KWRAP-CBC256`.
- `vault-tool` : binaire ELF (stripped) contenant la S-box du Feistel.

## Format du conteneur

```
offset 0x00 : magie/version (0x88 octets d'en-tête)
offset 0x20 : salt (16 octets)
offset 0x30 : IV (16 octets)
offset 0x40 : wrapped KEK (0x28 = 40 octets)
offset 0x88 : payload AES-256-CBC
```

## Chaîne cryptographique

1. **Feistel 8 tours** (clé = `master.key`, entrée = `salt`) → `WK` (wrapped KEK
   de 32 octets), avec la S-box extraite du binaire à l'offset `0x2460`
   (256 octets, `.rodata` : offset fichier == vaddr).
2. **AES Key Unwrap RFC 3394** (AES-256-ECB) de `wrapped_kek` avec `WK` →
   `KEK` (vérification d'intégrité `A6A6A6A6A6A6A6A6`).
3. **AES-256-CBC** (clé = `KEK`, IV du header) sur le payload → PKCS#7.
4. **gzip** puis **tar** → extraction de l'arborescence.

## Implémentation (extrait)

```python
def feistel_encrypt(block, key, sbox, rounds=8):
    left, right = block[:16], block[16:32]
    for _ in range(rounds):
        f = bytes(sbox[a ^ b] for a, b in zip(right, key))
        left, right = right, bytes(a ^ b for a, b in zip(left, f))
    return left + right

wk = feistel_encrypt(master, salt, sbox)
kek = aes_key_unwrap(wk, wrapped_kek)          # RFC 3394
plain = AES.new(kek, AES.MODE_CBC, iv).decrypt(payload)
plain = plain[:-plain[-1]]                      # PKCS#7
tar_data = gzip.decompress(plain)
tarfile.open(fileobj=io.BytesIO(tar_data)).extractall("out")
```

## Contenu du vault

- `CABLE-2026-10-03-TERVALIS-KALTYR.{txt,pdf}`
- `CABLE-2026-10-11-TERVALIS-MFA.{txt,pdf}`
- `asset-KS47-profile.{txt,pdf}`
- `handler-notes.txt`
- `exfil-topology.txt`
- `manifest.json`

Le flag (format standard de l'événement) est présent dans les documents déchiffrés ; il a
été transmis à la plateforme (valeur non reproduite ici).

## Pistes écartées

- `vault-tool` seul → exige un module HSM absent ; inutilisable directement.
- Déchiffrement sans la S-box du binaire → le Feistel ne produit pas un `WK`
  valide (l'intégrité AES-KW échoue en `A6…`).

## Validation reproductible

1. Télécharger les trois artefacts.
2. Extraire la S-box à `0x2460` dans `vault-tool`.
3. Appliquer Feistel(8) → AES-KW unwrap (contrôle `A6A6…`) → AES-CBC → gzip → tar.
4. Les fichiers extraits contiennent le flag au format standard de l'événement.
