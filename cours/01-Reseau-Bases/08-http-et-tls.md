# 1.8 — HTTP et HTTPS/TLS

> Fiche du chapitre 1.8 du module [01 — Réseau : les bases](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

1. **Lire une requête et une réponse HTTP** dans une capture, sans le navigateur.
2. **Repérer les éléments sensibles** qui circulent en clair quand TLS est absent.
3. **Suivre un handshake TLS** : ClientHello, ServerHello, suite négociée.
4. **Expliquer ce qui reste visible** en TLS 1.3 (IP, SNI, ports, tailles, durées).
5. **Déchiffrer une capture TLS** avec `SSLKEYLOGFILE`, dans un cadre de test.

## 1. HTTP dans une capture

```bash
tshark -r http.pcap -Y http.request -T fields -e http.host -e http.user_agent \
       -e http.request.method -e http.request.uri
tshark -r http.pcap -Y http.response -T fields -e http.response.code \
       -e http.content_type -e http.content_length
```

```text
127.0.0.1:8080  curl/8.14.1     GET     /

200     text/html       8
```

Tout est en clair : méthode, chemin, `Host`, `User-Agent`, code de retour, type et taille. En
conditions réelles s'y ajoutent les cookies, les jetons `Authorization` et les formulaires — c'est
la démonstration classique d'un réseau non chiffré.

## 2. Ce qu'on cherche en premier

| Élément | Où le voir | Pourquoi c'est important |
| --- | --- | --- |
| `Host` | `http.host` | plusieurs sites sur une même IP |
| `User-Agent` | `http.user_agent` | outil utilisé : `curl`, navigateur, scanner |
| Cookie / `Authorization` | `http.cookie`, `http.authorization` | vol de session |
| Code de retour | `http.response.code` | 401/403 = accès, 500 = erreur serveur |
| `Referer` | `http.referer` | enchaînement de navigation |
| Taille et durée | `http.content_length`, `http.time` | téléchargement massif, exfiltration |

## 3. Handshake TLS

```bash
tshark -r tls.pcap -Y "tls.handshake.type == 1 || tls.handshake.type == 2" \
       -T fields -e frame.number -e tls.handshake.type -e tls.handshake.version \
       -e tls.handshake.ciphersuite
```

```text
4       1       0x0303  0x1302,0x1303,0x1301,0xc02c,0xc030,0x009f,0xcca9,...
6       2       0x0303  0x1302
```

Lecture :

- **trame 4, type 1** : ClientHello. `0x0303` = TLS 1.2 dans le champ historique, mais la liste de
  suites commence par `0x1302`, `0x1303`, `0x1301` — les suites TLS 1.3. La version réelle se
  négocie via l'extension `supported_versions`.
- **trame 6, type 2** : ServerHello, qui **choisit** `0x1302` (TLS_AES_256_GCM_SHA384).
- Aucun certificat visible : en TLS 1.3, le certificat est chiffré. C'est un changement majeur par
  rapport à TLS 1.2, où il s'observait en clair.

| Suite | Signification |
| --- | --- |
| `0x1301` | TLS_AES_128_GCM_SHA256 |
| `0x1302` | TLS_AES_256_GCM_SHA384 |
| `0x1303` | TLS_CHACHA20_POLY1305_SHA256 |
| `0xc02f` | TLS 1.2, ECDHE_RSA_AES128_GCM |

## 4. Ce qui reste visible malgré TLS

| Visible | Invisible |
| --- | --- |
| adresses IP source et destination | chemin, en-têtes HTTP, cookies |
| ports, donc le service | corps des requêtes et réponses |
| SNI (nom d'hôte) dans ClientHello | certificat (TLS 1.3) |
| tailles et horodatages des paquets | contenu applicatif |
| durée de la connexion | — |

Le SNI est la dernière information nominative en clair sur une connexion HTTPS classique. D'où
**ECH** (Encrypted Client Hello), encore peu déployé, et le recours à l'analyse par IP et par
volume quand SNI disparaît.

## 5. Déchiffrer une capture, en lab

TLS n'est pas cassé : on fournit la clé de session. Les bibliothèques OpenSSL, NSS et BoringSSL
savent écrire les secrets dans un fichier si `SSLKEYLOGFILE` est défini.

```bash
export SSLKEYLOGFILE=$PWD/keys.log
curl -sk https://127.0.0.1:8443/ -o /dev/null
tshark -r tls.pcap -o tls.keylog_file:keys.log -Y http
```

Trois conditions, sinon rien ne se déchiffre :

1. le client doit écrire le fichier de clés (navigateur avec variable d'environnement, `curl`,
   Python `ssl`);
2. la capture doit contenir le handshake complet ;
3. le fichier de clés doit correspondre **à cette session**, pas à une autre.

C'est la méthode de référence en analyse d'incident autorisée, et en CTF réseau.

## 6. Codes de retour utiles

| Code | Sens | Piège fréquent |
| --- | --- | --- |
| 200 | OK | — |
| 301 / 302 | redirection | vers HTTP alors que HTTPS était attendu |
| 304 | non modifié | cache navigateur, pas une erreur |
| 401 | authentification requise | en-tête `Authorization` absent |
| 403 | interdit | authentifié mais non autorisé |
| 404 | introuvable | chemin, pas hôte : le `Host` peut être en cause |
| 429 | trop de requêtes | limitation côté serveur |
| 502 / 504 | erreur passerelle / délai | le reverse proxy n'atteint pas l'amont |

## 7. Filtres

| Objectif | Filtre d'affichage |
| --- | --- |
| Requêtes | `http.request` |
| Réponses | `http.response` |
| Une méthode | `http.request.method == "POST"` |
| Un hôte | `http.host contains "exemple"` |
| Cookies | `http.cookie` |
| Erreurs | `http.response.code >= 400` |
| Handshake TLS | `tls.handshake.type == 1` (client), `2` (serveur) |
| Alerte TLS | `tls.alert_message` |
| Nom de serveur | `tls.handshake.extensions_server_name` |

## 8. Pièges

| Symptôme | Cause |
| --- | --- |
| Port 443 mais aucune donnée lisible | c'est du TLS, tout est chiffré |
| Port 80 avec du binaire | service non HTTP sur un port habituel |
| Certificat absent de la capture | TLS 1.3 chiffre le certificat |
| `http` ne matche rien sur 443 | il faut `tls`, pas `http` |
| SNI vide | connexion par IP, ou ECH |
| Déchiffrement impossible | fichier de clés d'une autre session, ou handshake absent |
| Trames énormes marquées « malformées » | segmentation/reassembly : voir les options TCP |

## À retenir

- HTTP en clair expose méthode, chemin, cookies et jetons : c'est la preuve d'audit classique.
- TLS négocie une suite ; TLS 1.3 chiffre le certificat dès le ServerHello.
- Restent visibles : IP, ports, SNI, tailles, durées.
- Le déchiffrement passe par `SSLKEYLOGFILE`, jamais par un cassage.
- Un 404 parle du chemin ; un 403 parle de droits ; un 502 parle du proxy.

## Pour aller plus loin

- [1.9 Routage et NAT](09-routage-et-nat.md) — le chemin emprunté avant d'arriver au serveur.
- Guide [Wireshark](../../README.md) : chapitres 4.7 (HTTP/TLS), 9.5, 9.6.
- RFC 9110 (HTTP sémantique), RFC 8446 (TLS 1.3), RFC 6066 (SNI).
