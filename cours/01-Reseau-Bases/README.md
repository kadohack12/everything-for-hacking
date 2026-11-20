# 01 — Réseau : les bases

[← Programme](../README.md)

## Objectifs

À la fin du module, je dois pouvoir : expliquer le modèle OSI/TCP-IP, calculer un sous-réseau,
suivre une connexion TCP de bout en bout et justifier chaque trame capturée dans Wireshark.

## Prérequis

Aucun. Savoir ouvrir un terminal.

## Plan

| # | Chapitre | Contenu clé | Lab |
| --- | --- | --- | --- |
| 1.1 | Modèles en couches | OSI vs TCP/IP, encapsulation, PDU | dissection d'une requête HTTP |
| 1.2 | Adressage IPv4 | classes, masque, CIDR, VLSM | découper `192.168.1.0/24` en 4 sous-réseaux |
| 1.3 | IPv6 | notation, préfixes, SLAAC | ping6 entre deux VM |
| 1.4 | Couche 2 | Ethernet, ARP, VLAN, switch | ARP spoof en lab isolé |
| 1.5 | TCP / UDP | handshake, flags, fenêtre, ports | suivre un `curl` dans Wireshark |
| 1.6 | DNS | résolution récursive, types, cache | `dig +trace` |
| 1.7 | DHCP | DORA, baux | capture d'un bail |
| 1.8 | HTTP / HTTPS | requêtes, codes, TLS handshake | capture d'un handshake TLS 1.3 |
| 1.9 | Routage & NAT | table de routage, PAT, TTL | traceroute + NAT sur routeur Linux |
| 1.10 | Diagnostic | ping, traceroute, ss, tcpdump | analyser une panne simulée |

## Labs récapitulatifs

- **Lab A** — réseau à 3 VM (client, routeur Linux, serveur web) : faire passer du HTTP à travers le routeur avec NAT.
- **Lab B** — capture Wireshark d'une session complète : DNS → TCP handshake → HTTP → FIN.
- **Lab C** — panne volontaire (mauvais masque, mauvaise passerelle) à diagnostiquer.

## Outils

`ip` / `ifconfig` · `ss` · `tcpdump` · `Wireshark` · `dig` · `traceroute` · `nmap`

## Ressources

- Guide [Wireshark](../README.md) (dépôt `guide-wireshark`)
- RFC 791 (IP), RFC 793 (TCP), RFC 1035 (DNS)

## Notes

> À compléter au fil du module. Un fichier par chapitre si le contenu devient long :
> `01-modeles.md`, `02-ipv4.md`, …
