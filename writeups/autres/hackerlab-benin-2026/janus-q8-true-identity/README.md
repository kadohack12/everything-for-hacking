---
title: "JANUS Q8 · True Identity"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/08-true-identity.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q8 · True Identity (100 pts)

> *« Retrouvez l'alias utilisé par l'attaquant et son nom complet. »*

Format : `HLB2026{alias_nomcomplet}`

## TL;DR

Les IOCs du ransomware (hash SHA-256, mots-clés `BURNOUT`, `ASHEN`, `LYNX_FNS_ASHEN_TRIBUNAL_2026`) remontent à un pseudo sur la plateforme d'intel `feu.hackerlab.bj`.

**Flag** : `HLB2026{kr4ven_Simon Vermont}`

## IOCs collectés

Depuis le ransomware `calc.exe` :

| Type     | Valeur                                                             |
|----------|---------------------------------------------------------------------|
| SHA-256  | `09c36f6f39d44cc38c20102518890127de07a37fbf8b64541f662eebe8c29ea7` |
| MD5      | `1eeceb30b865633399228000fd7391fe`                                  |
| Name     | `BURNOUT` ransomware                                                |
| Magic    | `ASH2` (ASHEN)                                                      |
| Seed clé | `LYNX_FNS_ASHEN_TRIBUNAL_2026`                                      |
| Group    | *« Division Cyber FNS »* / *« Opérations LYNX »*                    |

Du webshell `allmatter.php` :

- MD5 contenu : `3daef9f35026dffa8a340b7a19528855cdb4ddb75135164bac448eedaef8607d`
- MD5 de la clé : `d490fcf74fd30358ebc9d7591c820b27`

## Recherche OSINT

Sur `feu.hackerlab.bj` (plateforme d'intel fournie avec un ID + mot de passe par le CTF), la recherche sur **`BURNOUT`** ou le SHA-256 remonte une fiche :

```
Persons 1
Simon Vermont
alias "kr4ven" · ACTIVE
```

## Flag

```
HLB2026{kr4ven_Simon Vermont}
```
