# 1.5 — TCP et UDP

> Fiche du chapitre 1.5 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Suivre une connexion TCP** : ouverture, transfert, fermeture, et lire les drapeaux.
2. **Interpréter un RST** correctement : port fermé, pas « pare-feu ».
3. **Reconnaître une retransmission** et distinguer lenteur réseau et perte réelle.
4. **Lire l'état d'une socket** avec `ss` et faire le lien avec la capture.
5. **Choisir TCP ou UDP** selon le besoin, et savoir ce que l'un ne garantit pas.

## 1. L'en-tête TCP

| Champ | Rôle en diagnostic |
| --- | --- |
| Ports source / destination | quel service, quel client |
| Numéro de séquence | position dans le flux d'octets |
| Numéro d'acquittement | prochain octet attendu |
| Drapeaux | `SYN`, `ACK`, `PSH`, `FIN`, `RST`, `URG` |
| Fenêtre | combien d'octets on peut encore recevoir |
| Options | `MSS`, `SACK`, `wscale`, timestamps |

Les options comptent : `MSS` fixe la taille maximale d'un segment, `wscale` multiplie la fenêtre
(16 bits seulement sans lui), les timestamps servent à mesurer le RTT.

## 2. Ouverture en trois temps

```bash
sudo tcpdump -i lo -w http.pcap 'tcp port 8080'
curl -s http://127.0.0.1:8080/ > /dev/null
sudo tcpdump -nn -r http.pcap
```

```text
IP 127.0.0.1.52488 > 127.0.0.1.8080: Flags [S], seq 1227792877, win 43690, options [mss 65495,sackOK,TS val 1788228249 ecr 0,nop,wscale 7], length 0
IP 127.0.0.1.8080 > 127.0.0.1.52488: Flags [S.], seq 3651000355, ack 1227792878, win 43690, options [mss 65495,sackOK,TS val 1788228249 ecr 1788228249,nop,wscale 7], length 0
IP 127.0.0.1.52488 > 127.0.0.1.8080: Flags [.], ack 1, win 342, options [nop,nop,TS val 1788228249 ecr 1788228249], length 0
IP 127.0.0.1.52488 > 127.0.0.1.8080: Flags [P.], seq 1:79, ack 1, win 342, options [nop,nop,TS val 1788228249 ecr 1788228249], length 78: HTTP: GET / HTTP/1.1
```

Trois paquets pour ouvrir, un quatrième qui porte déjà la requête. Le `[S.]` est un SYN **avec**
ACK : c'est le seul paquet de l'ouverture qui porte deux drapeaux.

La même chose en champs, pour un tri lisible :

```bash
tshark -r http.pcap -Y "tcp.flags.syn == 1 or tcp.flags.fin == 1" \
       -T fields -e frame.number -e tcp.srcport -e tcp.dstport \
       -e tcp.flags.syn -e tcp.flags.ack -e tcp.flags.fin
```

```text
1       52488   8080    True    False   False
2       8080    52488   True    True    False
10      52488   8080    False   True    True
11      8080    52488   False   True    True
```

Les trames 10 et 11 sont la fermeture : chacune envoie `FIN+ACK`, chacune répond `ACK`. Une
fermeture complète consomme quatre paquets quand les deux côtés ferment proprement.

## 3. Les drapeaux, en une table

| Drapeau | Sens | Ce qu'il raconte |
| --- | --- | --- |
| `SYN` | ouverture | demande de connexion, numéro de séquence initial |
| `SYN+ACK` | accord | le serveur accepte et choisit son propre ISN |
| `ACK` | acquittement | « j'ai reçu jusqu'à cet octet » |
| `PSH` | pousser | livrer à l'application sans attendre |
| `FIN` | fermeture propre | je n'ai plus rien à envoyer |
| `RST` | réinitialisation | **arrêt immédiat** : port fermé, connexion inconnue, ou rejet |

`RST` est le drapeau le plus mal interprété. Trois cas :

| Observation | Interprétation |
| --- | --- |
| `SYN` → `RST+ACK` immédiat | port fermé, l'hôte est joignable |
| `SYN` → rien du tout | filtrage (pare-feu) ou hôte absent |
| `RST` en cours de connexion | l'application a fermé brutalement, ou l'état a expiré |

C'est exactement la différence que fait `nmap` entre « closed » et « filtered ».

## 4. États de connexion vus du système

```bash
ss -tunap
```

```text
Netid State      Recv-Q Send-Q Local Address:Port   Peer Address:Port Process
tcp   LISTEN     0      2048         0.0.0.0:60000       0.0.0.0:*
tcp   TIME-WAIT  0      0         10.2.21.53:60000   10.2.98.130:35378
tcp   ESTAB      0      0         10.2.21.53:48430   34.44.63.36:443
```

