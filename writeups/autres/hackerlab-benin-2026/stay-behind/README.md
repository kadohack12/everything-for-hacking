---
title: "Stay Behind · AWS IAM persistence"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/web/stay_behind.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Stay Behind : Web · AWS IAM Persistence

**Catégorie** : web  
**Flag** : `HLB2026{2c769d9f441def112ad098192a7a3bb9}`

## TL;DR

Un bucket S3 public expose des credentials AWS. Avec ces creds on remonte jusqu'à un rôle Lambda, on y insère une trust policy wildcard qui survit au sweep IR, puis on ré-assume ce rôle après le nettoyage pour lire le canary dans S3.

## Reconnaissance

Le service expose un bucket `campaign-backup.zip` en accès public. L'archive contient des credentials AWS en clair :

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

Ces credentials appartiennent à `svc-campaign-ingest`. Une énumération IAM montre qu'il peut invoquer la Lambda `campaign-scheduler` et en modifier le code (`UpdateFunctionCode`). En remontant les droits attachés au rôle d'exécution `campaign-scheduler-exec`, on constate qu'il peut également appeler `UpdateAssumeRolePolicy`.

## Pivot vers la persistance

La plateforme expose un endpoint `POST /_ctf/run-ir` qui simule un Incident Response : il révoque les identités créées depuis T0, supprime les utilisateurs IAM, les clés, et modifie le code Lambda. Ce que le sweep ne touche pas : les trust policies des rôles existants.

Avant de déclencher l'IR, on modifie la trust policy de `campaign-scheduler-exec` pour autoriser n'importe quel principal AWS :

```json
{
  "Effect": "Allow",
  "Principal": {"AWS": "*"},
  "Action": "sts:AssumeRole"
}
```

## Post-IR

Une fois le sweep déclenché via `POST /_ctf/run-ir`, toutes les clés d'avant sont mortes. On ouvre une nouvelle session STS sans credentials préalables (`AssumeRole` sur le rôle désormais ouvert), et on accède à `s3://vdc-coord-audit/flag.canary` :

```
HLB2026{2c769d9f441def112ad098192a7a3bb9}
```

## À retenir

Les trust policies IAM sont souvent oubliées lors d'un nettoyage d'incident. Un `UpdateAssumeRolePolicy` sur un rôle existant est suffisant pour maintenir un accès persistant même si toutes les clés créées sont révoquées.
