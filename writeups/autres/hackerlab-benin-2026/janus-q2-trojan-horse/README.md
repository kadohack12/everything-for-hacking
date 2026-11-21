---
title: "JANUS Q2 · The Trojan Horse"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/02-trojan-horse.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q2 · The Trojan Horse (100 pts)

> *« Un fichier malveillant a été introduit sur le portail puis exploité. Identifiez : le nom du fichier malveillant, l'IP source, la dernière authentification réussie. »*

Format : `HLB2026{nom_IP_JJ-MM-AAAA HH:MM:SS}`

## TL;DR

Déchiffrement en masse des artefacts ransomware → Apache `access.log` → corrélation avec les sessions `/connexion` du portail.

**Flag** : `HLB2026{allmatter.php_45.137.22.198_08-11-2026 17:17:13}`

## Déchiffrement des logs

Avec la clé maître dérivée en Q1 (`f5d5ea867ed402236e78e156ddf1468d`), on déchiffre les artefacts clés :

```bash
python3 decrypt.py C/xampp/htdocs/uploads/allmatter.php.enc \
                   C/xampp/apache/logs/access.log.txt.enc \
                   C/xampp/htdocs/index.php.enc
```

## Analyse du webshell

`allmatter.php` (5682 octets) est un webshell PHP minimaliste avec :

- écran de login protégé par MD5 : `d490fcf74fd30358ebc9d7591c820b27`
- shell interactif `shell_exec($_POST['c'])`
- actions rapides : `net user svc_backup P@ssw0rd!2026 /add`, activation RDP…

Le double-extension classique a été utilisé pour bypasser le filtre upload :

```
GET /uploads/allmatter.php.pdf HTTP/1.1 200 5682
```

## Corrélation access log

L'application (`index.php`) route `POST /connexion` → `302 /tableau-de-bord` quand le login réussit (le fail redirige vers `/`).

Script de reconstitution de sessions :

```python
import re
pat = re.compile(r'^(\d+\.\d+\.\d+\.\d+) - - \[([^\]]+)\] "(\w+) (\S+)')
sessions = {}
for line in open("access.log.txt"):
    m = pat.match(line)
    if not m: continue
    ip, ts, method, path = m.groups()
    if path == "/connexion" and method == "POST":
        sessions[ip] = ts
    elif path == "/tableau-de-bord" and method == "GET" and ip in sessions:
        print(f"OK  {ip}  {sessions.pop(ip)}")
```

Deux sessions attaquant visibles :

| IP               | 1er login OK          | Commentaire                       |
|------------------|-----------------------|-----------------------------------|
| `185.220.101.47` | `07/Nov 23:14:16 UTC` | Tor exit : dépose `update.php`    |
| `45.137.22.198`  | `08/Nov 16:15:24 +01` | 2e session, dépose `allmatter.php` |
| `45.137.22.198`  | `08/Nov 17:17:13 +01` | **dernière auth réussie** du dossier |

Le fichier **exploité** (celui qui sert pour la post-expl) est bien `allmatter.php`. La timestamp du flag est celle du dernier `302 /connexion` côté attaquant (horodatage Apache tel-quel, +01 CET sur le serveur).

## Flag

```
HLB2026{allmatter.php_45.137.22.198_08-11-2026 17:17:13}
```
