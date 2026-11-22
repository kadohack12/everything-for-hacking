---
title: "The Fugitive · The Fugitive"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/the-fugitive/the-fugitive/writeup-the-fugitive.md"
license: "CC BY-SA 4.0"
status: published
---

# The Fugitive — HackerLab 2026 (MISC, 200 pts)

**Flag** : `HLB2026{23c99ee2b06e3deb01ea46e24b10f880}`

## Objectif

Reconstituer une opération d'exfiltration maritime à partir de documents saisis,
des données AIS, du registre maritime et du registre commercial, puis répondre
aux six questions de la plateforme NordMar pour obtenir le flag final.

- Cible : `http://172.28.41.2:80` (NordMar Maritime Platform)
- Instance : `dvpn-83869c92.conf`, subnet `172.28.41.0/24`
- Pièces jointes : `confidential.zip` (DOC-01, DOC-05, DOC-06)
- Format du flag : préfixe `HLB2026` suivi de la valeur entre accolades

## État initial

Le fichier `confidential.zip` et la configuration VPN ont été téléchargés depuis
la plateforme. La cible n'est joignable qu'après établissement du tunnel
WireGuard. Le poste de travail ne dispose pas de `sudo` (`no_new_privs`), mais
Docker est accessible et l'utilisateur appartient au groupe `docker`.

Extraction des pièces :

```bash
mkdir -p Misc/Fugitive && cd Misc/Fugitive
unzip -o ../../confidential.zip
ls -l confidential
```

Sortie :

```
DOC-01_Note_operationnelle_saisie.pdf
DOC-05_Crew_Change_Log_Nordheim.pdf
DOC-06_Carnet_codes_operationnels_BRN.pdf
```

## Reconnaissance

### 1. Documents saisis

```bash
for f in confidential/*.pdf; do
  echo "===== $f ====="
  pdftotext -layout "$f" -
done
```

Points utiles :

- **DOC-01** : opération `COLDWATER`, actif `MS`, pick-up à `Terminal B,
  Nordheim`, `DATE : vendredi 0600`, route `ALPHA → BRAVO → CHARLIE`,
  couverture `maint. tech (temp crew badge)`, handler `M.V. at CHARLIE`.
- **DOC-05** : journal d'embarquement NPA/CCL/2026-11-06/0037. Date
  `2026-11-06`, heure locale `06:00`, terminal `Terminal B`, quai `B-0`
  (dernier chiffre détruit), nom de couverture `Erik Moller`, rôle
  `Temporary maintenance crew`, navire partiellement caviardé, départ
  `approx. 07:20 local`.
- **DOC-06** : codebook BRN.
  - `ALPHA` = Nordheim, `BRAVO` = Kalport, `CHARLIE` = Porto Valdis.
  - `MS` = Mikkel Strand ; `M.V.` = handler non identifié à CHARLIE.
  - `Erik Moller` = couverture de MS (maintenance technician).
  - `COLDWATER` = exfiltration maritime de MS via un navire de charge.

### 2. Plateforme NordMar

L'application expose plusieurs sections statiques et une API d'investigation :

```bash
BASE=http://172.28.41.2
curl -sS "$BASE/api/questions"
curl -sS "$BASE/api/status"
curl -sS "$BASE/data/ais_positions.json" -o ais_positions.json
curl -sS "$BASE/data/registry.json" -o registry.json
curl -sS "$BASE/data/corporate_registry.json" -o corporate_registry.json
curl -sS "$BASE/data/ports.geojson" -o ports.geojson
curl -sS "$BASE/docs/DOC-04-port-bulletin.html" -o DOC-04.html
```

`/api/questions` renvoie six questions (Q01 à Q06) et `/api/submit` attend
`{"question_id": "...", "answer": "..."}` avec le cookie de session.

Le bulletin **DOC-04** (Porto Valdis, 09–10 nov. 2026) donne notamment :

| ETA (UTC) | Navire | IMO | Type | Terminal | Quai | Last Port |
|---|---|---|---|---|---|---|
| 08:00 | KALMAR EXPRESS | 9715438 | Container Ship | Terminal Sud | S-03 | Kalport |
| 11:00 | TERVALIS WIND | 9721542 | Container Ship | Terminal Sud | S-04 | Tervalis |
| 14:00 | SLEIPNIR | 9847322 | General Cargo | Terminal Nord | N-07 | Kalport |
| 16:30 | VALDORIA STAR | 9812640 | General Cargo | Terminal Ouest | O-03 | Nordheim |
| 08:00 (10 Nov) | FENRIR | 9651280 | General Cargo | Terminal Sud | S-02 | Kalport |

