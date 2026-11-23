# 1.6 — DNS : résolution, cache et analyse

> Fiche du chapitre 1.6 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Décrire une résolution récursive** du client jusqu'à la zone autoritative.
2. **Lire une réponse `dig`** : type, TTL, section réponse, autorité, additionnelle.
3. **Interpréter un TTL** et expliquer pourquoi une modification de zone met des heures à se voir.
4. **Analyser une requête DNS dans Wireshark** : nom, type, réponse, temps de réponse.
5. **Diagnostiquer** : mauvais résolveur, cache négatif, TCP fallback, échec DNSSEC.

## 1. Qui interroge qui

```text
application  →  résolveur stub (/etc/resolv.conf)  →  résolveur récursif  →  racine
                                                                    ↓
                                                              TLD (.com)
                                                                    ↓
                                                        zone autoritative (example.com)
```

- **Stub** : dans le système, il ne sait rien, il relaie au résolveur configuré.
- **Récursif** : fait le travail, met en cache, répond au client (souvent le routeur ou le FAI).
- **Autoritatif** : détient la zone, répond avec les vraies valeurs.

C'est le récursif qui est mis en cache, pas le client. D'où un comportement qui semble incohérent
d'une machine à l'autre.

## 2. Les types utiles

| Type | Contenu | Usage |
| --- | --- | --- |
| `A` | IPv4 | résolution classique |
| `AAAA` | IPv6 | idem en v6 |
| `CNAME` | alias | un nom pointe vers un autre nom |
| `MX` | serveur mail + priorité | routage du courrier |
| `NS` | serveurs de la zone | délégation |
| `TXT` | texte libre | SPF, DKIM, vérifications |
| `SOA` | autorité de la zone | numéro de série, timers |
| `PTR` | résolution inverse | `dig -x 8.8.8.8` |
| `SRV` | service + port | Active Directory, SIP |
| `CAA` | autorités de certification autorisées | TLS |

## 3. Lire une réponse

```bash
dig +noall +answer example.com A
dig +noall +answer gmail.com MX
```

```text
example.com.            30      IN      A       104.20.23.154
example.com.            30      IN      A       172.66.147.243

gmail.com.              30      IN      MX      30 alt3.gmail-smtp-in.l.google.com.
gmail.com.              30      IN      MX      10 alt1.gmail-smtp-in.l.google.com.
gmail.com.              30      IN      MX      5 gmail-smtp-in.l.google.com.
```

Colonnes : nom, **TTL**, classe, type, valeur. Les deux `A` signifient deux adresses, pas une
erreur : le client en essaie une, puis l'autre. Les priorités MX se lisent du plus petit au plus
grand.

Le TTL de 30 s est celui du cache du récursif interrogé, pas celui de la zone : il décroît à chaque
seconde passée en cache.

## 4. Suivre la délégation

```bash
dig +trace example.com A
```

```text
;; Received 729 bytes from 10.3.0.10#53(10.3.0.10) in 0 ms
com.                    172800  IN      NS      a.gtld-servers.net.
com.                    172800  IN      NS      b.gtld-servers.net.
```

`+trace` interroge la racine, puis le TLD, puis la zone, sans passer par le cache. C'est l'outil
qui distingue « la zone est fausse » de « mon cache est faux ».

## 5. Capture d'une résolution

```bash
sudo tcpdump -i eth0 -w dns.pcap 'udp port 53'
dig +short example.com
```

```bash
tshark -r dns.pcap -T fields -e frame.number -e ip.src -e ip.dst \
       -e dns.flags.response -e dns.qry.name -e dns.a
```

```text
1       10.2.21.53      10.3.0.10       False   example.com
2       10.3.0.10       10.2.21.53      True    example.com     172.66.147.243,104.20.23.154
```

Deux paquets : une question, une réponse. Le champ `dns.flags.response` à `False` puis `True`
identifie le sens sans ambiguïté. Sur un réseau chargé, c'est le filtre à poser en premier :

```text
dns && dns.flags.response == 0 && dns.qry.name contains "exemple"
```

Un exemple de laboratoire (capture générée, zone `exemple.lab`) donne le même squelette avec un
seul enregistrement :

