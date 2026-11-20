# 1.1 — Modèle OSI, TCP/IP et encapsulation

> Fiche du chapitre 1.1 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois être capable de :

1. **Situer un protocole sur une couche** — pour choisir le bon outil et le bon filtre, au lieu de
   taper au hasard.
2. **Suivre l'encapsulation** d'une requête HTTP jusqu'à la trame, et expliquer où chaque
   information est ajoutée (émission) puis retirée (réception).
3. **Lire une capture en dix secondes** : quelle couche, quel protocole, quel indice exploitable.
4. **Relier une couche à ses attaques** : ARP spoof (L2), IP spoof (L3), SYN scan (L4),
   DNS tunneling (L7).
5. **Justifier un résultat de scan** : pourquoi un port répond alors que `curl` échoue, pourquoi
   un `ping` muet ne signifie pas « hôte mort », pourquoi `nmap -sS` et `nmap -sT` ne donnent pas
   la même chose.

En CTF, ça se traduit concrètement par : comprendre un `tcpdump` sans documentation, reconnaître
un service à son port et à son PDU, et ne pas perdre vingt minutes sur un service qui n'écoute
pas là où on croit.

## 1. Pourquoi un modèle en couches ?

Un réseau réel est un empilement de responsabilités indépendantes : le câble ne sait pas ce qu'est
une requête HTTP, et le navigateur ne sait pas s'il passe par du Wi-Fi ou de la fibre.

- **Chaque couche rend un service à celle du dessus** et ignore comment celle du dessous est
  implémentée.
- **Chaque couche ajoute son en-tête** : c'est l'encapsulation.
- **Chaque couche est une surface d'attaque distincte** — c'est ce qui nous intéresse ici.

| Couche | Question à laquelle elle répond | Ce qu'on y attaque |
| --- | --- | --- |
| Application | « Que veut le client ? » | injection, SSRF, auth, DNS spoofing |
| Transport | « Quel programme, et de façon fiable ? » | scan de ports, SYN flood, détournement de flux |
| Réseau | « Quelle machine distante ? » | IP spoofing, ICMP tunneling, fragmentation |
| Liaison | « Quelle machine sur ce segment ? » | ARP spoofing, VLAN hopping, DHCP rogue |

## 2. OSI vs TCP/IP

Le modèle **OSI** (7 couches) est une grille de lecture ; le modèle **TCP/IP** (4 couches) est ce
qui tourne réellement. Les deux se superposent :

| # | OSI | TCP/IP | PDU | Adressage | Exemples | Outils |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | Application | Application | données | nom / URL | HTTP, DNS, SMTP, SSH | `curl`, `dig`, `burp` |
| 6 | Présentation | Application | données | encodage, TLS | TLS, JSON, UTF-8 | `openssl s_client` |
| 5 | Session | Application | données | session | cookies, RPC | — |
| 4 | Transport | Transport | segment (TCP) / datagramme (UDP) | **port** | TCP, UDP | `nmap`, `nc`, `hping3` |
| 3 | Réseau | Internet | paquet | **adresse IP** | IP, ICMP, ARP* | `nmap -sn`, `traceroute` |
| 2 | Liaison | Accès réseau | trame | **adresse MAC** | Ethernet, ARP, Wi-Fi | `arping`, `bettercap` |
| 1 | Physique | Accès réseau | bits | — | câble, ondes | — |

\* ARP est un cas d'école : il est porté par Ethernet (L2) mais sert à résoudre une adresse IP
(L3). On le range généralement en L2/L3.

Retenir pour le terrain : **L4 = ports**, **L3 = IP**, **L2 = MAC**. Quand un scan échoue, la
première question est toujours « à quelle couche je me place ? ».

## 3. Encapsulation

Analogie : des poupées russes. Chaque couche emballe le contenu de la précédente et colle son
étiquette devant.

```text
Application   HTTP   | "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
                     v
Transport     TCP    | [port 51234 -> 80][seq/ack][flags][données HTTP]      = segment
                     v
Réseau        IP     | [10.10.14.7 -> 93.184.216.34][TTL 64][proto 6][segment] = paquet
                     v
Liaison       Eth    | [MAC dst][MAC src][type 0x0800][paquet IP][FCS]        = trame
                     v
Physique             | 01001000 01010100 01010100 01010000 ...              = bits
```

