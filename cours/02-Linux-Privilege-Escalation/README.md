# 02 — Linux Privilege Escalation

[← Programme](../README.md)

## Objectifs

Partir d'un shell utilisateur non privilégié et obtenir `root` en identifiant méthodiquement
les mauvaises configurations. Savoir **quoi** énumérer, dans quel ordre, et pourquoi.

## Prérequis

- Module [01 — Réseau](../01-Reseau-Bases/README.md)
- Ligne de commande Linux confortable (fichiers, permissions, processus, systemd)

## Plan

| # | Chapitre | Contenu clé | Lab |
| --- | --- | --- | --- |
| 2.1 | Méthodologie | boucle énumération → hypothèse → test | checklist d'énumération |
| 2.2 | Identité & permissions | uid/gid, `sudo -l`, fichiers world-writable | trouver un script modifiable |
| 2.3 | SUID / SGID | recherche, GTFOBins | `find / -perm -4000` |
| 2.4 | Capabilities | `getcap`, caps dangereuses | `cap_setuid+ep` sur un binaire |
| 2.5 | Tâches planifiées | cron, timers systemd, PATH détourné | cron job root sur script utilisateur |
| 2.6 | Services & sockets | unités systemd, sockets UNIX, droits | service root mal configuré |
| 2.7 | Secrets en clair | historique, clés SSH, configs, `.env` | grep ciblé |
| 2.8 | Noyau & binaires | versions vulnérables, exploits publics | CVE de kernel en lab |
| 2.9 | Conteneurs & namespaces | Docker socket, montages, `--privileged` | évasion d'un conteneur de test |
| 2.10 | Persistance & traces | comment rester discret, nettoyer | journalctl / audit |

## Labs

- **Lab A** — VM volontairement mal configurée (SUID + cron + sudo) : root en 3 étapes.
- **Lab B** — conteneur `--privileged` : sortie vers l'hôte.
- **Lab C** — énumération à l'aveugle : `linPEAS` puis validation manuelle de chaque piste.

## Outils

`linPEAS` · `pspy` · `GTFOBins` · `LinEnum` · `linux-exploit-suggester` · `getcap` · `sudo -l`

## Notes

> Une fiche par vecteur : condition, détection, exploitation, remédiation.
> Toujours documenter la **remédiation** — c'est la moitié du métier.
