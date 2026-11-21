---
title: "Forensic Recovery · Git + GPG"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/forensics/forensic-recovery.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# Forensic Recovery : Forensics · Git dangling commits + GPG

**Catégorie** : forensics  
**Flag** : `HLB2026{95420c91e0a7929e42b14d05a5ed9f78}`

## TL;DR

Une archive de poste opérateur contient un dépôt git avec des commits pendants. L'un d'eux expose un `.env` avec une passphrase GPG. L'autre commit pendant contient `op-briefing.gpg`, déchiffrable avec cette passphrase.

## Analyse de l'archive

L'archive `operator-ws.tar.gz` contient un homedir avec un dépôt git. La clé SSH présente un commentaire révélateur : `nrv-ops-42@borealis-ws`. Ce n'est pas un poste Vantage Hosting Mirova : c'est une machine Borealis Analytics, Norveth.

## Commits pendants

```bash
git fsck --lost-found
```

Deux commits dangling apparaissent :

- `16a1bec9` : suppression d'un fichier `.env` contenant `GPG_PASSPHRASE=Borealis-Kaltyr-2026!` et un faux flag orienté Valdoria (leurre narratif).
- `040693ab` : ajout de `op-briefing.gpg`.

```bash
git show 040693ab:op-briefing.gpg > op-briefing.gpg
gpg --batch --passphrase 'Borealis-Kaltyr-2026!' -d op-briefing.gpg
```

Le document déchiffré contient un `AUTH_TOKEN` et le flag :

```
HLB2026{95420c91e0a7929e42b14d05a5ed9f78}
```

## Lecture narrative

Le commentaire SSH `nrv-ops-42@borealis-ws` et la passphrase `Borealis-Kaltyr-2026!` confirment le lien Norveth/Kaltyr. Le faux flag Valdoria dans le `.env` supprimé est un leurre intentionnel dans la narration du challenge.

## À retenir

`git fsck --lost-found` récupère tous les objets non référencés d'un dépôt, y compris les commits dont la branche a été supprimée. Un `.env` supprimé dans un commit reste accessible dans l'historique git tant que le dépôt n'a pas été `gc`'d.
