# 1.10 — Diagnostic méthodique

> Fiche du chapitre 1.10 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Poser quatre questions** avant de lancer un outil, et éviter le tâtonnement.
2. **Choisir l'outil** selon la couche concernée, pas selon l'habitude.
3. **Diagnostiquer trois pannes classiques** : mauvaise passerelle, mauvais masque, DNS cassé.
4. **Prouver** une conclusion avec une capture, pas avec une impression.
5. **Documenter** un diagnostic de façon réutilisable.

## 1. Les quatre questions

Avant tout outil :

| Question | Réponse cherchée | Outil |
| --- | --- | --- |
| La machine a-t-elle une adresse ? | IP, masque, passerelle | `ip -br addr`, `ip route` |
| Le voisin répond-il ? | couche 2 et 3 locales | `ip neigh`, `ping <passerelle>` |
| Le nom se résout-il ? | couche 7 (DNS) | `dig`, `getent hosts` |
| Le service répond-il ? | port et application | `ss`, `nc -vz`, `curl -v` |

L'ordre compte : une panne de couche 2 rend inutile tout test applicatif. Vérifier dans l'ordre
évite de « déboguer » un serveur web quand le câble est débranché.

## 2. La table de décision

| Symptôme | Couche probable | Première vérification |
| --- | --- | --- |
| `ip -br addr` sans adresse | 2/3 | câble, Wi-Fi, DHCP |
| adresse en `169.254.x.x` | 3 (DHCP) | serveur DHCP, VLAN |
| passerelle injoignable | 2/3 | `ip neigh`, ARP, VLAN |
| passerelle OK, IP externe non | 3 | `ip route get`, NAT, pare-feu |
| IP externe OK, nom non | 7 (DNS) | `dig @résolveur`, `/etc/resolv.conf` |
| nom OK, port fermé | 4 | `nc -vz`, `ss -ltnp` |
| port ouvert, application en erreur | 7 | journaux, codes HTTP |
| tout OK mais lent | 4/7 | `dns.time`, retransmissions, RTT |

## 3. Le kit d'outils, par couche

| Couche | Outils | Ce qu'ils répondent |
| --- | --- | --- |
| 2 | `ip neigh`, `bridge fdb`, `tcpdump -e` | qui est sur le segment, quelle MAC |
| 3 | `ip addr`, `ip route`, `ip route get`, `ping`, `traceroute` | adressage, chemin |
| 4 | `ss -tunap`, `nc -vz`, `tcpdump 'tcp port …'` | qui écoute, qui parle |
| 7 | `dig`, `curl -v`, `openssl s_client` | nom, contenu, certificat |

Deux commandes sous-estimées :

- `ss -tunap` montre l'état **réel** des sockets, y compris celles en `CLOSE-WAIT` qui trahissent
  une fuite applicative ;
- `curl -v` montre la résolution, la connexion, le handshake TLS et les en-têtes, dans l'ordre.

## 4. Lab A : mauvais masque

Deux machines sur le même switch, `192.168.1.10/24` et `192.168.1.20/25`.

`192.168.1.20/25` croit que son réseau s'arrête à `192.168.1.127`. Elle voit `.10` comme extérieure
et envoie donc à sa passerelle. Sans passerelle, ou avec une passerelle qui ne route pas, rien ne
passe — alors que le câble et les adresses sont corrects.

Diagnostic :

```bash
ip -br addr                 # comparer les deux masques
ip route get 192.168.1.20   # côté .10 : direct ? via passerelle ?
```

Sur `.10/24`, `ip route get 192.168.1.20` répond `dev eth0` sans passerelle. Sur `.20/25`, la même
commande pour `.10` répond `via <passerelle>`. La conclusion est immédiate.

## 5. Lab B : mauvaise passerelle

Adresse correcte, passerelle inexistante (`192.168.1.254` alors que le routeur est `.1`).

| Test | Résultat attendu | Interprétation |
| --- | --- | --- |
| `ping 192.168.1.20` (voisin) | OK | la couche 2 fonctionne |
| `ip neigh` | entrée du voisin `REACHABLE` | ARP résolu |
| `ping 192.168.1.254` | échec | passerelle absente |
| `ping 8.8.8.8` | échec | rien ne route |
| `dig` | échec ou lenteur | dépend du résolveur, souvent local |

La preuve : `ip neigh` affiche une entrée `INCOMPLETE` ou `FAILED` pour la passerelle, ce qui
signifie « ARP sans réponse » — donc aucune machine à cette adresse sur le segment.

## 6. Lab C : DNS cassé

Tout fonctionne sauf les noms.

```bash
ip route get 8.8.8.8          # chemin OK
ping -c1 8.8.8.8              # IP joignable
dig +short example.com        # échec
dig @1.1.1.1 +short example.com   # succès
```

Si le dernier test réussit, le problème est le résolveur configuré, pas le réseau. Vérifier :

```bash
cat /etc/resolv.conf
systemd-resolve --status 2>/dev/null | head -20
```

Les causes fréquentes : option DHCP 6 absente, résolveur interne éteint, `ndots` trop élevé,
pare-feu qui bloque le port 53 sortant.

## 7. Prouver, puis documenter

Une capture vaut mieux qu'une affirmation. Le squelette d'une preuve :

```bash
sudo tcpdump -i eth0 -nn -w preuve.pcap 'host 192.168.1.20 and (arp or icmp)'
tshark -r preuve.pcap -Y "arp.opcode == 1" -T fields -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4
```

Un compte rendu utile tient en cinq lignes :

```text
Symptôme   : .20 ne joint pas .10, alors que .10 joint .20
Mesure     : ip -br addr -> .20 en /25 ; ip route get -> via passerelle
Preuve     : arp sans réponse pour la passerelle (capture preuve.pcap)
Cause      : masque /25 au lieu de /24
Correction : ip addr del/dev avec /24, ou bail DHCP corrigé
```

## 8. Pièges

| Piège | Conséquence |
| --- | --- |
| Tester l'application avant la couche 3 | on débogue au mauvais endroit |
| Conclure « hôte mort » sur un `ping` muet | ICMP filtré : tester un port TCP |
| Oublier le cache ARP / DNS | on observe un état périmé, pas la réalité |
| Capturer sur la mauvaise interface | on ne voit rien et on conclut à une panne |
| Ignorer l'heure des captures | deux captures décalées ne se comparent pas |
| Ne pas noter la version de libc/OS | un diagnostic non reproductible ne sert qu'une fois |

## À retenir

- Quatre questions, dans l'ordre : adresse, voisin, nom, service.
- Une panne de couche 2 invalide tous les tests au-dessus.
- `ip route get` et `ip neigh` tranchent la majorité des cas locaux.
- `dig @autre-résolveur` sépare « réseau cassé » de « DNS cassé ».
- Un diagnostic se prouve par une capture et se documente en cinq lignes.

## Pour aller plus loin

- [1.11 Wireshark en pratique](11-wireshark-pratique.md) — les filtres et les statistiques.
- Guide [Wireshark](../../README.md) : chapitre 10 (dépannage méthodique), 12 (travaux pratiques).
- RFC 1122 (exigences des piles TCP/IP), RFC 8085 (bonnes pratiques UDP).
