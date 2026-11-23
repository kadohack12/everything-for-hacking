# 1.7 — DHCP : obtenir une adresse

> Fiche du chapitre 1.7 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Décrire DORA** et reconnaître les quatre messages dans une capture.
2. **Lire les options** d'un bail : durée, routeur, DNS, domaine.
3. **Expliquer pourquoi un poste est en `169.254.x.x`** et comment le prouver.
4. **Reconnaître un serveur DHCP indésirable** sur un réseau de laboratoire.
5. **Distinguer DHCP et DHCPv6**, et savoir ce que SLAAC remplace.

## 1. DORA, quatre messages

| Message | De → vers | Contenu |
| --- | --- | --- |
| **D**iscover | client `0.0.0.0` → `255.255.255.255:67` | « y a-t-il un serveur ? », MAC du client |
| **O**ffer | serveur → `255.255.255.255:68` | proposition d'adresse + options |
| **R**equest | client → diffusion | « je prends celle-là », avec l'IP du serveur |
| **A**ck | serveur → client | confirmation, bail accordé |

Le client n'a pas d'adresse au départ : tout passe en diffusion, sauf si un relais DHCP est en
place (le relais met son adresse dans `giaddr` et le serveur répond en unicast au relais).

## 2. Capture du cycle complet

Capture de laboratoire (quatre trames générées pour l'exercice, serveur `192.168.1.1`, client
`aa:00:00:00:00:01`) :

```bash
tshark -r dhcp.pcap
```

```text
1   0.000000      0.0.0.0 → 255.255.255.255 DHCP 286 DHCP Discover - Transaction ID 0x12345678
2   0.000580  192.168.1.1 → 255.255.255.255 DHCP 310 DHCP Offer    - Transaction ID 0x12345678
3   0.000931      0.0.0.0 → 255.255.255.255 DHCP 298 DHCP Request  - Transaction ID 0x12345678
4   0.001195  192.168.1.1 → 255.255.255.255 DHCP 298 DHCP ACK      - Transaction ID 0x12345678
```

Le `Transaction ID` identifie le cycle : deux cycles entrelacés se distinguent par ce champ, pas
par l'ordre d'arrivée.

Les champs utiles en colonnes :

```bash
tshark -r dhcp.pcap -T fields -e frame.number -e dhcp.option.dhcp \
       -e dhcp.option.ip_address_lease_time -e dhcp.option.requested_ip_address -e dhcp.ip.your
```

```text
1       1                       0.0.0.0
2       2       86400           192.168.1.10
3       3               192.168.1.10    0.0.0.0
4       5       86400           192.168.1.10
```

Le type de message (`dhcp.option.dhcp`) vaut 1, 2, 3, 5 : Discover, Offer, Request, ACK. Le bail
est de 86 400 s, soit 24 h. `dhcp.ip.your` (`yiaddr`) est l'adresse proposée puis confirmée.

## 3. Les options qui comptent

| Option | Contenu | Effet si absente ou fausse |
| --- | --- | --- |
| 51 | durée du bail | bail très court : renouvellements permanents |
| 3 | routeur (passerelle) | pas de sortie du réseau local |
| 6 | serveur DNS | résolution impossible, ou DNS indésirable |
| 15 | nom de domaine | noms courts non résolus |
| 42 | serveurs NTP | horloge dérive : TLS et Kerberos échouent |
| 121 | routes classless | accès à des réseaux spécifiques |
| 82 | information de relais | traçabilité, attribution par port de switch |

Un bail DHCP n'est pas qu'une adresse : c'est **toute la configuration réseau** du poste. Un
serveur mal configuré peut donc casser la résolution DNS sans toucher au routage.

## 4. Renouvellement

| Étape | Quand | Message |
| --- | --- | --- |
| Renouvellement | 50 % du bail (T1) | Request en unicast au serveur |
| Relance | 87,5 % du bail (T2) | Request en diffusion à tout serveur |
| Expiration | 100 % | le client repart en Discover |

Avec un bail de 24 h : renouvellement à 12 h, relance à 21 h. Sur un bail de 10 minutes, un poste
en veille peut perdre son adresse et en obtenir une autre au réveil — ce qui explique des
connexions coupées « sans raison ».

## 5. Diagnostic d'un poste sans adresse

| Observation | Interprétation |
| --- | --- |
| Adresse `169.254.x.x` | aucun serveur n'a répondu : APIPA |
| Discover répétés sans réponse | serveur absent, ou diffusion bloquée (VLAN, Wi-Fi client isolation) |
| Offer reçue, pas de Request | client qui refuse l'offre (adresse déjà utilisée) |
| Request sans ACK | serveur saturé, ou pool épuisé |
| Deux Offers différents | deux serveurs DHCP sur le segment : à identifier d'urgence |

Le cas des deux serveurs est le plus grave : rien n'empêche un serveur non autorisé de répondre
plus vite. La parade est le **DHCP snooping** sur le switch, qui n'accepte les réponses que sur les
ports déclarés de confiance.

## 6. DHCPv6 et SLAAC

| Mécanisme | Ce qui est fourni | Où |
| --- | --- | --- |
| SLAAC | préfixe `/64` via RA, adresse dérivée | IPv6 seulement |
| DHCPv6 sans état | DNS, autres options | complète SLAAC |
| DHCPv6 avec état | adresse + options | serveur garde l'état |

En IPv6, la machine a **toujours** une adresse lien locale (`fe80::/10`), même sans serveur. Un
`ping6` vers la passerelle peut donc réussir alors qu'il n'y a aucune connectivité globale : le
diagnostic se fait sur l'adresse globale, pas sur le lien local.

## 7. Filtres

| Objectif | Filtre d'affichage |
| --- | --- |
| Tout le DHCP | `dhcp` |
| Par type | `dhcp.option.dhcp == 1` (Discover), `5` (ACK) |
| Un client | `dhcp.hw.mac_addr == aa:00:00:00:00:01` |
| Un serveur | `dhcp.option.dhcp_server_id == 192.168.1.1` |
| Bail court | `dhcp.option.ip_address_lease_time < 600` |
| DHCPv6 | `dhcpv6` |

En capture : `tcpdump 'udp port 67 or udp port 68'`.

## 8. Pièges

| Symptôme | Cause |
| --- | --- |
| `169.254.x.x` | pas de serveur, ou diffusion bloquée |
| Adresse correcte, pas de DNS | option 6 absente : `cat /etc/resolv.conf` |
| IP qui change à chaque réveil | bail court, ou identifiant client non stable |
| `ping` vers la passerelle OK, pas d'Internet | option 3 fausse, ou NAT absent |
| Deux postes avec la même IP | bail statique dupliqué, ou serveur non autorisé |
| Capture DHCP vide | port 67/68 filtré, ou capture hors du VLAN concerné |

## À retenir

- DORA : Discover, Offer, Request, ACK, tous liés par le `Transaction ID`.
- Un bail transporte adresse, passerelle, DNS, domaine, NTP : tout peut casser d'un coup.
- `169.254.x.x` = pas de DHCP, c'est un symptôme, pas une configuration.
- Deux serveurs DHCP sur un segment = incident de sécurité.
- En IPv6, SLAAC remplace l'attribution d'adresse, pas les options.

## Pour aller plus loin

- [1.8 HTTP et HTTPS](08-http-et-tls.md) — ce que le poste fait une fois configuré.
- Guide [Wireshark](../../README.md) : chapitres 4.6 (DHCP), 9.2 (analyse DHCP).
- RFC 2131 (DHCP), RFC 8415 (DHCPv6), RFC 4862 (SLAAC).