À la réception, c'est l'inverse (**décapsulation**) : la carte réseau vérifie le FCS et jette les
trames qui ne lui sont pas destinées, IP vérifie la destination et décrémente le TTL, TCP
réordonne et acquitte, puis l'application lit le contenu.

Deux conséquences pratiques :

- **Chaque en-tête coûte de la place.** Un MTU Ethernet de 1500 octets laisse ~1460 octets utiles
  en TCP/IPv4. Au-delà, IP fragmente — source de bugs et de contournements de filtres.
- **Ce que voit un IDS dépend de la couche où il inspecte.** Un filtrage L3/L4 ne voit pas une
  attaque dans le corps HTTP.

[TODO: exemple concret / capture Wireshark — `curl http://example.com`, puis clic droit sur le
paquet HTTP → Follow → TCP Stream, et capture de la pile d'encapsulation dans le panneau
« Packet Details »]

## 4. Les protocoles clés

### ARP — trouver la MAC d'une IP (L2/L3)

- **Rôle** : « qui a 192.168.1.1 ? » diffusé en broadcast, réponse avec la MAC.
- **À retenir** : pas d'authentification, la réponse est crue. Un cache ARP peut être empoisonné.
- **En CTF** : un ARP spoof en lab permet le man-in-the-middle sur un réseau commuté.
- **À regarder** : `arp -a`, trames `ARP` en broadcast, doublons de MAC.

[TODO: exemple concret / capture Wireshark — `arp -a` avant/après un `bettercap` ARP spoof en
lab isolé]

### IP — acheminer un paquet (L3)

- **Rôle** : adresse source/destination, TTL, protocole encapsulé, fragmentation.
- **À retenir** : **TTL** indique le nombre de routeurs traversés (64 au départ sur Linux/macOS,
  128 sur Windows, 255 sur du matériel réseau) — utile pour deviner l'OS distant.
- **En CTF** : `traceroute` exploite le TTL ; l'IP spoofing est possible mais la réponse part
  ailleurs.

### ICMP — signaler, pas transporter (L3)

- **Rôle** : `echo request/reply` (ping), `time exceeded` (traceroute), `destination unreachable`.
- **À retenir** : **pas de port**. Un hôte qui ne répond pas au ping peut très bien avoir 22 et 80
  ouverts (ICMP filtré).
- **En CTF** : ICMP tunneling, exfiltration lente, découverte d'hôtes via `nmap -sn`.

[TODO: capture Wireshark — un `ping` (echo request/reply) et un `traceroute` (TTL croissant +
time exceeded)]

### TCP — flux fiable, orienté connexion (L4)

- **Rôle** : ports, numéros de séquence, acquittements, fenêtre, retransmission.
- **Handshake en trois temps** : `SYN` → `SYN/ACK` → `ACK`. Fermeture : `FIN`/`ACK` des deux
  côtés, ou `RST` pour couper net.
- **À retenir** : un `SYN` sans réponse = port filtré ; un `SYN/ACK` = port ouvert ; un `RST` =
  port fermé. C'est exactement ce que fait un scan `-sS`.
- **En CTF** : scan furtif, SYN flood, détection de services par bannière.

[TODO: capture Wireshark — handshake complet, filtre `tcp.flags.syn == 1`, puis la même
conversation vue par `nmap -sS -p 80,443`]

### UDP — datagrammes sans état (L4)

- **Rôle** : pas de connexion, pas d'acquittement, pas d'ordre garanti.
- **À retenir** : plus dur à scanner (pas de réponse ≠ port fermé), souvent filtré, utilisé par
  DNS, DHCP, SNMP, NTP, QUIC.
- **En CTF** : amplification DNS/NTP, services « invisibles » aux scans TCP.

### DNS — la carte du réseau (L7)

- **Rôle** : résolution nom → IP, et l'inverse ; types `A`, `AAAA`, `MX`, `TXT`, `CNAME`, `NS`.
- **À retenir** : **UDP 53** pour les requêtes courantes, **TCP 53** pour les réponses volumineuses
  et les transferts de zone (`AXFR`).
- **En CTF** : énumération de sous-domaines, transfert de zone mal configuré, DNS tunneling pour
  l'exfiltration.

[TODO: exemple concret / capture Wireshark — `dig +trace example.com`, puis un `dig AXFR` sur une
zone de lab]

### HTTP — la couche applicative qu'on exploite le plus (L7)

