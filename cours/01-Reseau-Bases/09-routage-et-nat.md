# 1.9 — Routage et NAT

> Fiche du chapitre 1.9 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Lire une table de routage** et expliquer quelle route gagne (plus long préfixe).
2. **Utiliser `ip route get`** pour répondre à « par où part ce paquet ».
3. **Décrire NAT et PAT** et lire une table de translation.
4. **Expliquer traceroute** par le TTL, et pourquoi il échoue parfois.
5. **Diagnostiquer** un aller qui marche et un retour qui ne revient pas.

## 1. La table de routage

```bash
ip route
```

```text
default via 169.254.1.1 dev eth0
169.254.1.1 dev eth0 scope link
```

Deux routes, deux comportements :

| Ligne | Sens |
| --- | --- |
| `default via …` | tout ce qui n'a pas de route plus précise part par là |
| `… dev eth0 scope link` | la passerelle est joignable directement, sans routeur intermédiaire |

Une table réelle en contient davantage : réseaux locaux, routes VPN, routes `blackhole`, routes
avec métrique.

**La règle qui décide** : le **plus long préfixe** gagne. `10.1.2.0/24` bat `10.0.0.0/8`, qui bat
`default`. La métrique ne sert qu'à départager deux routes de même préfixe.

## 2. Savoir par où part un paquet

```bash
ip route get 8.8.8.8
```

```text
8.8.8.8 via 169.254.1.1 dev eth0 src 10.2.21.53 uid 10001
    cache
```

La commande donne trois informations : la passerelle, l'interface et l'**adresse source** choisie.
C'est la source qui pose problème dans la majorité des cas : un serveur avec deux cartes peut
répondre depuis la mauvaise, et le client jette la réponse.

## 3. TTL et traceroute

Chaque routeur décrémente le TTL. À zéro, il jette le paquet et renvoie un ICMP *time exceeded*.

`traceroute` exploite exactement cela : il envoie des paquets avec un TTL de 1, puis 2, puis 3, et
lit l'adresse du routeur qui répond à chaque fois.

| Observation | Interprétation |
| --- | --- |
| `* * *` sur une ligne | routeur qui ne répond pas en ICMP (fréquent, souvent sans gravité) |
| Sauts qui se répètent | boucle de routage, ou réponses hors séquence |
| Latence qui saute d'un coup | changement de chemin, ou lien saturé |
| Arrêt après 3 sauts alors que la cible est loin | ICMP filtré sur le chemin |
| `!H` | hôte injoignable : route absente côté destination |

`traceroute` en UDP (par défaut sur Linux) et `traceroute -I` (ICMP) ne donnent pas toujours le même
résultat, parce que les filtres ne traitent pas les deux de la même façon.

## 4. NAT et PAT

| Type | Ce qui change | Usage |
| --- | --- | --- |
| SNAT | adresse source | sortie d'un réseau privé vers Internet |
| MASQUERADE | adresse source = celle de l'interface | lien à IP dynamique (box, VPS) |
| DNAT | adresse destination | redirection de port vers un serveur interne |
| PAT | ports aussi | plusieurs clients derrière une seule IP |

Table NAT d'un système sans règle :

```bash
sudo iptables -t nat -L -n -v
```

```text
Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain INPUT (policy ACCEPT 0 packets, 0 bytes)

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
```

Trois chaînes, trois moments :

- **PREROUTING** : avant le routage, donc pour du DNAT ;
- **INPUT** : trafic destiné à la machine elle-même ;
- **OUTPUT** : trafic émis par la machine.

Le suivi des connexions est tenu par `nf_conntrack` :

```bash
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
```

```text
0
131072
```

Une table pleine se traduit par des paquets jetés sans message clair : `nf_conntrack: table full`.
C'est une panne classique sur un routeur très sollicité.

## 5. Routage avancé

```bash
ip rule
```

```text
0:      from all lookup local
32766:  from all lookup main
32767:  from all lookup default
```

Les priorités se lisent de bas en haut. `local` d'abord (adresses de la machine), puis `main`
(la table par défaut), puis `default`. Un VPN ajoute souvent une table dédiée et une règle avant
`main` : c'est ainsi qu'il capture le trafic.

## 6. Quand le retour ne revient pas

Le symptôme : `SYN` part, rien ne revient, alors que la destination répond à d'autres.

| Cause | Vérification |
| --- | --- |
| route de retour absente sur le serveur | `ip route get <ip_client>` côté serveur |
| `rp_filter` strict | `cat /proc/sys/net/ipv4/conf/all/rp_filter` (1 = strict) |
| pare-feu stateful qui n'a pas vu le SYN | `conntrack -L`, journaux du pare-feu |
| NAT asymétrique | capture des deux côtés : les adresses ne correspondent pas |
| MTU trop grand | ICMP « fragmentation needed » filtré : `ping -M do -s 1400` |

`rp_filter` mérite une note : en mode strict (valeur `1`, état par défaut ici), le noyau jette un
paquet entrant dont l'adresse source n'est pas joignable par l'interface d'arrivée. Sur un routeur
avec deux liens, cela casse le trafic asymétrique — c'est voulu, mais surprenant.

## 7. Filtres utiles en capture

| Objectif | Filtre |
| --- | --- |
| TTL qui décroît | `ip.ttl < 64` |
| ICMP de diagnostic | `icmp.type == 11` (time exceeded), `3` (unreachable) |
| Un flux précis | `ip.addr == 10.0.0.5 && tcp.port == 443` |
| Fragmentation nécessaire | `icmp.type == 3 && icmp.code == 4` |

## 8. Pièges

| Symptôme | Cause |
| --- | --- |
| Ping OK, connexion TCP non | route de retour ou pare-feu stateful |
| `traceroute` s'arrête tôt | ICMP filtré, pas une panne |
| Deux machines derrière NAT, même port source | PAT : la traduction se fait par port |
| Connexions qui expirent après 5 min | bail conntrack trop court pour du TCP inactif |
| MTU 1500 côté LAN, 1400 côté VPN | MSS clamping nécessaire sur le routeur |
| `ip route get` donne une source inattendue | plusieurs adresses sur l'interface, ou policy routing |

## À retenir

- Le plus long préfixe gagne ; la métrique départage à préfixe égal.
- `ip route get` donne passerelle, interface et **adresse source**.
- Traceroute n'est que du TTL décrémenté ; `* * *` n'est pas une preuve de panne.
- NAT modifie les adresses, PAT aussi les ports : la capture doit être faite des deux côtés.
- Un aller qui marche et un retour qui ne revient pas : chercher la route de retour, pas le pare-feu.

## Pour aller plus loin

- [1.10 Diagnostic](10-diagnostic.md) — la méthode complète.
- Guide [Wireshark](../../README.md) : chapitres 3.3 (NAT), 10.2 (problème de connexion).
- RFC 1812 (routeurs), RFC 3022 (NAT), RFC 8899 (PMTUD).
