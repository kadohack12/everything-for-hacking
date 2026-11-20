---
title: "NomMachine"
platform: "Hack The Box"
category: "Machine"
os: "Linux"
difficulty: "Easy"
date: 2026-01-01
tags: [nmap, web, privesc]
status: draft
---

# NomMachine — Hack The Box (Linux, Easy)

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
