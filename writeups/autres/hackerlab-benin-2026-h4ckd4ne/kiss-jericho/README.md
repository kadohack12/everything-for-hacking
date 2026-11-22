---
title: "Kiss · Jericho"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "W1z4rd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/kiss/jericho/writeup-jericho.md"
license: "CC BY-SA 4.0"
status: published
---

# Jericho — Opération RESSAC (simulation de perquisition)

## Objectif

Après l'interpellation de Mikkel STRANDHJELM, l'équipe tactique perquisitionne l'appartement 3B. Le challenge demande de placer sous scellés les **18 éléments d'intérêt** de la scène :

- 4 à l'entrée ;
- 4 dans le séjour ;
- 4 dans la chambre ;
- 6 au niveau du bureau.

Cible : `http://172.28.28.2:8080` (challenge la plateforme **Jericho**, forensics, 100 pts).

## État initial

- Instance VPN `dvpn-ef6a9b0a.conf`, subnet `172.28.28.0/24`.
- Application web « Opération RESSAC — Simulation de perquisition » (SPA Vite/React).
- Page d'accueil : « Lancer l'intervention », boutons `Scellés`, `Journal`, `Clôturer la perquisition`.
- Le bundle JS expose les éléments de la scène et une API de partie.

## Reconnaissance

Le bundle principal est `assets/index-OeMI0vsb.js`. Il contient :

- les objets de la scène (`id`, `name`, `room`, `seal`, `inside`, `action`, `open`, `findings`) ;
- une fonction `hi(r,e)` qui appelle `POST /api/<r>` avec un corps JSON et `credentials: same-origin` ;
- les endpoints utilisés par l'application :
  - `POST /api/new` : démarre/redémarre une partie ;
  - `POST /api/open` : ouvre un meuble/contenant (`{"id":"...","open":true}`) ;
  - `POST /api/action` : exécute une action de fouille (`{"id":"..."}`) ;
  - `POST /api/seal` : place un élément sous scellé (`{"id":"..."}`) ;
  - `POST /api/unseal` : retire un scellé ;
  - `POST /api/finish` : clôture et renvoie le flag si les scellés sont conformes.

Le serveur refuse une clôture avec un message générique :

```
403 {"ok":false,"error":"Clôture refusée : le magistrat estime que les scellés ne correspondent pas aux éléments d'intérêt de l'enquête. Reprenez la fouille."}
```

## Identification des 18 éléments

Le bundle liste 25 objets portant un code `seal` (donc potentiellement scellables). Les **contenants** (sac poubelle, carton, paquet de cigarettes, livre, cadre, valise) ne sont pas les éléments d'intérêt : ils cachent le vrai contenu. Les éléments à sceller sont les objets découverts, y compris les objets cachés révélés par une action ou une ouverture.

### Entrée (4)

| Id | Élément | Justification |
|---|---|---|
| `cam` | Caméra IP | Logement microSD vide, carte retirée |
| `receipt` | Reçu de transfert déchiré | Caché dans le sac poubelle ; transfert de 4 900 € vers NORDVEL TRADING LTD |
| `simbox` | Boîtier SIM box artisanal | Caché dans le carton ; passerelle GSM 16 SIM |
| `wallet` | Portefeuille | Carte d'identité de Mikkel STRANDHJELM |

Les contenants `trash` (sac) et `parcel` (carton) ne sont pas scellés.

### Séjour (4)

| Id | Élément | Justification |
|---|---|---|
| `compass_watch` | Montre à aiguilles | Portée par l'interpellé, arrêtée sur 12 |
| `phone` | Smartphone personnel | Notification anti-forensique, verrouillé |
| `microsd` | Carte microSD | Cachée dans le paquet de cigarettes |
| `usb` | Clé USB | Cachée dans le livre ; archive `kit_heliance_v3.zip` |

Les contenants `cigs` et `book` ne sont pas scellés.

### Chambre (4)

