---
title: "Ghost Authority · Ghost Authority (partie 1)"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/ghost-authority/ghost-authority-partie-1/writeup-ghost-authority.md"
license: "CC BY-SA 4.0"
status: published
---

# Ghost Authority — Write-up

## Objectif

- **Catégorie** : Forensics
- **Énoncé** : un poste analyste a été mis sous écoute toute une matinée. Parmi
  toutes les sessions TLS de la capture, une seule s'appuie sur une autorité que
  rien ne reconnaît. Trouver le **nom exact** de cette autorité.
- **Fichiers fournis** : `capture-poste.pcap`, `trusted-cas.pem`
- **Format attendu** : le flag suit le format standard de l'événement (nom exact de l'autorité entre accolades).

## État initial

- `trusted-cas.pem` : un bundle PEM contenant 5 autorités de certification (CA)
  auto-signées considérées comme « de confiance ».
- `capture-poste.pcap` : capture réseau de ~2,5 Mo contenant un grand nombre de
  sessions TLS (SNI variés : `*.example`, plus un domaine suspect
  `c2.lynx-varelid.var`).

## Reconnaissance et interprétation

L'énoncé indique qu'une seule session TLS repose sur une CA absente de la liste
de confiance. La démarche est donc :

1. Lister les CA de confiance fournies.
2. Extraire la chaîne de certificats de **chaque** session TLS de la capture.
3. Identifier le certificat émetteur (issuer) qui ne figure **pas** dans la liste
   de confiance.

Le fichier de lore du CTF mentionnait déjà une piste : une autorité privée liée à
Borealis Analytics (Norveth). Le domaine `c2.lynx-varelid.var` — l'infra C2 du
groupe « Lynx Varelien » (VARELID, attribué à Varelia) — est le candidat naturel.

## Commandes et observations

### 1. CA de confiance

```bash
openssl crl2pkcs7 -nocrl -certfile trusted-cas.pem \
  | openssl pkcs7 -print_certs -noout
```

Les 5 sujets reconnus :

```
CN=ISG E5, O=Internet Security Group
CN=Sectrust RSA Domain Validation Secure Server CA, O=Sectrust
CN=GlobalNex GCC R6 DV TLS CA 2024, O=GlobalNex
CN=cPortal, Inc. Certification Authority, O=cPortal, Inc.
CN=Unatel RSA 2048 M03, O=Unatel
```

### 2. Inventaire des sessions TLS (SNI)

```bash
tshark -r capture-poste.pcap -Y "tls.handshake.type==1" \
  -T fields -e tcp.stream -e tls.handshake.extensions_server_name
```

Une destination se démarque des autres (toutes des `*.example`) :

```
137  203.0.113.47   c2.lynx-varelid.var
```

### 3. Extraction du certificat de la session suspecte

```bash
tshark -r capture-poste.pcap -Y "tls.handshake.type==11 && tcp.stream==137" \
  -T fields -e tls.handshake.certificate
```

Conversion du DER en texte, puis lecture :

```bash
openssl x509 -inform DER -in cert0.der -noout -subject -issuer
openssl x509 -inform DER -in cert1.der -noout -subject -issuer
```

Résultat :

```
cert0 (feuille/serveur):
  subject = C=VR, O=VARELCORP, OU=Engenharia, CN=varelcorp.var,
            emailAddress=mateus.varga@varelcorp.var
  issuer  = C=XX, O=Borealis Trust Services, CN=Borealis Certification Authority

cert1 (autorité, racine auto-signée):
  subject = C=XX, O=Borealis Trust Services, CN=Borealis Certification Authority
  issuer  = C=XX, O=Borealis Trust Services, CN=Borealis Certification Authority
```

### 4. Vérification de l'unicité

Confirmation qu'**aucune** autre session TLS de la capture ne référence cette
autorité (les émetteurs des autres flux correspondent uniquement aux 5 CA de
confiance).

## Raisonnement menant à la solution

- La feuille de la session `c2.lynx-varelid.var` est signée par une autorité
  nommée **Borealis Certification Authority** (O=Borealis Trust Services), qui
  s'auto-signe (racine).
- Cette autorité ne figure pas dans `trusted-cas.pem` : c'est donc « l'autorité
  que rien ne reconnaît ».
- Le nom exact de l'autorité est le Common Name du certificat de CA :
  `Borealis Certification Authority`.
- Le nom correspond à l'indice de la lore (Borealis) et au contexte narratif
  (accusation contre Varelia, certificat au nom de VARELCORP et de l'ingénieur
  Mateus Varga).

## Pistes écartées

- Chercher un flag dans les données brutes (strings/binwalk) : non pertinent, la
  réponse est un nom d'autorité présent dans un certificat.
- Utiliser les 5 CA de confiance comme réponse : ce sont précisément les
  autorités reconnues, donc exclues.

## Validation (reproductible)

```bash
# 1) lister les CA de confiance
openssl crl2pkcs7 -nocrl -certfile trusted-cas.pem | openssl pkcs7 -print_certs -noout

# 2) extraire les certificats de la session TLS suspecte (tcp.stream==137)
tshark -r capture-poste.pcap -Y "tls.handshake.type==11 && tcp.stream==137" \
  -T fields -e tls.handshake.certificate > chain.txt

# 3) décoder chaque certificat (séparés par une virgule) et lire issuer/subject
openssl x509 -inform DER -in cert.der -noout -subject -issuer

# 4) constater que l'émetteur (Borealis Certification Authority) n'est PAS dans
#    trusted-cas.pem
```

Le Common Name de l'autorité non reconnue constitue la réponse attendue ; la
valeur soumise est reportée à la plateforme.
