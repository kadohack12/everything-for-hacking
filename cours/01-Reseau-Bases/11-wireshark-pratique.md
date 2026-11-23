# 1.11 — Wireshark en pratique

> Fiche du chapitre 1.11 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Capturer sans être root**, proprement, sur le bon point de capture.
2. **Distinguer filtre de capture et filtre d'affichage** et ne plus confondre la syntaxe.
3. **Enchaîner les huit étapes** d'une analyse qui aboutit à une conclusion.
4. **Utiliser la ligne de commande** : `dumpcap`, `tshark`, `capinfos`, `editcap`.
5. **Éviter les cinq pièges** qui font croire à une panne réseau qui n'existe pas.

## 1. Installation et droits

```bash
sudo apt install wireshark tshark
sudo usermod -aG wireshark "$USER"     # puis se reconnecter
```

Le paquet configure `dumpcap` avec la capacité `cap_net_raw` pour le groupe `wireshark` : la
capture devient possible sans `sudo`. Vérification :

```bash
getcap /usr/bin/dumpcap
```

```text
/usr/bin/dumpcap cap_net_admin,cap_net_raw=eip
```

Sur Windows, l'installateur propose Npcap, avec une case « support du mode moniteur » à cocher si
l'on veut capturer du Wi-Fi.

## 2. Le bon point de capture

| Emplacement | Ce qu'on voit |
| --- | --- |
| sur la machine | son trafic, plus diffusion et multicast |
| port miroir (SPAN) | tout un port de switch |
| TAP passif | tout un lien, sans perturbation |
| agrégation (LACP) | le flux agrégé, parfois désordonné |
| conteneur / veth | souvent seulement une extrémité |

Une capture réseau ne montre **que** ce qui passe devant la carte. Un `SYN` absent de la capture
peut très bien avoir été envoyé : la capture a lieu après le pare-feu local, ou sur l'autre
interface.

## 3. Deux syntaxes à ne pas confondre

| | Filtre de capture | Filtre d'affichage |
| --- | --- | --- |
| Syntaxe | BPF (libpcap) | langage Wireshark |
| Quand | pendant la capture | après, sur les paquets |
| Effet | jette ce qui ne correspond pas | masque seulement |
| Exemple | `tcp port 443 and host 10.0.0.5` | `tcp.port == 443 && ip.addr == 10.0.0.5` |
| Test d'égalité | `port 443` | `tcp.port == 443` |
| ET logique | `and` | `&&` |
| Non | `not` | `!` |
| Sous-chaîne | — | `contains` |

Erreur classique : taper `tcp.port == 443` dans la barre de capture. Réponse de Wireshark :
`syntax error`. Un filtre de capture trop restrictif est pire : les paquets sont **perdus**, pas
masqués.

## 4. Filtres d'affichage à connaître

| Objectif | Filtre |
| --- | --- |
| Un hôte | `ip.addr == 10.0.0.5` |
| Un flux | `tcp.stream eq 3` |
| Un port | `tcp.port == 443` |
| Ouvertures TCP | `tcp.flags.syn == 1 && tcp.flags.ack == 0` |
| Réinitialisations | `tcp.flags.reset == 1` |
| Retransmissions | `tcp.analysis.retransmission` |
| DNS sans réponse | `dns.flags.response == 0` |
| Erreurs DNS | `dns.flags.rcode != 0` |
| HTTP en erreur | `http.response.code >= 400` |
| ARP | `arp` |
| VLAN | `vlan.id == 42` |
| Handshake TLS | `tls.handshake.type == 1` |

Les opérateurs se combinent : `ip.addr == 10.0.0.5 && tcp.port == 443 && !arp`.

## 5. Huit étapes d'analyse

| Étape | Question | Geste |
| --- | --- | --- |
| 1 | Quelle est la question ? | l'écrire avant d'ouvrir le fichier |
| 2 | L'original est-il préservé ? | copier le pcap, ne jamais travailler sur l'unique copie |
| 3 | Quel volume ? | `capinfos`, `-z io,phs` |
| 4 | Réduire le bruit | un filtre d'affichage ciblé |
| 5 | Qui parle à qui ? | `-z conv,tcp` |
| 6 | Suivre un flux | clic droit → Follow → TCP Stream |
| 7 | Mesurer | `dns.time`, `tcp.analysis.ack_rtt`, retransmissions |
| 8 | Documenter | capture + commande + conclusion |

