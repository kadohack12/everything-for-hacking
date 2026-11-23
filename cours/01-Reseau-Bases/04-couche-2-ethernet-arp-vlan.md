# 1.4 — Couche 2 : Ethernet, ARP et VLAN

> Fiche du chapitre 1.4 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Lire une trame Ethernet** : MAC source, MAC destination, EtherType, charge utile, FCS.
2. **Expliquer ARP** et reconnaître une réponse ARP non sollicitée.
3. **Détecter un ARP spoofing** dans une capture, sans outil magique.
4. **Lire un tag VLAN 802.1Q** et comprendre access/trunk.
5. **Choisir le bon point de capture** : ce qu'on ne voit pas depuis un port d'accès.

## 1. La trame Ethernet

| Champ | Taille | Rôle |
| --- | --- | --- |
| Préambule + SFD | 8 octets | synchronisation (jamais livré à Wireshark) |
| MAC destination | 6 octets | qui doit recevoir |
| MAC source | 6 octets | qui émet |
| EtherType / longueur | 2 octets | `0x0800` IPv4, `0x86dd` IPv6, `0x0806` ARP, `0x8100` VLAN |
| Charge utile | 46 à 1500 octets | le paquet de la couche 3 |
| FCS | 4 octets | CRC, souvent retiré par la carte réseau |

Trois EtherType suffisent à couvrir la majorité des captures : `0x0800` (IPv4), `0x86dd` (IPv6),
`0x0806` (ARP). Le champ `0x8100` annonce un tag VLAN, traité plus bas.

**MTU** : 1500 octets de charge utile en standard. Au-delà, il faut de la fragmentation IP ou du
jumbo frame (9000), qui exige que **tous** les équipements du chemin le supportent.

## 2. Adresses MAC

```text
aa:00:00:00:00:01
│  │  └──────┴── partie NIC (constructeur)
│  └───────────── partie OUI
└──────────────── bit I/G : 0 = unicast, 1 = multicast
```

| Adresse | Signification |
| --- | --- |
| `ff:ff:ff:ff:ff:ff` | diffusion, tout le segment |
| `01:00:5e:…` | multicast IPv4 |
| `33:33:…` | multicast IPv6 |
| `01:80:c2:00:00:0e` | LLDP (non transmis par un switch standard) |

Le bit de poids faible du premier octet distingue unicast et multicast. C'est pour cela qu'une MAC
commençant par `01:` est toujours du multicast.

## 3. ARP : trouver une MAC à partir d'une IP

```text
Qui a 192.168.1.1 ? Dites-le à 192.168.1.10      (requête, diffusion)
192.168.1.1 est à aa:00:00:00:00:fe              (réponse, unicast)
```

