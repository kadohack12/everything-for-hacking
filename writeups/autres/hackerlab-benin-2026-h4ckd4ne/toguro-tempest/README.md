---
title: "Toguro Tempest · Toguro Tempest"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc"
difficulty: "—"
points: 500
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/toguro-tempest/toguro-tempest/writeup-toguro-tempest.md"
license: "CC BY-SA 4.0"
status: published
---

# Toguro Tempest — Tempest Press (MISC, 500 pts)

## Objectif

Neutraliser le pipeline de publication automatique de Tempest Press avant que le
deployer ne publie les preuves. Cible : `http://172.28.20.2:80`.

## Reconnaissance

Le site expose dans son HTML un commentaire de staging :

```html
<!-- staging: git.tempest-press.kt:3000 -- ne pas exposer en prod -->
```

`robots.txt` révèle `/gitea/`, `/press/draft/` et surtout `/backup/`, servi en
autoindex. Le Gitea interne est proxifié sous `/gitea/` (`Tempest Internal`).

## Récupération des accès

`/backup/` contient `gitea-dump-f4acfd7b.zip`, un dump complet :

- `app.ini` (SECRET_KEY, INTERNAL_TOKEN, JWT_SECRET) ;
- `gitea-db.sq3` (utilisateurs, dépôts, webhooks) ;
- `data/deploy-token` (token API de `k.valenko`) ;
- `data/home/k.valenko/.ssh/id_ed25519` (clé privée SSH de l'admin).

Le token permet de lister les dépôts privés et de cloner :

- `press-release` : documents à publier + `publish.sh` + `config.yml` ;
- `infra-tools` : `deployer.py`, `crontab`, documentation du lockdown.

## Compréhension du pipeline

`press-release/README.md` et `config.yml` indiquent :

- un webhook Gitea déclenche `publish.sh` à chaque push sur `main` ;
- un cron de secours existe dans le service deployer ;
- en cas d'urgence, un fichier `.lockdown` **valide** dans `/var/www/publish`
  bloque le déploiement.

`config.yml` précise les deux formats acceptés :

- `sha256-derived` : hash dérivé des credentials opérateur ;
- `ssh-signature` : signature SSH de `LOCKDOWN` par la clé `k.valenko`,
  namespace `lockdown`.

`deployer.py` contient le détail décisif : lorsque le lockdown est valide, il ne
publie pas les documents mais écrit dans `/var/www/publish/blocked.log` :

```text
Lockdown verified. Operator credential: <FLAG>
```

nginx sert `/var/www/publish` sous `/press/`, dotfiles inclus. Le flag est donc
lisible directement, sans exécution de code supplémentaire.

## Exploitation

1. Cloner `press-release` avec le deploy token.
2. Pousser sur `main` un `publish.sh` qui dépose un `.lockdown` valide :

```bash
mkdir -p "$PUBLISH_DIR/documents"
printf 'LOCKDOWN' > "$PUBLISH_DIR/.lockdown"
# .lockdown.sig = signature SSH de "LOCKDOWN" par k.valenko (namespace lockdown)
```

3. Le webhook (ou le cron de secours) exécute le deployer.
4. Le deployer vérifie la signature, bloque la publication et écrit
   `blocked.log` avec le flag de l'instance.
5. Lire le résultat :

```bash
curl -s http://172.28.20.2/press/blocked.log
```

Réponse observée (flag redacté) :

```text
Publication blocked at 2026-11-17T06:30:23.823269+00:00
Lockdown verified. Operator credential: <redacted-flag>
```

Le flag a été reporté à la plateforme sous **Toguro Tempest** et n'est pas recopié ici.

## Pièges

- `GET /press/blocked.log` seulement : `/blocked.log` et `/documents/flag.txt`
  à la racine renvoient 404, le site est monté sous `/press/`.
- Écrire le `.lockdown` par PUT ou SSH ne sert à rien : nginx est statique et le
  port 22 est fermé. Le flag sort par `blocked.log`.
- Les credentials, la clé SSH et le FLAG sont régénérés à chaque cycle
  d'instance. Le flag d'un write-up précédent (`172.28.14.2`) n'est pas valide
  pour l'instance courante ; toujours repartir du dump `/backup/` courant.

## Validation

1. `curl -s http://172.28.20.2/press/blocked.log` doit renvoyer un fichier
   `Last-Modified` postérieur au push et contenir `Lockdown verified`.
2. Vérifier que `/press/` renvoie la page « En attente » et que les documents ne
   sont pas publiés.
3. Le flag live est la valeur `Operator credential` de ce log.
