---
title: "Operation BATMAN · Operation BATMAN"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web-osint"
difficulty: "—"
points: 500
os: "—"
date: 2026-11-20
author: "5c0r7"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/operation-batman/operation-batman-harmattan/writeup-harmattan.md"
license: "CC BY-SA 4.0"
status: published
---

---
title: "HARMATTAN — Localisation d'Erik Lindberg"
ctf: "HLB2026"
date: 2026-11-17
category: "web / osint"
difficulty: medium
points: 500
flag_format: "HLB2026{...}"
author: "Batman"
---

# HARMATTAN

## Résumé

Le portail HARMATTAN est une application web statique contenant les pièces du dossier JANUS : documents, chronologie, communications, finances et traces OSINT. La localisation finale s'obtient en reliant les alias de Lindberg aux traces Instagram, au forum et aux activités Strava.

## Solution

### 1. Récupération des données

Le HTML révèle deux fichiers importants : `data.js` et `app.js`.

```bash
BASE=http://172.28.29.2:8080
curl -s "$BASE/data.js" -o harmattan-data.js
curl -s "$BASE/app.js" -o harmattan-app.js
curl -s "$BASE/" -o harmattan.html
```

Les questions sont visibles dans `data.js`, et `app.js` montre les endpoints de validation :

```text
POST /api/check
POST /api/submit
```

### 2. Corrélation des identités et de la localisation

Le graphe et les documents donnent la chaîne d'alias suivante :

```text
Erik LINDBERG → Gabor VARGA → Matias ECHEVARRIA
```

Les éléments utiles sont :

- le faux passeport hongrois utilisé pour la location : `HU-BA 9022918` ;
- le compte crypto géorgien au nom de Matias Echeverria ;
- le compte Instagram affiché : `@matias.echeverria.ar` ;
- le forum mentionne le quartier Vera et la rue Barnov ;
- la photo Instagram du 27/10 montre la plaque `Barnov St. 16` devant le Caffe Verdi ;
- Strava montre quatre départs sur le trottoir nord, entre les numéros 16 et 20, avec l'appartement au 3e étage.

La vérification directe de la question 28 confirme l'adresse :

```bash
curl -s -X POST http://172.28.29.2:8080/api/check \
  -H 'Content-Type: application/json' \
  --data '{"id":28,"answer":"20 rue Barnov"}'
```

Réponse :

```json
{"ok":true}
```

La localisation est donc **20 rue Barnov, Tbilissi, quartier Vera, appartement au 3e étage**.

### 3. Validation finale

Les trois puzzles se résolvent en regroupant les éléments par ordre chronologique, circuit financier et identité. Le score obtenu avec les réponses validées et les puzzles terminés est de 475/490, au-dessus du seuil de 440 points.

```python
import json
import urllib.request

BASE = "http://172.28.29.2:8080"

answers = {
    1: "Renault Kangoo",
    2: "Gabor Varga",
    3: "HU-BA 9022918",
    4: "10:35",
    5: "Mirova-Sud",
    6: "Hotel Baobab, chambre 24",
    7: "Tariel Gelashvili",
    8: "Caucasus Freight Solutions LLC",
    9: "Toyota Hilux",
    10: "Boreal Trade Consulting Ltd",
    11: "Danube River Logistics Kft",
    12: "Gabor Varga",
    13: "Nordic Shield Consulting AS",
    14: "4",
    15: "BTC-Caucasus",
    16: "Matias Echeverria",
    17: "Kaltyr Star",
    18: "Kadikoy",
    19: "Sarpi",
    20: "@matias.echeverria.ar",
    21: "Kadikoy",
    22: "Mtatsminda",
    23: "Caffe Verdi",
    24: "Barnov",
    25: "Ingrid Solvang",
    26: "Egersund",
    27: "Tbilissi, Erevan, Doha, Buenos Aires",
    28: "20 rue Barnov",
}

solved = {str(i): True for i in range(1, 29)}
puzzles = {
    "route": {str(i): i for i in range(8)},
    "argent": {str(i): i for i in range(8)},
    "visages": {
        "0": 0, "1": 3, "2": 6,
        "3": 1, "4": 4, "5": 7,
        "6": 2, "7": 5, "8": 8,
    },
}

body = json.dumps({
    "answers": {str(k): v for k, v in answers.items()},
    "solved": solved,
    "puzzles": puzzles,
}).encode()

req = urllib.request.Request(
    BASE + "/api/submit",
    data=body,
    headers={"Content-Type": "application/json"},
)
print(urllib.request.urlopen(req).read().decode())
```

Sortie obtenue :

```json
{"score":475,"threshold":440,"flag":"HLB2026{REDACTED}"}
```

## Flag

```text
HLB2026{REDACTED}
```