Le port de Nordheim est en `UTC+2` dans `ports.geojson` ; le port de Porto
Valdis est en `UTC±0`. Le départ « 07:20 local » de DOC-05 correspond donc à
`05:20 UTC`.

## Analyse AIS

Les données contiennent 4 385 observations et 15 navires. On isole les navires
présents à Nordheim (62.20 N, 5.305 E) le 6 novembre 2026 au matin, puis on
cherche celui qui appareille vers 05:20 UTC.

```python
import json, datetime
ais = json.load(open('ais_positions.json'))
for p in sorted(ais, key=lambda p: p['timestamp_utc']):
    if p['vessel_name'] == 'SLEIPNIR':
        print(p['timestamp_utc'], p['lat'], p['lon'], p['sog'], p['cog'])
```

Extraits significatifs :

```
2026-11-06 03:55 UTC  lat=62.20177 lon=5.30498 sog=0.1   # à quai B-03
2026-11-06 05:20 UTC  lat=62.20007 lon=5.28996 sog=2.7   # appareillage
2026-11-06 05:36 UTC  lat=62.18432 lon=5.28736 sog=12.9  # route au sud
2026-11-06 18:03 UTC  lat=59.84990 lon=7.90019 sog=13.1  # arrivée Kalport
2026-11-06 18:23 UTC  lat=59.84578 lon=7.87963 sog=0.4   # à quai Kalport
2026-11-08 05:06 UTC  lat=59.85000 lon=7.89000 sog=2.9   # départ Kalport
2026-11-08 17:47 UTC  lat=59.80008 lon=2.60001 sog=12.7  # arrivée Porto Valdis
2026-11-08 18:07 UTC  lat=59.80186 lon=2.61375 sog=0.1   # mouillage
```

Le quai de Nordheim correspondant à `lat=62.2018` est `B-03` (B-01 =
62.1982, B-02 = 62.2000, B-03 = 62.2018), ce qui est compatible avec le
`B-0?` partiellement détruit de DOC-05.

Les autres navires présents à Nordheim le 6 novembre :

- `FENRIR` reste à quai jusqu'à 06:30 UTC et appareille à 06:35 UTC
  (08:35 local), soit trop tard pour le départ de 07:20 local.
- `RAN` et `POLAR DAWN` restent à quai.
- `KALMAR EXPRESS` n'est jamais remonté à Nordheim sur la période (latitude
  maximale 59.85).
- `NORDIC PIONEER`, `VALDORIA STAR` et `POLAR DAWN` ont appareillé le
  5 novembre, avant l'embarquement du 6 novembre.

`SLEIPNIR` est donc le seul navire compatible avec l'heure et le quai de
DOC-05. Son track AIS épouse l'itinéraire `Nordheim → Kalport → Porto Valdis`
(cf. `regular_routes` du registre).

## Analyse des registres

`registry.json` donne :

```json
{
  "name": "SLEIPNIR",
  "imo": "9847322",
  "type": "General Cargo",
  "flag": "Norveth",
  "operator": "NordMar Shipping AS",
  "regular_routes": ["Nordheim-Kalport-Porto Valdis", "Nordheim-Kalport"]
}
```

Le registre commercial (`corporate_registry.json`) confirme par ailleurs :

- `Strand Consulting ENK`, dirigeant `Mikkel Strand` (la cible `MS`) ;
- `Borealis Analytics AS`, 12 Havnegata, 3e étage, Nordheim (le local de la
  perquisition FIN-46, maison mère du réseau BRN) ;
- `NordMar Shipping AS`, 12 Havnegata, Nordheim, exploitant de SLEIPNIR,
  FENRIR, NJORD et RAN.

Le bulletin DOC-04 donne le point d'arrivée prévu de SLEIPNIR : **Terminal
Nord, quai N-07, Porto Valdis, ETA 2026-11-09 14:00 UTC**, en provenance de
Kalport. C'est le point d'interception planifié.

## Réponses validées

| Question | Réponse | Justification |
|---|---|---|
| Q01 — Ghost Passenger | `Mikkel Strand` | DOC-06 : `MS` = Mikkel Strand ; registre commercial : Strand Consulting ENK. |
| Q02 — Dead Reckoning | `Nordheim → Kalport → Porto Valdis` | DOC-01 (`ALPHA → BRAVO → CHARLIE`) + DOC-06 + track AIS de SLEIPNIR. |
| Q03 — Shadow Hull | `SLEIPNIR` | Départ de Nordheim B-03 à 05:20 UTC (07:20 local) le 2026-11-06 ; track vers Kalport puis Porto Valdis. |
| Q04 — Hull Number | `9847322` | IMO de SLEIPNIR dans `registry.json`. |
| Q05 — Shell Company | `NordMar Shipping AS` | Champ `operator` de SLEIPNIR dans `registry.json`. |
| Q06 — Last Port of Call | `N-07 / Terminal Nord / Porto Valdis` | DOC-04 : ETA 2026-11-09 14:00 UTC, Terminal Nord, quai N-07. |