Capture de laboratoire (trois trames générées pour l'exercice) :

```bash
tshark -r arp.pcap -T fields -e frame.number -e arp.opcode -e arp.src.hw_mac \
       -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4
```

```text
1       1       aa:00:00:00:00:01       192.168.1.10    192.168.1.1
2       2       aa:00:00:00:00:fe       192.168.1.1     192.168.1.10
3       2       aa:00:00:00:00:99       192.168.1.1     192.168.1.10
```

Les trames 1 et 2 forment une résolution normale. **La trame 3 est l'anomalie** : une deuxième MAC
(`…:99`) annonce la même IP `192.168.1.1`, sans qu'aucune requête ne l'ait précédée. C'est la
signature d'un ARP spoofing, ou d'un doublon d'adresse.

Le cache ARP de la machine se lit directement :

```bash
ip neigh
```

```text
169.254.1.1 dev eth0 lladdr ee:ee:ee:ee:ee:ee REACHABLE
10.1.0.17 dev eth0 lladdr ee:ee:ee:ee:ee:ee STALE
```

`REACHABLE` signifie « entrée confirmée récemment ». `STALE` signifie « utilisable mais non
revérifiée » : ce n'est pas une erreur. Une entrée qui change de MAC toutes les quelques secondes
est, elle, un signal fort.

## 4. Switch, CAM et diffusion

Un switch apprend la MAC source de chaque trame et l'associe au port d'arrivée (table CAM). Une
trame dont la destination est inconnue est **inondée** sur tous les ports sauf celui d'origine.

Conséquences pour l'analyse :

- sur un **port d'accès**, on ne voit que son propre trafic, la diffusion et le multicast ;
- pour voir tout un segment, il faut un **miroir de port** (SPAN) ou un TAP ;
- en Wi-Fi, la capture dépend du mode de la carte et de la clé.

C'est la raison n°1 pour laquelle « Wireshark ne voit rien » : le point de capture est mauvais, pas
le filtre.

## 5. VLAN 802.1Q

Un tag de 4 octets s'insère entre la MAC source et l'EtherType :

| Champ | Bits | Rôle |
| --- | --- | --- |
| TPID | 16 | `0x8100` |
| PCP | 3 | priorité (QoS) |
| DEI | 1 | éligibilité au rejet |
| **VID** | 12 | identifiant de VLAN, 0 à 4095 (1 à 4094 utilisables) |

Décodage réel d'une trame taguée VLAN 42 :

```bash
tshark -r vlan-lab.pcap -V | grep -A3 "802.1Q Virtual LAN"
```

```text
802.1Q Virtual LAN, PRI: 0, DEI: 0, ID: 42
    000. .... .... .... = Priority: Best Effort (default) (0)
    ...0 .... .... .... = DEI: Ineligible
    .... 0000 0010 1010 = ID: 42
```

Sur un port **access**, le switch retire le tag avant de livrer la trame : une capture sur le poste
ne montre aucun VLAN. Sur un **trunk**, les trames circulent taguées : c'est là qu'on les voit.

Le VLAN segmente au niveau 2 : deux machines dans des VLAN différents ne se joignent pas en ARP,
même sur le même switch. Le routage entre VLAN exige un routeur ou un switch de niveau 3.

## 6. Filtres

| Objectif | Filtre d'affichage |
| --- | --- |
| Une MAC | `eth.addr == aa:00:00:00:00:01` |
| Diffusion | `eth.dst == ff:ff:ff:ff:ff:ff` |
| ARP seul | `arp` |
| Requêtes ARP | `arp.opcode == 1` |
| Réponses ARP | `arp.opcode == 2` |
| ARP gratuit | `arp.opcode == 2 && arp.src.proto_ipv4 == arp.dst.proto_ipv4` |
| Deux MAC pour une IP | `arp.opcode == 2 && arp.src.proto_ipv4 == 192.168.1.1` |
| VLAN précis | `vlan.id == 42` |

En capture : `tcpdump -i eth0 'arp'` ou `'vlan 42'`.

## 7. Pièges

| Symptôme | Cause |
| --- | --- |
| Aucune trame ARP visible | capture sur un port d'accès alors que le trafic est ailleurs |
| MAC `ee:ee:ee:ee:ee:ee` | interface virtuelle (veth, bridge) : la MAC est synthétique |
| Deux IP pour une MAC | NAT, proxy ARP, ou plusieurs adresses sur une interface : souvent normal |
| Une IP change de MAC sans raison | ARP spoofing ou adresse dupliquée |
| VLAN absent de la capture | port access (tag retiré) ou carte qui filtre les tags |
| Trames de 1514 octets « invalides » | offload : le FCS n'est pas recalculé avant la capture |

## À retenir

- EtherType dit ce qu'il y a dans la charge utile ; la MAC dit qui doit la recevoir.
- ARP est une résolution locale, en diffusion ; une réponse non sollicitée est suspecte.
- Un switch n'inonde que l'inconnu : le point de capture décide de ce qu'on peut voir.
- Le tag 802.1Q n'existe que sur les trunks ; en access, il a déjà été retiré.
- VLAN = segmentation L2, pas une sécurité à elle seule (VLAN hopping existe).

## Pour aller plus loin

- [1.5 TCP et UDP](05-tcp-udp.md) — la couche au-dessus.
- Guide [Wireshark](../../README.md) : chapitres 4.1 (Ethernet/ARP), 8 (lecture de trame), 9.1.
- RFC 826 (ARP), IEEE 802.1Q (VLAN), RFC 894 (encapsulation Ethernet).
