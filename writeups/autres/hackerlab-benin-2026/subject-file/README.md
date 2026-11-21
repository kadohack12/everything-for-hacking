---
title: "Subject File · SMB share caché Recon-Data"
platform: "HackerLab Benin 2026"
category: "ad"
difficulty: "—"
points: 0
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/ad/subject-file.md"
tags: [hackerlab-benin-2026, ad]
status: published
---

# Subject File : Q · SMB share caché Recon-Data

**Catégorie** : AD  
**Flag** : `HLB2026{RECON_VALDORIA_AD_ENUMERATED}`

## TL;DR

Le domaine `valdoria.fbi.lab` expose plusieurs partages SMB. Deux sont des leurres. Le vrai flag est dans `Recon-Data`, un partage non listé accessible uniquement par `svc_web`.

## Reconnaissance

Avec les credentials `svc_web / W3bSvc!2024@FBI` (récupérés dans `ad-connector.properties` sur le broker), l'énumération SMB donne :

```bash
netexec smb <DC_IP> -u svc_web -p 'W3bSvc!2024@FBI' --shares
```

Les partages visibles sont `IPC$`, `SYSVOL`, `NETLOGON`, `IT-Share` et `classified`. Deux pièges :

- `IT-Share` contient `flag-i26.txt` : flag rejeté par la plateforme (leurre).
- `classified` : `ACCESS_DENIED` pour tous les comptes testés (`svc_web`, `svc_mssql`, `svc_certsvc`).

## Share caché

La plateforme indique dans son hint que le partage recherché porte un nom lié à la reconnaissance. `Recon-Data` n'apparaît pas dans l'énumération standard car il est marqué `browseable = no` dans la config Samba.

```bash
smbclient //DC/Recon-Data -U 'VALDORIA.FBI.LAB\svc_web%W3bSvc!2024@FBI'
```

Le partage répond avec un accès en lecture. Il contient `tims_profile.txt` et `ad_security_audit.txt`.

`tims_profile.txt` contient le flag :

```
HLB2026{RECON_VALDORIA_AD_ENUMERATED}
```

`ad_security_audit.txt` contient en bonus les hashes NTLM de `svc_mssql`, `svc_backup`, `svc_web` et `svc_certsvc`, utiles pour les questions suivantes.

## À retenir

`ACCESS_DENIED` sur un share signifie qu'il existe mais que les droits sont insuffisants. `BAD_NETWORK_NAME` signifie qu'il n'existe pas. Un share `browseable = no` n'apparaît pas dans les listings mais répond parfaitement à une connexion directe avec le bon nom.
