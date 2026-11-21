---
title: "Harmattan Q1 · Operation BATMAN"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 500
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/harmattan/01-operation-batman.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# HARMATTAN : Operation BATMAN (500 pts)

> *« Exploitez les données disponibles pour localiser Erik Lindberg, l'un des agents en fuite, avant qu'il ne parvienne à quitter le territoire. »*

## TL;DR

Le portail est une SPA Vanilla JS dont **toutes les données sont dans `data.js`**. Les questions sont validées via `POST /api/check` et le flag se récupère via `POST /api/submit` une fois le seuil atteint (440/490 pts).

**Flag** : `HLB2026{69d52d35b2c0e69a7be69c38cf7c0f39}` (unique à chaque session).

## Approche

### 1. Reconnaissance

```bash
curl http://172.28.X.2:8080/data.js -o data.js
curl http://172.28.X.2:8080/app.js  -o app.js
```

Dans `app.js` :

```js
xhr.open('POST', '/api/check');
xhr.send(JSON.stringify({id: id, answer: a}));
...
xhr.open('POST', '/api/submit');
xhr.send(JSON.stringify({answers, solved, puzzles}));
```

Dans `data.js` les 28 questions (`QS`) et 3 puzzles (`PZ`).

### 2. Données aléatoires par session

Attention : certaines valeurs sont **randomisées à chaque spawn d'instance** (numéro de passeport, heure de passage frontière, numéro du café dans la rue Barnov…). Il faut **re-fetch `data.js`** sur l'instance active, pas copier/coller un writeup existant.

### 3. Recoupement des 28 réponses

| # | Question                              | Réponse                                  |
|---|---------------------------------------|------------------------------------------|
| 1 | Véhicule pour quitter Zanthara        | Renault Kangoo                           |
| 2 | Identité de location                  | VARGA Gabor                              |
| 3 | N° passeport (contrat AutoPlus)       | `HU-BA XXXXXXX` (randomisé)              |
| 4 | Heure frontière Mirova-Sud            | `HH:MM` (randomisé)                      |
| 5 | Poste-frontière                       | Mirova-Sud                               |
| 6 | Logement à Mirova                     | Hôtel Baobab                             |
| 7 | Vrai nom de « M. Taro »               | Tariel GELASHVILI                        |
| 8 | Société de Gelashvili                 | Caucasus Freight Solutions LLC           |
| 9 | Véhicule après le Kangoo              | Toyota Hilux                             |
| 10| Propriétaire du Hilux                 | Boreal Trade Consulting Ltd              |
| 11| Premier destinataire Nordic Shield    | Danube River Logistics Kft               |
| 12| Directeur Danube River                | Gabor VARGA                              |
| 13| Source des fonds JANUS                | Nordic Shield Consulting AS              |
| 14| Nombre de sociétés-écrans             | 4 (CF est prestataire)                   |
| 15| Exchange crypto géorgien              | BTC-Caucasus                             |
| 16| Identité du compte crypto             | Matias ECHEVERRIA                        |
| 17| Moyen de transport quitter Mirova     | Ferry (MV Kaltyr Star)                   |
| 18| Quartier Istanbul                     | Kadıköy                                  |
| 19| Poste-frontière Géorgie               | Sarpi                                    |
| 20| Compte Instagram                      | `matias.echeverria.ar` *                  |
| 21| Quartier photo 19/10                  | Kadıköy                                  |
| 22| Site photo 23/10                      | parc de Mtatsminda                       |
| 23| Café fréquenté                        | Caffe Verdi                              |
| 24| Rue (Strava)                          | rue Barnov                               |
| 25| Propriétaire +47                      | Ingrid SOLVANG                           |
| 26| Ville d'Ingrid                        | Egersund                                 |
| 27| Itinéraire billet                     | Tbilissi, Erevan, Doha, Buenos Aires     |
| 28| Adresse actuelle                      | `N rue Barnov` (café à `N-4`, Strava `N±1`) |

*Q20 peut poser problème selon la session.

### 4. Les 3 puzzles

Format du JSON attendu : `{"route": {"0":0,"1":1,...}, "argent": {...}, "visages": {...}}`

```json
{
  "route":   {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7},
  "argent":  {"0":0, "1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7},
  "visages": {"0":0, "1":3, "2":6, "3":1, "4":4, "5":7, "6":2, "7":5, "8":8}
}
```

Ces indices correspondent à l'ordre canonique des chips défini dans `PZ` → chaque slot `k` reçoit la chip d'index `k` (pour les deux premiers), et le mix 3-par-3 pour `visages`.

### 5. Submit

Seuil : **440 pts**. Tant que tu totalises ≥ 440 avec les Q réussies + puzzles × 30, tu obtiens le flag.

```python
r = requests.post(f"{B}/api/submit", json={
    "answers": answers,
    "solved": {str(k): True for k in answers},
    "puzzles": puzzles
}).json()
# → {"score": 440, "threshold": 440, "flag": "HLB2026{...}"}
```

## Script complet

```python
import json, urllib.request
B = "http://172.28.X.2:8080"

def post(p, body):
    req = urllib.request.Request(B+p, data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

answers = {
 1:"Renault Kangoo", 2:"VARGA Gabor", 3:"HU-BA XXXXXXX",  # ← relire data.js
 4:"HH:MM", 5:"Mirova-Sud", 6:"Hôtel Baobab",
 7:"Tariel GELASHVILI", 8:"Caucasus Freight Solutions LLC",
 9:"Toyota Hilux", 10:"Boreal Trade Consulting Ltd",
 11:"Danube River Logistics Kft", 12:"Gabor VARGA",
 13:"Nordic Shield Consulting AS", 14:"4", 15:"BTC-Caucasus",
 16:"Matias ECHEVERRIA", 17:"ferry", 18:"Kadıköy", 19:"Sarpi",
 20:"matias.echeverria.ar", 21:"Kadıköy", 22:"parc de Mtatsminda",
 23:"Caffe Verdi", 24:"rue Barnov", 25:"Ingrid SOLVANG",
 26:"Egersund", 27:"Tbilissi, Erevan, Doha, Buenos Aires",
 28:"N rue Barnov",  # ← café N-4 selon data.js
}
solved = {str(k): post("/api/check", {"id":k,"answer":v}).get("ok", False)
          for k, v in answers.items()}

puzzles = {
    "route":   {str(i): i for i in range(8)},
    "argent":  {str(i): i for i in range(8)},
    "visages": {str(i): c for i, c in enumerate([0,3,6,1,4,7,2,5,8])},
}

print(post("/api/submit", {"answers":answers, "solved":solved, "puzzles":puzzles}))
```

## Flag

```
HLB2026{69d52d35b2c0e69a7be69c38cf7c0f39}
```