- **Rôle** : méthode + chemin + en-têtes + corps ; codes `2xx` succès, `3xx` redirection, `4xx`
  erreur client, `5xx` erreur serveur.
- **À retenir** : HTTP est **en clair** (port 80 par défaut), HTTPS est HTTP dans TLS (443).
  Beaucoup de services web vivent ailleurs : 8080, 8443, 5000, 3000…
- **En CTF** : énumération de répertoires, manipulation de cookies/JWT, injection, SSRF, IDOR.

[TODO: capture Wireshark — `curl -v`, un `GET` puis un `POST` avec cookie de session, et la même
chose en HTTPS pour montrer que le contenu devient illisible]

## 5. Tableaux de synthèse

### Ports à connaître

| Port | Service | Transport | Intérêt en pentest |
| --- | --- | --- | --- |
| 21 | FTP | TCP | anonyme, écriture, `ftp` en clair |
| 22 | SSH | TCP | clés faibles, réutilisation de credentials |
| 23 | Telnet | TCP | tout en clair |
| 25 | SMTP | TCP | relais ouvert, énumération d'utilisateurs |
| 53 | DNS | UDP/TCP | AXFR, tunneling, sous-domaines |
| 80 | HTTP | TCP | la base : énumération web |
| 111 | rpcbind | TCP/UDP | cartographie NFS |
| 139/445 | SMB | TCP | partages, null session, EternalBlue |
| 161 | SNMP | UDP | communautés `public`, dump de configuration |
| 389/636 | LDAP(S) | TCP | énumération d'annuaire |
| 443 | HTTPS | TCP | web chiffré, vhosts |
| 1433 | MSSQL | TCP | `xp_cmdshell` |
| 2049 | NFS | TCP/UDP | partages exportés en `no_root_squash` |
| 3306 | MySQL | TCP | `root` sans mot de passe en lab |
| 3389 | RDP | TCP | BlueKeep, brute force |
| 5432 | PostgreSQL | TCP | `COPY ... FROM PROGRAM` |
| 5900 | VNC | TCP | souvent sans mot de passe |
| 5985/5986 | WinRM | TCP | exécution à distance |
| 6379 | Redis | TCP | écriture de fichier / cron |
| 8080 | HTTP alternatif | TCP | proxies, Tomcat, Jenkins |
| 27017 | MongoDB | TCP | base sans authentification |

### Outils par couche

| Couche | But | Outils |
| --- | --- | --- |
| L2 | voir/attaquer le segment local | `arping`, `arp-scan`, `bettercap`, `tcpdump -e` |
| L3 | découverte d'hôtes, chemin | `ping`, `traceroute`, `nmap -sn`, `hping3` |
| L4 | ports et services | `nmap -sS/-sU/-sV`, `nc`, `masscan` |
| L7 | protocoles applicatifs | `curl`, `dig`, `openssl s_client`, `ffuf`, `burp` |
| Toutes | capturer et filtrer | `tcpdump`, `tshark`, `Wireshark` |

## 6. Méthode de lecture d'une capture

1. **Filtrer** avant de lire : `ip.addr == <cible>`, `tcp.port == 80`, `dns`, `arp`.
2. **Remonter la pile** : la trame (L2) donne les MAC, le paquet (L3) les IP et le TTL, le
   segment (L4) les ports et les flags, le contenu (L7) le protocole.
3. **Chercher l'anomalie** : `RST` inattendu, port source inhabituel, TTL qui change, requête DNS
   vers un domaine bizarre, payload lisible là où on attend du chiffré.
4. **Suivre le flux** : `Follow → TCP Stream` reconstitue la conversation applicative.

## 7. Pièges classiques en CTF

- **« Le ping ne répond pas »** ≠ hôte éteint : ICMP est souvent filtré. Tester un port TCP.
- **`nmap -sS` vs `-sT`** : le SYN scan ne termine pas le handshake ; un `-sT` complet laisse des
  traces dans les logs applicatifs.
- **Port fermé vs filtré** : `RST` = fermé, silence = filtré (pare-feu qui jette).
- **DNS sur deux transports** : une requête volumineuse bascule sur TCP 53 — un scan UDP seul
  rate le service.
- **HTTP n'est pas toujours sur 80** : toujours confirmer avec `curl -I` et un scan complet.
- **TTL et NAT** : le TTL observé peut être modifié en chemin ; ne pas en faire une preuve.
- **Encapsulation ≠ chiffrement** : HTTPS protège le contenu L7, mais les IP, ports et tailles de
  paquets restent visibles.

