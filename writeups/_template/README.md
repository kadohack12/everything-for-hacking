---
# Métadonnées obligatoires — voir CONTRIBUTING.md
title: "Nom de la machine"
platform: "Hack The Box"          # doit correspondre au dossier : writeups/hackthebox/
category: "Machine"               # Machine | Room | crypto | web | reverse | pwn | forensics | hardware | misc
os: "Linux"                       # libre : Linux | Windows | Android | —
difficulty: "Easy"                # libre : Intro | Easy | Medium | Hard | Insane
date: 2026-01-01                  # AAAA-MM-JJ
author: "Prénom Nom ou pseudo"
# author_github: "ton-login"      # optionnel : lien vers ton profil dans l'index
tags: [nmap, web, privesc]
status: draft                     # draft tant que la machine est active, puis published
---

# Nom de la machine — Hack The Box (Linux, Easy)

> **TL;DR** — Service web vulnérable → shell `www-data` → binaire SUID maison → root.

## Sommaire

- [Reconnaissance](#reconnaissance)
- [Énumération](#énumération)
- [Accès initial](#accès-initial)
- [Élévation de privilèges](#élévation-de-privilèges)
- [Flags](#flags)
- [Leçons](#leçons)

## Reconnaissance

```bash
nmap -sC -sV -oA nmap/initial 10.10.10.10
```

![Scan nmap](assets/01-nmap.png)

| Port | Service | Version |
| --- | --- | --- |
| 22 | ssh | OpenSSH 8.9 |
| 80 | http | nginx 1.18 |

## Énumération

...

![Énumération web](assets/02-enum.png)

## Accès initial

...

![Exploit](assets/03-exploit.png)

## Élévation de privilèges

...

## Flags

```text
user.txt : 1a2b3c4d...e5f6
root.txt : 9f8e7d6c...b3a2
```

## Leçons

- ...
- ...