| Id | Élément | Justification |
|---|---|---|
| `pistol` | Pistolet semi-automatique | Tiroir de la table de chevet, numéro limé |
| `envelope` | Enveloppe dissimulée | Derrière le cadre photo ; phrase de récupération crypto (12 mots) |
| `cash` | Liasses de billets | Dans la valise ; 18 400 € |
| `burner` | Téléphone à clapet | Dans la valise ; contact unique « C » |

Les contenants `frame` (cadre) et `suitcase` (valise) ne sont pas scellés. La valise est **dans l'armoire** : il faut d'abord ouvrir `ward_r`, puis `suitcase`, pour que `cash` et `burner` soient découverts.

### Bureau (6)

| Id | Élément |
|---|---|
| `laptop` | Ordinateur portable allumé, session verrouillée |
| `notebook` | Carnet de comptabilité manuscrite |
| `mail` | Courrier au nom de Thomas RIVES |
| `postit` | Post-it avec un mot de passe (redacté) |
| `cards` | Cartes bancaires de tiers |
| `sims` | Lot de cartes SIM prépayées |

## Exploitation (API)

Les appels se font avec le cookie de session de l'application (`credentials: same-origin`). Séquence reproductible :

```bash
BASE=http://172.28.28.2:8080

# 1) Nouvelle partie
curl -s -X POST "$BASE/api/new"

# 2) Ouvrir l'armoire AVANT la valise (la valise est rangée dedans)
curl -s -X POST "$BASE/api/open" -H 'Content-Type: application/json' -d '{"id":"ward_r","open":true}'
curl -s -X POST "$BASE/api/open" -H 'Content-Type: application/json' -d '{"id":"suitcase","open":true}'

# 3) Ouvrir les tiroirs / meubles contenant les éléments du bureau et de la chambre
for id in desk_drawer cab_d2 cab_d3 ns_drawer; do
  curl -s -X POST "$BASE/api/open" -H 'Content-Type: application/json' -d "{\"id\":\"$id\",\"open\":true}"
done

# 4) Fouiller les contenants (révèle les objets cachés)
for id in trash parcel cigs book frame; do
  curl -s -X POST "$BASE/api/action" -H 'Content-Type: application/json' -d "{\"id\":\"$id\"}"
done

# 5) Placer les 18 éléments sous scellé
for id in cam receipt simbox wallet \
          compass_watch phone microsd usb \
          pistol envelope cash burner \
          laptop notebook mail postit cards sims; do
  curl -s -X POST "$BASE/api/seal" -H 'Content-Type: application/json' -d "{\"id\":\"$id\"}"
done

# 6) Clôturer
curl -s -X POST "$BASE/api/finish"
```

La clôture renvoie alors `{"ok":true,"flag":"[flag redacted]"}`.

## Chemins qui ont échoué

- Sceller un seul élément (`wallet`) : `403`, les scellés ne correspondent pas.
- Sceller 16 éléments sans `cash` et `burner` : `403`.
- Sceller `cash`/`burner` avant d'ouvrir la valise : `409 Élément non accessible : il n'a pas encore été découvert.`
- Ouvrir `suitcase` avant `ward_r` : `409 Action impossible sur cet élément.` (la valise est dans l'armoire).
- Sceller les contenants (`trash`, `parcel`, `cigs`, `book`, `frame`, `suitcase`) : ce ne sont pas les éléments d'intérêt ; le contenu doit être découvert puis scellé.

## Validation

1. Appeler `POST /api/new` pour repartir d'une scène propre.
2. Rejouer les ouvertures dans l'ordre (`ward_r` → `suitcase`, puis les tiroirs), les actions de fouille, puis les 18 `seal`.
3. Vérifier que les 18 appels `seal` répondent `200 {"ok":true,"n":...}` (numéros 1 à 18).
4. Appeler `POST /api/finish` : la réponse doit être `200 {"ok":true,...}`. Le flag renvoyé est le secret du challenge ; il est volontairement **redacté** ici.

## Remarque

Le flag n'apparaît nulle part dans ce document. La valeur soumise n'est pas reproduite ici.