## 8. Exercice pratique

Un collègue te transmet cet extrait de capture, prise sur un poste d'audit. Réponds sans
documentation.

```text
$ sudo tcpdump -nnvv -X -i eth0 -c 4 'host 93.184.216.34'
14:02:11.104512 IP (tos 0x0, ttl 64, id 54321, offset 0, flags [DF], proto TCP (6), length 60)
    10.10.14.7.51234 > 93.184.216.34.80: Flags [S], cksum 0x1a2b (correct),
    seq 3141592653:3141592653, win 64240, options [mss 1460,sackOK,TS val 1234567 ecr 0], length 0
14:02:11.238817 IP (tos 0x0, ttl 119, id 0, offset 0, flags [DF], proto TCP (6), length 60)
    93.184.216.34.80 > 10.10.14.7.51234: Flags [S.], cksum 0x9f8e (correct),
    seq 2718281828:2718281828, ack 3141592654, win 65160, options [mss 1460,sackOK], length 0
14:02:11.238880 IP (tos 0x0, ttl 64, id 54322, offset 0, flags [DF], proto TCP (6), length 52)
    10.10.14.7.51234 > 93.184.216.34.80: Flags [.], cksum 0x2c3d (correct), ack 1, win 502, length 0
14:02:11.239002 IP (tos 0x0, ttl 64, id 54323, offset 0, flags [DF], proto TCP (6), length 114)
    10.10.14.7.51234 > 93.184.216.34.80: Flags [P.], cksum 0x3c4d (correct), seq 1:75, ack 1, win 502, length 74
        0x0000:  4745 5420 2f20 4854 5450 2f31 2e31 0d0a  GET./.HTTP/1.1..
        0x0010:  486f 7374 3a20 6578 616d 706c 652e 636f  Host:.example.co
```

1. Quel protocole de transport, quel port de destination, quel service ?
2. Qui initie la connexion, et à quoi le voit-on ?
3. Combien de segments ouvre la connexion, et lesquels ?
4. Que peut-on déduire des TTL 64 et 119 ?
5. Quel filtre d'affichage Wireshark isole cette conversation ?
6. Le contenu applicatif est-il lisible ? Qu'est-ce que cela implique pour un auditeur ?

<details>
<summary>Correction</summary>

**1. Transport et service** — TCP, port destination **80**, donc HTTP (le payload le confirme).

**2. Initiateur** — le poste `10.10.14.7`, port source éphémère `51234`. On le voit au premier
paquet : `Flags [S]` (SYN) part du client vers le serveur.

**3. Ouverture** — trois segments (handshake en trois temps) :
`[S]` du client → `[S.]` (SYN/ACK) du serveur → `[.]` (ACK) du client.
Le quatrième paquet `[P.]` est déjà de la donnée (PSH/ACK).

**4. TTL** — `ttl 64` côté client : origine Linux/Unix (ou macOS). `ttl 119` côté serveur : la
valeur de départ était probablement 128 (Windows) et 9 routeurs ont été traversés
(128 − 119 = 9). C'est une **indication**, pas une preuve : NAT et proxys modifient le TTL.

**5. Filtre Wireshark** — `ip.addr == 93.184.216.34 && tcp.port == 80`, ou plus simplement
`tcp.stream eq 0` une fois le flux repéré. En ligne de commande : `tshark -r capture.pcap -Y
'tcp.port == 80'`.

**6. Lisibilité** — oui : le dump hexadécimal se lit directement en ASCII
(`GET / HTTP/1.1`, `Host: example.co…`). HTTP n'est pas chiffré : credentials, cookies et
jetons circulent en clair. C'est exactement ce qu'un auditeur cherche à démontrer sur un réseau
non chiffré — et pourquoi HTTPS (port 443) rend le même dump illisible.

</details>

## 9. Pour aller plus loin

- Guide [Wireshark](../../README.md) (dépôt `guide-wireshark`) : filtres et labs progressifs.
- RFC 791 (IP), RFC 792 (ICMP), RFC 793/9293 (TCP), RFC 768 (UDP), RFC 826 (ARP), RFC 1035 (DNS),
  RFC 9110 (HTTP).
- Chapitre suivant : [1.2 Adressage IPv4](README.md#plan).
