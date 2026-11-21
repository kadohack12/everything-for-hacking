---
title: "JANUS Q3 · New Blood"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/03-new-blood.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q3 · New Blood (100 pts)

> *« Après avoir obtenu un premier accès, un compte utilisateur a été créé. Retrouvez : le nom, l'heure de création, l'heure de première ouverture de session. »*

Format : `HLB2026{compte_HH:MM:SS_HH:MM:SS}` (temps en CET local serveur).

## TL;DR

Le compte `backup` est créé par l'attaquant via le webshell. SAM et le log `TerminalServices-LocalSessionManager` donnent les timestamps.

**Flag** : `HLB2026{backup_17:55:56_18:21:27}`

## SAM

Après déchiffrement de `C/Windows/System32/config/SAM.enc`, lecture via `regipy` :

```python
from regipy.registry import RegistryHive
h = RegistryHive("SAM")
users = h.get_key(r"\SAM\Domains\Account\Users")
for sk in users.iter_subkeys():
    if sk.name == "Names": continue
    for v in sk.iter_values():
        if v.name == "F":
            pw_last_set = struct.unpack("<Q", v.value[24:32])[0]
            last_logon  = struct.unpack("<Q", v.value[8:16])[0]
            print(sk.name, ft(pw_last_set), ft(last_logon))
```

RID `000003E9` = `backup` :
- `pw_last_set = 2026-11-08 16:55:56 UTC` → **17:55:56 CET** = heure de création
- `last_logon  = 2026-11-08 18:47:49 UTC` → dernière ouverture, pas la première

## Terminal Services : première session

Pour la **première** ouverture on relit `Microsoft-Windows-TerminalServices-LocalSessionManager%4Operational.evtx` (déchiffré) :

```
EID=21  t=2026-11-08 17:21:27 UTC  user=DESKTOP-DR7GDH8\backup  addr=LOCAL
EID=22  t=2026-11-08 17:21:28 UTC  user=DESKTOP-DR7GDH8\backup  addr=LOCAL
```

EID 21 = *Session logon succeeded* → première connexion à **17:21:27 UTC = 18:21:27 CET**.

## Flag

```
HLB2026{backup_17:55:56_18:21:27}
```

> **Note timezone** : le serveur est en `W. Central Africa Standard Time` (UTC+1, pas de DST). Les horodatages Windows (SAM, EVTX) sont stockés en UTC, à convertir en local pour matcher la convention utilisée par l'énoncé (déjà en +01:00 dans les logs Apache).
