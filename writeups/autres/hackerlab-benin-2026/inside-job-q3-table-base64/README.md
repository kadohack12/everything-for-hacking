---
title: "Inside Job Q3 · Table convoy_route"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/misc/inside-job3.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# Inside Job : Q3 · Table convoy_route en base64

**Catégorie** : misc  
**Flag** : `HLB2026{c0nv01_fbl0847_1nt3rc3pt_a3f91c}`

## TL;DR

L'API vault expose un asset véhicule `VDC-FBL-0847` dont les métadonnées indiquent une table SQL interne `convoy_route`. Un SELECT sur cette table depuis le Postgres vault révèle un waypoint avec un payload base64 contenant le flag.

## Contexte

Depuis le shell RCE `www-data` (Q1), on a accès au Postgres `vdc_vault` avec les credentials de `wp-config.php`. L'API vault expose `/api/assets` pour lister les actifs avec un JWT Bearer admin.

```bash
curl -H "Authorization: Bearer <JWT>" http://vault:5000/api/assets
```

L'asset `VDC-FBL-0847` (id=4) a dans ses métadonnées :

```json
{
  "route_table": "convoy_route (SQL interne)",
  "transport": "Siege -> Datacenter Valmere"
}
```

L'endpoint `/api/fleet/4/location` retourne uniquement la position actuelle au garage, pas l'itinéraire complet.

## Requête SQL

```sql
SELECT * FROM convoy_route WHERE vehicle_id=4 ORDER BY seq;
```

L'itinéraire complet :

| seq | segment | note | coords |
|-----|---------|------|--------|
| 1 | SECURE | Départ garage | 6.3702,2.3912 |
| 2 | SECURE | Périphérique nord | 6.3661,2.4055 |
| 3 | EXPOSED | Sortie 12 | 6.3510,2.4330 |
| 4 | EXPOSED | Zone industrielle | 6.3482,2.4410 |
| 5 | EXPOSED | Pont-bascule Sudhafen | 6.3455,2.4502 |
| 6 | EXPOSED | Corridor logistique | 6.3460,2.4610 |
| 7 | SECURE | Entrée Datacenter Valmere | 6.3530,2.4901 |

Le waypoint seq=5 a un champ supplémentaire `payload_b64` :

```
SExCMjAyNntjMG52MDFfZmJsMDg0N18xbnQzcmMzcHRfYTNmOTFjfQ==
```

```bash
echo "SExCMjAyNntjMG52MDFfZmJsMDg0N18xbnQzcmMzcHRfYTNmOTFjfQ==" | base64 -d
# HLB2026{c0nv01_fbl0847_1nt3rc3pt_a3f91c}
```

## Pièges

Chercher l'asset par plaque `VDC-FBL-0847` en path (`/api/assets/VDC-FBL-0847`) retourne 404. L'API utilise l'id numérique : `/api/assets/4`. L'endpoint `/api/fleet/4/location` ne donne que la position en temps réel, pas les waypoints de l'itinéraire planifié.
