# 1.2 — Adressage IPv4, masques et sous-réseaux

> Fiche du chapitre 1.2 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois être capable de :

1. **Lire un en-tête IPv4** et nommer chaque champ utile pour le diagnostic (TTL, protocole,
   longueur, drapeaux de fragmentation).
2. **Calculer un sous-réseau** de tête : adresse réseau, diffusion, plage utilisable, nombre
   d'hôtes — et vérifier le calcul avec `ipaddress` de Python.
3. **Découper un réseau en sous-réseaux de tailles différentes** (VLSM) sans chevauchement.
4. **Diagnostiquer une panne de masque** : deux machines qui se voient en ping sur le même switch
   mais dont l'une croit être sur un autre réseau.
5. **Choisir le bon filtre Wireshark** pour isoler un hôte, un réseau ou un paquet fragmenté.

## 1. L'en-tête IPv4

Un paquet IP commence par un en-tête de 20 octets minimum. Quatre champs servent tous les jours :

| Champ | Taille | À quoi il sert en pratique |
| --- | --- | --- |
| Version / IHL | 1 + 1 octet | 4 pour IPv4 ; IHL × 4 = taille de l'en-tête (options incluses) |
| Longueur totale | 2 octets | taille du paquet entier, en-tête compris, maximum 65 535 |
| Identification | 2 octets | regroupe les fragments d'un même datagramme |
| Drapeaux + offset | 3 bits + 13 bits | `MF` (more fragments), `DF` (don't fragment), position du fragment |
| **TTL** | 1 octet | décrémenté de 1 par chaque routeur ; à 0, le paquet est jeté (ICMP time exceeded) |
| **Protocole** | 1 octet | 6 = TCP, 17 = UDP, 1 = ICMP, 58 = ICMPv6 |
| **Somme de contrôle** | 2 octets | en-tête uniquement, recalculée par chaque routeur |
| Source / destination | 4 + 4 octets | les deux adresses |

Le TTL est le champ le plus utilisé en diagnostic : c'est lui qui rend `traceroute` possible, et
lui qui révèle parfois le système d'exploitation d'origine (64 pour Linux, 128 pour Windows),
**quand aucun NAT ni proxy n'a réécrit le paquet**.

## 2. Masque, réseau, diffusion

Une adresse IPv4 se découpe en deux parties : la partie réseau (imposée par le masque) et la
partie hôte.

| Notation | Masque | Hôtes utilisables |
| --- | --- | --- |
| `/8` | 255.0.0.0 | 16 777 214 |
| `/16` | 255.255.0.0 | 65 534 |
| `/24` | 255.255.255.0 | 254 |
| `/25` | 255.255.255.128 | 126 |
| `/26` | 255.255.255.192 | 62 |
| `/27` | 255.255.255.224 | 30 |
| `/30` | 255.255.255.252 | 2 |
| `/31` | 255.255.255.254 | 2 (RFC 3021, lien point à point) |
| `/32` | 255.255.255.255 | 1 (une seule adresse, pas de réseau) |

Deux adresses ne sont jamais attribuables dans un réseau classique : la **première** (adresse de
réseau) et la **dernière** (adresse de diffusion). D'où `2^n − 2`.

## 3. Calculer, puis vérifier

Le calcul mental reste indispensable en intervention, mais rien ne remplace une vérification. Voici
les trois opérations courantes, exécutées avec `ipaddress` :

```python
import ipaddress as ip

n = ip.ip_network("10.20.30.40/27", strict=False)
print("reseau  :", n)
print("masque  :", n.netmask, "/", n.prefixlen)
print("wildcard:", n.hostmask)
print("diffus. :", n.broadcast_address)
print("hotes   :", n.num_addresses - 2, "utilisables")
```

```text
reseau  : 10.20.30.32/27
masque  : 255.255.255.224 / 27
wildcard: 0.0.0.31
diffus. : 10.20.30.63
hotes   : 30 utilisables
```

`strict=False` est important : sans lui, `10.20.30.40/27` est refusé, parce que `.40` n'est pas
l'adresse de réseau. C'est justement l'erreur qu'on veut pouvoir calculer, pas celle qu'on veut
voir lever.

## 4. Lab : découper 192.168.1.0/24 en 4

```python
import ipaddress as ip

for n in ip.ip_network("192.168.1.0/24").subnets(new_prefix=26):
    print(f"{str(n):<18} masque {str(n.netmask):<16} hotes {n.num_addresses-2:>3}  "
          f"{n[1]} -> {n[-2]}")
```

```text
192.168.1.0/26     masque 255.255.255.192  hotes  62  192.168.1.1 -> 192.168.1.62
192.168.1.64/26    masque 255.255.255.192  hotes  62  192.168.1.65 -> 192.168.1.126
192.168.1.128/26   masque 255.255.255.192  hotes  62  192.168.1.129 -> 192.168.1.190
192.168.1.192/26   masque 255.255.255.192  hotes  62  192.168.1.193 -> 192.168.1.254
```

Chaque sous-réseau perd deux adresses : la sienne et sa diffusion. `192.168.1.63` n'appartient à
aucun des quatre : c'est la diffusion du premier.

## 5. VLSM : des sous-réseaux de tailles différentes

Un `/24` découpé en `/26` uniformes gaspille des adresses quand les besoins diffèrent. Le VLSM
alloue du plus grand au plus petit :

```python
import ipaddress as ip

cursor = ip.ip_network("172.16.0.0/24")
for nom, hotes in [("LAN-1", 100), ("LAN-2", 50), ("LAN-3", 20), ("WAN", 2)]:
    prefixe = 32 - (hotes + 2 - 1).bit_length()
    sous = next(cursor.subnets(new_prefix=prefixe))
    print(f"{nom:<7} {hotes:>3} hotes -> {str(sous):<18} /{sous.prefixlen} "
          f"({sous.num_addresses-2} dispo)")
    cursor = ip.ip_network((int(sous.network_address) + sous.num_addresses, sous.prefixlen))
```

```text
LAN-1   100 hotes -> 172.16.0.0/25      /25 (126 dispo)
LAN-2    50 hotes -> 172.16.0.128/26    /26 (62 dispo)
LAN-3    20 hotes -> 172.16.0.192/27    /27 (30 dispo)
WAN       2 hotes -> 172.16.0.224/30    /30 (2 dispo)
```

La règle : `2^n − 2 ≥ besoin`, et on arrondit à la puissance de deux supérieure. Un LAN de 100
hôtes exige 128 adresses, donc un `/25`, pas un `/26` (62 hôtes, insuffisant).

## 6. Plages à connaître

| Plage | Usage | Remarque |
| --- | --- | --- |
| `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | privées (RFC 1918) | jamais routées sur Internet |
| `127.0.0.0/8` | boucle locale | tout le /8 est local |
| `169.254.0.0/16` | link-local (APIPA) | symptôme classique : pas de DHCP |
| `100.64.0.0/10` | CGNAT (RFC 6598) | opérateurs, à ne pas confondre avec du privé |
| `224.0.0.0/4` | multicast | `224.0.0.251` = mDNS |
| `0.0.0.0/8`, `240.0.0.0/4` | réservées | `0.0.0.0` = « cette machine » en source DHCP |

Une machine en `169.254.x.x` n'a pas obtenu de bail DHCP. C'est la première chose à vérifier quand
un poste « n'a pas Internet » mais que le câble est branché.

## 7. Vérifier sur la machine

```bash
ip -br addr
ip route
ip route get 8.8.8.8
```

```text
lo               UNKNOWN        127.0.0.1/8
eth0@if58        UP             10.2.21.53/32

default via 169.254.1.1 dev eth0
169.254.1.1 dev eth0 scope link

8.8.8.8 via 169.254.1.1 dev eth0 src 10.2.21.53 uid 10001
    cache
```

`ip route get` est la commande la plus utile du lot : elle répond à « par où partirait ce paquet,
et avec quelle adresse source ». En cas de double interface ou de VPN, c'est elle qui tranche.

## 8. Filtres Wireshark utiles

| Objectif | Filtre d'affichage |
| --- | --- |
| Un hôte, dans les deux sens | `ip.addr == 10.0.0.5` |
| Un réseau entier | `ip.addr == 10.0.0.0/24` |
| TTL faible (proche du but) | `ip.ttl < 5` |
| Paquets fragmentés | `ip.flags.mf == 1 \|\| ip.frag_offset > 0` |
| Ne pas fragmenter | `ip.flags.df == 1` |
| Protocole | `ip.proto == 6` (TCP), `17` (UDP), `1` (ICMP) |
| En-tête avec options | `ip.hdr_len > 20` |

## 9. Pièges

| Symptôme | Cause probable |
| --- | --- |
| Deux machines du même switch ne se parlent pas | masques différents : l'une croit l'autre hors réseau et envoie à sa passerelle |
| Un hôte répond mais pas ses voisins | mauvaise adresse de diffusion dans un service (ex. `255.255.255.0` codé en dur) |
| `ping` OK, `ssh` KO | filtre sur un port, pas un problème d'adressage |
| Paquets tronqués à 1500 octets | MTU et `DF` : fragmentation nécessaire, ICMP « fragmentation needed » filtré |
| Checksum IP invalide dans Wireshark | déchargement sur la carte réseau (checksum offload) : la capture voit le paquet avant calcul |
| TTL « incohérent » | NAT, proxy ou tunnel réécrivent le TTL : ce n'est pas une preuve de distance |

## À retenir

- Le masque décide de ce qui est local ; la passerelle sert à tout le reste.
- `2^n − 2` : réseau et diffusion ne s'attribuent pas (sauf `/31` et `/32`).
- VLSM : on alloue du plus grand au plus petit, jamais l'inverse.
- `ip route get <ip>` répond à « par où ça part, avec quelle source ».
- Un checksum faux dans Wireshark est souvent un artefact d'offload, pas une attaque.

## Pour aller plus loin

- [1.3 IPv6](03-ipv6.md) — même logique d'adressage, règles différentes.
- Guide [Wireshark](../../README.md) (dépôt `guide-wireshark`) : chapitre 3.3, sous-réseaux et NAT.
- RFC 791 (IPv4), RFC 1918 (adresses privées), RFC 3021 (`/31`), RFC 6598 (CGNAT).
