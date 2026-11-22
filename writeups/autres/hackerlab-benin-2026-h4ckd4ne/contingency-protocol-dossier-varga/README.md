---
title: "Contingency Protocol · Dossier Varga"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web3"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/contingency-protocol/contingency-protocol-dossier-varga/writeup-contingency-protocol.md"
license: "CC BY-SA 4.0"
status: published
---

# Contingency Protocol — Dossier Varga (dead man's switch)

**Flag** : `HLB2026{efe2f7684bf731e5322e91068f4c28aa}`

## Objectif

Neutraliser le contrat `Vault` avant la publication automatique du dossier.
Cible : `http://172.28.30.2:9030/` (RPC Hardhat, chainId 31337).

## Reconnaissance

Le dashboard expose `/state` :

```json
{"contract":"0x5fbdb2315678afecb367f032d93f642f64180aa3",
 "player_key":"<redacted>",
 "player_addr":"0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
 "deadline":1794897101,"ttl":1800,"armed":true,"solved":false}
```

Le contrat `Vault` (source sur `/source`) expose :

- `claimOwnership()` : **aucun contrôle d'accès**, `owner = msg.sender` ;
- `disarm()` : `onlyOwner` (`tx.origin == owner`), remet `encryptedCid` à zéro et
  passe `disarmed = true` ;
- `isSolved()` : `disarmed && !revealed && encryptedCid == 0`.

## Exploitation

1. Le compte joueur est déjà approvisionné en gas.
2. Appeler `claimOwnership()` : le compte joueur devient owner.
3. Appeler `disarm()` : la gâchette est neutralisée à la racine.
4. `isSolved()` renvoie `true`, puis `GET /flag` renvoie le flag.

Transactions :

```text
claimOwnership : 0x71de8f1e7cd2c2020694a40c87d30388c91089dae982f76730d17c1188ca81b1
disarm         : 0x2aafdab6d26dd0db197c08c646327ff295cd1ce36df2b52e30bc37f2523ed0d6
```

Le flag est indiqué en tête de ce document.

## Validation

1. `GET /state` : vérifier `armed:true`, `solved:false`.
2. Envoyer `claimOwnership()` puis `disarm()` depuis le compte joueur.
3. `eth_call isSolved()` doit renvoyer `0x...01`.
4. `GET /flag` renvoie le flag.
