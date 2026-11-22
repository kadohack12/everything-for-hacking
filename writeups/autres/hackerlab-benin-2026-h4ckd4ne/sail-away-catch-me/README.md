---
title: "Sail Away · Catch Me"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "osint"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Sh1n"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/sail-away/catch-me/writeup-catch-me.md"
license: "CC BY-SA 4.0"
status: published
---

# Catch me — Sail Away (OSINT, 100 pts, q:1)

## Objectif

Retrouver la ville où se cache **Kjell Runvik**, officier junior de Norveth,
disparu, à partir du pseudonyme laissé dans ses fichiers :

```text
paul_morphy_r
```

Le flag attend la ville en minuscules, sans accent.

## État initial

- Challenge OSINT `Catch me`, mission `Sail Away`.
- Aucun fichier joint ; seul le pseudonyme est fourni.
- Un dump du téléphone/traces de Runvik a été déchiffré (17 028 fichiers,
  arborescence `Users/` incluse) : ni `paul_morphy_r` ni `Runvik` n'y
  apparaissent. C'est une impasse pour cette piste.

## Reconnaissance

Le pseudonyme a été passé dans Sherlock :

```bash
sherlock paul_morphy_r --timeout 8 --print-found --no-color
sherlock paulmorphyr  --timeout 8 --print-found --no-color
```

Comptes trouvés (entre autres) :

```text
Chess.com   https://www.chess.com/member/paul_morphy_r
7Cups       https://www.7cups.com/@paul_morphy_r
Envato      https://forums.envato.com/u/paul_morphy_r
F3.cool     https://f3.cool/paul_morphy_r/
TikTok      https://www.tiktok.com/@paul_morphy_r
Venmo       https://account.venmo.com/u/paul_morphy_r
omg.lol     https://paul_morphy_r.omg.lol
```

D'autres profils avaient été signalés par un scan précédent : Mercado Livre,
OpenNet, forum php.ru, Mastodon `tchncs.de`, Threads `@paul_morphy_r`.

Le profil **Chess.com** est le plus utile : le pseudonyme est une référence
directe au joueur d'échecs Paul Morphy, et Chess.com expose une API publique.

```bash
curl -s https://api.chess.com/pub/player/paul_morphy_r
```

Réponse utile :

```json
{
  "username": "paul_morphy_r",
  "country": "https://api.chess.com/pub/country/EE",
  "joined": 1794580311,
  "last_online": 1794666721
}
```

Le code pays **EE** correspond à l'**Estonie**. Le contexte de la mission
(port, yacht, fuite par la mer) et la capitale portuaire désignent la ville
soumise. La valeur exacte du flag est enregistrée dans le la plateforme et n'est pas
recopiée ici.

## Pistes qui n'ont pas abouti

- **Dump téléphone** : le pseudonyme et le nom de Runvik n'y figurent pas.
- **omg.lol** : `https://omg.lol/paul_morphy_r` renvoie une page « Not found »
  et `https://paul_morphy_r.omg.lol` ne résout pas (underscore dans le nom
  d'hôte) ; le profil n'a pas fourni de ville.
- **Mercado Livre / OpenNet / php.ru** : profils inaccessibles ou sans champ de
  localisation exploitable.
- **Threads** : profil derrière un mur de connexion ; impossible à lire sans
  compte.
- **Mastodon tchncs.de** : `https://tchncs.de/@paul_morphy_r` et l'API de
  lookup renvoient 404 au moment du test.
- **TikTok / Venmo / 7Cups / Envato** : pas de ville publique ou page vide.

## Raisonnement

1. Le pseudonyme est un indice de type « nom de joueur d'échecs ».
2. Sherlock confirme un compte Chess.com actif portant exactement ce nom.
3. L'API Chess.com expose le pays du compte : `EE`.
4. `EE` = Estonie ; la mission parle d'un départ par la mer et d'un port.
5. La ville portuaire attendue est la capitale estonienne, à soumettre en
   minuscules sans accent.

## Validation reproductible

```bash
curl -s https://api.chess.com/pub/player/paul_morphy_r | \
  python3 -c 'import sys,json; print(json.load(sys.stdin)["country"])'
# https://api.chess.com/pub/country/EE
```

Soumettre la ville correspondante au format du challenge (minuscules, sans
accent). La plateforme a accepté la valeur (challenge déjà marqué résolu pour
l'équipe).
