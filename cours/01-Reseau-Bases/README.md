# 01 — Réseau : les bases

[← Programme](../README.md)

## Objectifs

À la fin du module, je dois pouvoir : expliquer le modèle OSI/TCP-IP, calculer un sous-réseau,
suivre une connexion TCP de bout en bout et **justifier chaque trame capturée dans Wireshark**.

Concrètement :

- décrire l'encapsulation et nommer la couche d'un problème avant de sortir un outil ;
- calculer un plan d'adressage IPv4 (CIDR, VLSM) et lire un adressage IPv6 ;
- expliquer ARP, VLAN, TCP, UDP, DNS, DHCP, HTTP et TLS à partir d'une capture ;
- diagnostiquer une panne en quatre questions, avec une preuve et non une impression.

## Prérequis

Aucun. Savoir ouvrir un terminal. Pour les labs : `iproute2`, `tcpdump`, `tshark`, `dnsutils`,
`nmap`, et Wireshark en interface graphique.

## Plan

| # | Chapitre | Contenu clé | Lab |
| --- | --- | --- | --- |
| 1.1 | [Modèles en couches](01-modele-osi-et-tcp-ip.md) | OSI vs TCP/IP, encapsulation, PDU | dissection d'une requête HTTP |
| 1.2 | [Adressage IPv4](02-adressage-ipv4.md) | masque, CIDR, VLSM, plages privées | découper `192.168.1.0/24` en 4 |
| 1.3 | [IPv6](03-ipv6.md) | notation, préfixes, NDP, SLAAC | capture NS/NA/RA |
| 1.4 | [Couche 2](04-couche-2-ethernet-arp-vlan.md) | Ethernet, ARP, VLAN 802.1Q | détecter un ARP spoof |
| 1.5 | [TCP / UDP](05-tcp-udp.md) | handshake, drapeaux, fenêtre, ports | suivre un `curl` dans Wireshark |
| 1.6 | [DNS](06-dns.md) | résolution récursive, types, cache | `dig +trace` et capture |
| 1.7 | [DHCP](07-dhcp.md) | DORA, options, baux | lire un cycle DORA complet |
| 1.8 | [HTTP / HTTPS](08-http-et-tls.md) | requêtes, codes, handshake TLS | capture d'un handshake TLS 1.3 |
| 1.9 | [Routage & NAT](09-routage-et-nat.md) | table de routage, PAT, TTL | `ip route get` + analyse de retour |
| 1.10 | [Diagnostic](10-diagnostic.md) | méthode en 4 questions, 3 pannes | diagnostiquer une panne simulée |
| 1.11 | [Wireshark en pratique](11-wireshark-pratique.md) | filtres, tshark, statistiques | analyse d'une capture inconnue |

## Fiches de chapitre

| Chapitre | Fiche | État |
| --- | --- | --- |
| 1.1 Modèles en couches | [01 — Modèle OSI, TCP/IP et encapsulation](01-modele-osi-et-tcp-ip.md) | rédigée |
| 1.2 Adressage IPv4 | [02 — Adressage IPv4, masques et sous-réseaux](02-adressage-ipv4.md) | rédigée |
| 1.3 IPv6 | [03 — IPv6 : notation, préfixes et voisinage](03-ipv6.md) | rédigée |
| 1.4 Couche 2 | [04 — Couche 2 : Ethernet, ARP et VLAN](04-couche-2-ethernet-arp-vlan.md) | rédigée |
| 1.5 TCP / UDP | [05 — TCP et UDP](05-tcp-udp.md) | rédigée |
| 1.6 DNS | [06 — DNS : résolution, cache et analyse](06-dns.md) | rédigée |
| 1.7 DHCP | [07 — DHCP : obtenir une adresse](07-dhcp.md) | rédigée |
| 1.8 HTTP / HTTPS | [08 — HTTP et HTTPS/TLS](08-http-et-tls.md) | rédigée |
| 1.9 Routage & NAT | [09 — Routage et NAT](09-routage-et-nat.md) | rédigée |
| 1.10 Diagnostic | [10 — Diagnostic méthodique](10-diagnostic.md) | rédigée |
| 1.11 Wireshark | [11 — Wireshark en pratique](11-wireshark-pratique.md) | rédigée |

## Labs récapitulatifs

- **Lab A** — réseau à 3 VM (client, routeur Linux, serveur web) : faire passer du HTTP à travers
  le routeur avec NAT, et le prouver par deux captures (avant/après traduction).
- **Lab B** — capture Wireshark d'une session complète : DNS → TCP handshake → HTTP → FIN, avec
  les filtres de chaque étape.
- **Lab C** — panne volontaire (mauvais masque, mauvaise passerelle, DNS cassé) à diagnostiquer
  sans accès au routeur, uniquement avec les outils locaux et une capture.

## Comment les captures de ce module ont été produites

Deux méthodes, toutes deux reproductibles :

1. **Trafic réel capturé** sur la machine de rédaction : HTTP et TLS sur la boucle locale
   (`python3 -m http.server`, serveur HTTPS auto-signé), DNS vers le résolveur du réseau, scan SYN
   `nmap` vers un service local. Les sorties `tshark` et `tcpdump` de ces captures sont recopiées
   telles quelles.
2. **Captures générées avec scapy** pour les protocoles impossibles à provoquer dans un conteneur
   (ARP, DHCP, VLAN, IPv6/NDP, traceroute) : les trames sont écrites dans un `.pcap` puis relues par
   `tshark`. Le script de génération est donné dans le chapitre concerné, et les adresses suivent la
   documentation (RFC 5737 : `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).

Les chiffres (TTL, ports, numéros de séquence, durées) sont ceux des captures, jamais des valeurs
plausibles inventées.

## Outils

`ip` · `ss` · `tcpdump` · `tshark` · `Wireshark` · `dig` · `nmap` · `traceroute` · `nc` ·
`capinfos` · `editcap`

## Ressources

- Guide [Maîtriser les réseaux avec Wireshark](https://github.com/kadohack12/guide-wireshark), MIT.
- RFC 791 (IP), RFC 793/9293 (TCP), RFC 826 (ARP), RFC 1035 (DNS), RFC 2131 (DHCP),
  RFC 8446 (TLS 1.3).
- Documentation officielle Wireshark : <https://www.wireshark.org/docs/>

## Crédits

Ce module s'appuie sur le guide **« Maîtriser les réseaux avec Wireshark »**
([`kadohack12/guide-wireshark`](https://github.com/kadohack12/guide-wireshark)), publié sous licence
MIT, © 2026 Kadohack12. Les chapitres 1.4 à 1.11 en reprennent la progression et les choix
pédagogiques, réécrits pour ce dépôt et complétés par des labs exécutés localement.

## Notes

> Un fichier par chapitre : `NN-nom-du-chapitre.md` (ex. `01-modele-osi-et-tcp-ip.md`).
> Toute nouvelle fiche doit être ajoutée au tableau « Fiches de chapitre » ci-dessus.
> Après modification de `cours/`, régénérer l'empreinte : `python3 scripts/check_cours.py --update`.