Format soumis : les espaces sont remplacés par des `_`, conformément aux
placeholders (`Prenom_Nom`, `Port1_Port2_Port3`, etc.).

## Soumission

Les six réponses ont été envoyées à l'API avec une session HTTP conservée. Dans
l'extrait ci-dessous, chaque valeur est préfixée par le format attendu
(préfixe `HLB2026` + accolades) ; le préfixe est omis pour ne pas recopier de
valeur ressemblant à un flag.

```python
import requests
s = requests.Session()
s.get('http://172.28.41.2/api/questions')
for qid, answer in [
    ('Q01', 'Mikkel_Strand'),
    ('Q02', 'Nordheim_Kalport_Porto_Valdis'),
    ('Q03', 'SLEIPNIR'),
    ('Q04', '9847322'),
    ('Q05', 'NordMar_Shipping_AS'),
    ('Q06', 'N-07_Terminal_Nord_Porto_Valdis'),
]:
    r = s.post('http://172.28.41.2/api/submit',
               json={'question_id': qid, 'answer': answer})
    print(qid, r.status_code, r.json().get('correct'),
          r.json().get('total_validated'))
```

Sortie (sans le flag) :

```
Q01 200 True 1
Q02 200 True 2
Q03 200 True 3
Q04 200 True 4
Q05 200 True 5
Q06 200 True 6
```

La dernière réponse renvoie `all_done: true` et le flag. Le flag est indiqué en tête de ce document.

## Chemins qui ont échoué

1. **WireGuard dans un namespace utilisateur seul** : `unshare -Urn` permet
   bien de créer `wg0` et de configurer l'adresse, mais le namespace n'a pas de
   route vers l'endpoint public. Le handshake reste à `0` et les paquets ICMP
   vers `172.28.41.2` sont perdus. De plus, la résolution DNS de
   `vpn.hackerlab.bj` échoue dans ce namespace.
2. **`wg-quick` avec `sudo`** : impossible, le drapeau `no_new_privs` empêche
   l'élévation.
3. **Résolution de l'endpoint dans le namespace** : `wg setconf` tente de
   résoudre `vpn.hackerlab.bj` et échoue ; il faut utiliser l'IP
   `169.58.54.1` (ou configurer un résolveur accessible).
4. **Candidat `FENRIR`** : même opérateur et même route déclarée, mais départ
   à 08:35 local, incompatible avec les 07:20 de DOC-05.
5. **Session de validation** : la validation des questions est liée à la
   session HTTP. Un premier test de Q04 dans une session séparée a validé la
   réponse, mais la session finale a dû resoumettre les six réponses pour
   obtenir `all_done`.

## Validation reproductible

1. Établir le tunnel WireGuard depuis un conteneur privilégié en réseau hôte
   (le conteneur partage le netns de l'hôte, ce qui donne une route vers
   l'endpoint public) :

   ```bash
   docker run --rm --network host --cap-add NET_ADMIN --cap-add NET_RAW \
     -v /home/kali/HackerLab2026:/cfg:ro redis:7-alpine sh -c '
       apk add --no-cache wireguard-tools iproute2 curl
       wg-quick strip /cfg/dvpn-83869c92.conf > /tmp/wg.conf
       ip link add wg0 type wireguard
       wg setconf wg0 /tmp/wg.conf
       ip addr replace 10.128.110.181/32 dev wg0
       ip link set mtu 1380 dev wg0
       ip link set wg0 up
       ip route replace 172.28.41.0/24 dev wg0
     '
   ```

   Vérifier ensuite :

   ```bash
   ping -c 2 172.28.41.2
   curl -sS http://172.28.41.2/api/questions
   ```

2. Rejouer l'analyse AIS et vérifier le départ de SLEIPNIR à
   `2026-11-06 05:20 UTC`, son passage à Kalport le 6 novembre au soir, puis
   son arrivée à Porto Valdis le 8 novembre au soir.
3. Vérifier dans `DOC-04` la ligne SLEIPNIR : ETA `2026-11-09 14:00 UTC`,
   Terminal Nord, quai `N-07`, last port `Kalport`.
4. Soumettre les six réponses avec une session unique. Attendu :
   `total_validated` passe de 1 à 6 et `all_done` devient `true`.

## Remarque

Le flag final figure en tête de ce document. Le tunnel `wg0` peut être supprimé après
validation avec :

```bash
docker run --rm --network host --cap-add NET_ADMIN redis:7-alpine \
  ip link del wg0
```