```bash
tshark -r dns-lab.pcap -T fields -e frame.number -e dns.flags.response -e dns.qry.name -e dns.a -e dns.time
```

```text
1       False   exemple.lab
2       True    exemple.lab     192.168.1.50    0.000232000
```

`dns.time` mesure le délai entre question et réponse : c'est la métrique à surveiller quand
« Internet est lent mais le débit est bon ».

## 6. Ce qui se passe quand ça casse

| Symptôme | Cause probable | Vérification |
| --- | --- | --- |
| `NXDOMAIN` | nom inexistant, ou faute de frappe | `dig +trace` |
| `SERVFAIL` | DNSSEC invalide, ou zone cassée | `dig +dnssec` |
| Réponse `TC` (tronquée) | réponse > 512 octets, TCP requis | `dig +tcp` |
| Lenteur de 5 s puis succès | premier résolveur injoignable, bascule sur le second | `dig +time=1` |
| Réponse différente selon la machine | caches différents, ou résolveurs différents | `dig @8.8.8.8` vs `dig @résolveur local` |
| `dig` marche, `curl` non | `ndots` et domaine de recherche : le nom essayé n'est pas celui attendu | `dig` sur le FQDN complet |

Le cas `ndots` mérite un mot : avec `options ndots:5` (fréquent en Kubernetes), un nom court est
d'abord essayé suffixé par chaque domaine de recherche. Cinq échecs, puis le nom réel. D'où des
résolutions qui prennent des secondes.

## 7. DNS chiffré

| Transport | Port | Visibilité en capture |
| --- | --- | --- |
| UDP classique | 53 | noms en clair |
| TCP classique | 53 | noms en clair |
| DoT (DNS over TLS) | 853 | seulement le SNI et l'IP |
| DoH (DNS over HTTPS) | 443 | indistinguable du web |

Dès que DoT ou DoH est utilisé, la capture ne montre plus les noms : il faut passer par les journaux
du résolveur, ou par l'endpoint lui-même. C'est un changement majeur pour l'analyse forensic, et
pour la détection d'exfiltration par DNS.

## 8. Filtres

| Objectif | Filtre d'affichage |
| --- | --- |
| Tout le DNS | `dns` |
| Requêtes | `dns.flags.response == 0` |
| Réponses | `dns.flags.response == 1` |
| Un nom | `dns.qry.name contains "exemple"` |
| Un type | `dns.qry.type == 16` (TXT), `28` (AAAA), `15` (MX) |
| Erreurs | `dns.flags.rcode != 0` |
| Réponses lentes | `dns.time > 0.5` |

En capture : `tcpdump 'udp port 53'`, `tcpdump 'port 53'` pour inclure le TCP.

## 9. Pièges

| Symptôme | Cause |
| --- | --- |
| TTL qui n'est jamais celui de la zone | on lit le cache du récursif |
| « Ça marche chez moi » | caches différents, propagation en cours |
| Nom résolu vers `127.0.0.1` | blocage local (fichier `hosts`, DNS menteur, captive portal) |
| `.local` ne répond pas | mDNS (port 5353), pas le DNS classique |
| Beaucoup de TXT longs | DKIM/SPF légitimes, ou tunneling DNS : regarder la taille et la fréquence |
| `SERVFAIL` uniquement avec `+dnssec` | chaîne de confiance cassée, pas la zone |

## À retenir

- Stub, récursif, autoritatif : trois rôles, trois niveaux de cache.
- Le TTL lu est celui du cache ; `+trace` montre la zone réelle.
- `TC` signifie « passe en TCP » ; `SERVFAIL` n'est pas « nom inexistant ».
- Une résolution lente se mesure avec `dns.time`, pas à l'impression.
- DoH/DoT suppriment les noms de la capture : c'est un choix de conception, pas un bug.

## Pour aller plus loin

- [1.7 DHCP](07-dhcp.md) — comment l'adresse du résolveur arrive sur la machine.
- Guide [Wireshark](../../README.md) : chapitres 4.5 (DNS), 9.3 (analyse DNS), 10.5 (problème DNS).
- RFC 1035 (DNS), RFC 6891 (EDNS0), RFC 7858 (DoT), RFC 8484 (DoH).
