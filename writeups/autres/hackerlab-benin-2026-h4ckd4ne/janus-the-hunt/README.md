---
title: "Janus · The Hunt"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/janus/the-hunt/writeup-the-hunt.md"
license: "CC BY-SA 4.0"
status: published
---

# The hunt — adresse mail du suspect

## Objectif

Deux artefacts sont fournis : un binaire Linux `exfil` et `capture.pcap`.
L'analyse dynamique du binaire a produit la capture réseau. Il faut retrouver
l'adresse mail du suspect dans les données exfiltrées.

## Inventaire

```bash
unzip -l artefact.zip
#  14592  exfil
#  24842  capture.pcap

file exfil capture.pcap
# exfil: ELF 64-bit LSB pie executable, x86-64, stripped
# capture.pcap: pcap capture file, Ethernet
```

Le pcap ne contient que du DNS et de l'ICMP :

```text
eth/ip/udp/dns      168 frames
eth/ip/icmp          62 frames
```

Les requêtes DNS (`outlook.office365.com`, `github.com`, etc.) sont du bruit.
Le trafic utile part vers `203.0.113.15` en **ICMP Echo Request** avec un
payload de 48 octets précédé d'un en-tête de 4 octets.

## Analyse statique de exfil

Le binaire est strippé mais ses imports sont parlants : `socket`, `sendto`,
`inet_pton`, `fopen`, `fread`, `srand`, `rand`, `usleep`.

La fonction principale (`0x1140`) :

1. exige `argc > 2` : `exfil <ip> <fichier>` ;
2. crée une socket brute `AF_INET / SOCK_RAW / IPPROTO_ICMP` ;
3. convertit l'IP cible avec `inet_pton` ;
4. ouvre le fichier en mode `"rb"` ;
5. initialise `srand(time(NULL))` — utilisé uniquement pour le délai aléatoire
   entre paquets, pas pour le chiffrement ;
6. lit le fichier par blocs de `0x30` (48) octets ;
7. XOR chaque bloc avec une clé de 16 octets ;
8. construit un paquet ICMP : type `8`, identifiant `0x3713`, numéro de
   séquence, en-tête de 4 octets (longueur + séquence obfusquées), puis les
   données chiffrées ;
9. envoie le paquet et attend un délai aléatoire.

La clé XOR est générée par la fonction `0x1580` :

```text
key[i] = data_4080[i] ^ (3*i + 0x55)     pour i = 0..15
```

Les 16 octets de `.data` à `0x4080` sont :

```text
3b 68 29 2a 09 17 13 0b 1f 2f 41 46 4b 48 5e a3
```

Ce qui donne la clé :

```text
n0rthstar_2024!!
```

## Décodage des paquets ICMP

L'en-tête de 4 octets du payload contient, après obfuscation :

```text
[ len_low, len_high, (seq ^ 0xcafe)_low, (seq ^ 0xcafe)_high ]  (little-endian)
```

Exemple pour le paquet de séquence 1, longueur `0x30` :

```text
payload = ca ff 00 30 06 00 17 1a 01 0b 2b 59 ...
          \_______/  \________________________/
          en-tête            données XOR
```

Les paquets utiles sont les séquences 1 à 6 (le paquet 0 est un ping vide).
Leurs longueurs de données sont `48, 48, 48, 48, 48, 40`, soit 280 octets.

Déchiffrement :

```python
key = b"n0rthstar_2024!!"
plain = b""
for seq in sorted(chunks):
    enc = payload[4:]              # on retire l'en-tête de 4 octets
    plain += bytes(c ^ key[i % 16] for i, c in enumerate(enc))
```

## Résultat

Le fichier reconstitué est un rapport de session :

```text
h0enix_83
TS: 2024-09-15T14:22:07+01:00
VER: 2.3.1
--- SYSINFO ---
HOST: PC-MUSIC-01
ADDR: 192.168.1.45
USER: TARGETCORP\jdupont
OS: Windows 10 Pro x64
--- OPERATOR CONFIG ---
c2: 203.0.113.15
fallback: 203.0.113.42
contact: <redacted email>
interval: 300
--- END SESSION ---
```

La ligne `contact:` contient l'adresse mail du suspect. Elle a été reportée à la plateforme sous le challenge **The hunt** et est volontairement absente de ce
document.

## Pistes écartées

- Les centaines de requêtes DNS sont des leurres : aucune ne contient de
  donnée encodée (noms légitimes, longueurs normales).
- Les pings vers `1.1.1.1`, `8.8.8.8` et `192.168.1.1` n'ont pas de payload.
- `srand(time(NULL))` ne sert pas au chiffrement : la clé XOR est constante et
  dérivée de `.data`. La capture n'a donc pas besoin d'être rejouée avec un
  seed particulier.
- Le paquet de séquence 0 ne contient que `00000000` : ce n'est pas une donnée
  utile mais un ping de contrôle.

## Validation reproductible

1. `objdump -s -j .data exfil` : lire les 16 octets à `0x4080`.
2. Calculer `key[i] = data[i] ^ (3*i + 0x55)`.
3. Extraire de la capture les ICMP Echo vers `203.0.113.15`.
4. Retirer les 4 premiers octets de chaque payload, XOR avec la clé, puis
   concaténer dans l'ordre des séquences.
5. Lire la ligne `contact:` : c'est l'adresse soumise.
