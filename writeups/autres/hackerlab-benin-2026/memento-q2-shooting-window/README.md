---
title: "Memento Q2 · Shooting Window"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/memento/02-shooting-window.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# The Fall of Memento : Q2 · Shooting window (100 pts)

> *« Donne la destination réelle et l'heure locale d'arrivée. »*

Format : `HLB2026{Ville-HH:MM}`

## TL;DR

Le PDF417 de la carte d'embarquement + la grille `KalAir` dans `data.js` donnent la 3e étape : **Charter KA088 KVX→KDR jour 137, arrivée 17:25**.

**Flag** : `HLB2026{Kaltyr-Durn-17:25}`

## Déduction

Le post-it (`exhibit-C.jpg`) dit :

```
Vexholm : laisser filer
charter KA0.. (pas la ligne)
```

Le PDF417 confirme la ligne cachée du billet :

```
QR4T9Z KVXKDRKA 0088 137Y014C0044 ... KA088/137 OPR KALAIR
```

Grille horaires dans `data.js` :

```js
["KA088","KVX -> KDR","137","15:40","17:25"]
```

## Flag

```
HLB2026{Kaltyr-Durn-17:25}
```