L'étape 3 évite d'ouvrir un fichier de 2 Go à la main. L'étape 7 distingue « ça a l'air lent » de
« 340 ms de RTT et 4 % de retransmissions ».

## 6. La ligne de commande

```bash
capinfos capture.pcap
```

```text
File name:           /tmp/http.pcap
File type:           Wireshark/tcpdump/... - pcap
File encapsulation:  Ethernet
Number of packets:   12
File size:           1294 bytes
Capture duration:    0.003595 seconds
```

```bash
tshark -r capture.pcap -q -z io,phs
```

```text
===================================================================
Protocol Hierarchy Statistics
Filter:

eth                                      frames:12 bytes:1078
  ip                                     frames:12 bytes:1078
    tcp                                  frames:12 bytes:1078
      http                               frames:2 bytes:218
```

```bash
tshark -r capture.pcap -q -z conv,tcp
```

```text
127.0.0.1:52488            <-> 127.0.0.1:8080                   5 530 bytes       7 548 bytes      12 1078 bytes
```

`conv,tcp` répond à « qui parle à qui, et combien » en une seconde : c'est le premier tableau à
regarder sur une capture inconnue.

Découper un gros fichier :

```bash
editcap -c 5 capture.pcap morceau.pcap
```

```text
morceau_00000_20261123220033.pcap
morceau_00001_20261123220034.pcap
morceau_00002_20261123220034.pcap
```

`editcap` sert aussi à convertir (`-F pcapng`), à filtrer par plage horaire (`-A`/`-B`) et à
supprimer les doublons (`-d`).

## 7. Les cinq pièges

| Piège | Effet | Parade |
| --- | --- | --- |
| Checksum incorrect | Wireshark signale une erreur qui n'existe pas | offload de la carte : ignorer, ou capturer ailleurs |
| Snap length trop court | paquets tronqués, application illisible | `-s 0` (tout capturer) |
| Segmentation / reassembly | « données non disséquées » | activer le reassembly TCP, regarder les segments |
| Chiffrement | tout illisible au-delà du handshake | `SSLKEYLOGFILE` en lab, sinon analyse par IP/volume |
| Fichier énorme | Wireshark sature | `editcap` pour découper, `tshark` pour filtrer |

Un checksum faux est le piège le plus fréquent : la carte réseau calcule les checksums après la
capture, donc la capture montre des valeurs nulles ou fausses. Ce n'est pas une anomalie de sécurité.

## 8. Pièges de méthode

| Erreur | Conséquence |
| --- | --- |
| Capturer sans filtre sur un lien chargé | Go de données, analyse impossible |
| Filtrer en capture puis chercher autre chose | les paquets sont perdus, il faut recapturer |
| Comparer deux captures sans horloge commune | conclusions fausses sur les délais |
| Conclure sur un seul paquet | il faut le contexte du flux |
| Oublier la version de l'outil | un bug de dissection peut ressembler à une attaque |

## À retenir

- `dumpcap` avec capacité : capture sans root ; le point de capture décide de tout.
- Capture = BPF (`and`, `port 443`) ; affichage = Wireshark (`&&`, `tcp.port == 443`).
- `capinfos` puis `-z io,phs` puis `-z conv,tcp` : trois commandes pour comprendre une capture.
- Huit étapes, de la question à la preuve documentée.
- Checksum faux, snaplen court, chiffrement : trois artefacts à ne pas confondre avec une panne.

## Pour aller plus loin

- Guide [Wireshark](../../README.md) (dépôt `guide-wireshark`, MIT) : chapitres 5 à 11 et les dix
  travaux pratiques.
- Documentation officielle : <https://www.wireshark.org/docs/>
- `man tshark`, `man dumpcap`, `man editcap`, `man capinfos`.