| État | Signification |
| --- | --- |
| `LISTEN` | socket en écoute, aucune connexion |
| `ESTAB` | connexion établie, données possibles |
| `TIME-WAIT` | fermeture terminée, on garde l'état 2×MSL (souvent 60 s) |
| `CLOSE-WAIT` | le pair a fermé, l'application locale n'a pas encore fermé |
| `SYN-SENT` | SYN envoyé, pas de réponse : filtrage, hôte absent, ou lenteur |

Un `CLOSE-WAIT` qui s'accumule est un bug applicatif (descripteur non fermé), pas un problème
réseau. Un `TIME-WAIT` nombreux est normal sur un serveur web.

## 5. Retransmissions et lenteur

Une retransmission est un segment renvoyé parce que l'acquittement n'est pas arrivé à temps.

| Filtre Wireshark | Ce qu'il montre |
| --- | --- |
| `tcp.analysis.retransmission` | segment renvoyé à l'identique |
| `tcp.analysis.fast_retransmission` | renvoi déclenché par trois ACK dupliqués |
| `tcp.analysis.duplicate_ack` | le récepteur réclame le même octet |
| `tcp.analysis.zero_window` | le récepteur est saturé, l'émetteur attend |
| `tcp.analysis.window_full` | fenêtre pleine côté émetteur |
| `tcp.analysis.ack_rtt > 0.2` | RTT supérieur à 200 ms |

Un pourcentage de retransmission supérieur à 1 % mérite une explication. En dessous, c'est souvent
du bruit de congestion.

**Attention** : une capture faite sur la machine émettrice peut montrer des « retransmissions » qui
n'ont jamais quitté la carte réseau (offload, GRO). Le doute se lève en capturant des deux côtés,
ou sur un TAP.

## 6. UDP

UDP ne fait rien d'autre que transporter des datagrammes :

- pas d'ouverture, pas d'état, pas d'acquittement ;
- pas de retransmission : la perte est silencieuse ;
- en-tête de 8 octets seulement (ports, longueur, checksum).

| Usage | Pourquoi UDP |
| --- | --- |
| DNS | une question, une réponse, renvoi par le client |
| DHCP | diffusion avant d'avoir une adresse |
| VoIP, jeux | mieux vaut perdre une trame que d'attendre |
| QUIC (HTTP/3) | fiabilité gérée dans l'application |
| SNMP, syslog | datagrammes courts, tolérants à la perte |

Le checksum UDP est **facultatif en IPv4** (valeur 0 = non calculé), obligatoire en IPv6. Un
checksum nul dans une capture IPv4 n'est donc pas une anomalie.

## 7. Filtres

| Objectif | Filtre d'affichage |
| --- | --- |
| Un flux précis | `tcp.stream eq 0` |
| Un port | `tcp.port == 8080` |
| Ouvertures seulement | `tcp.flags.syn == 1 && tcp.flags.ack == 0` |
| Réinitialisations | `tcp.flags.reset == 1` |
| Fermetures | `tcp.flags.fin == 1` |
| UDP | `udp` |
| Un port UDP | `udp.port == 53` |

En capture : `tcpdump 'tcp port 8080'`, `tcpdump 'tcp[tcpflags] & tcp-syn != 0'`.

## 8. Pièges

| Symptôme | Cause |
| --- | --- |
| `RST` immédiat sur `SYN` | port fermé : l'hôte est vivant |
| Aucune réponse au `SYN` | filtrage : ne pas conclure « hôte mort » |
| Beaucoup de `TIME-WAIT` | normal, ou serveur qui ferme en premier |
| Retransmissions visibles d'un seul côté | point de capture ou offload, pas forcément une perte |
| Fenêtre à zéro pendant un transfert | récepteur lent (disque, application), pas le réseau |
| Connexion qui traîne puis échoue | MTU/PMTUD : voir les ICMP « fragmentation needed » |
| `SYN` renvoyés à intervalles réguliers | SYN non acquitté : filtrage ou perte sur le retour |

## À retenir

- Trois paquets pour ouvrir, quatre pour fermer proprement.
- `RST` = réponse active ; silence = filtrage. La distinction change le diagnostic.
- Une retransmission se mesure en pourcentage, pas au paquet près.
- UDP ne garantit rien : la fiabilité est déplacée dans l'application.
- `ss` et la capture doivent raconter la même histoire ; sinon, le point de capture est suspect.

## Pour aller plus loin

- [1.6 DNS](06-dns.md) — premier gros consommateur d'UDP.
- Guide [Wireshark](../../README.md) : chapitres 4.3 (TCP), 4.4 (UDP), 9.4 (analyse TCP), 10.4.
- RFC 9293 (TCP), RFC 768 (UDP), RFC 5681 (contrôle de congestion).
