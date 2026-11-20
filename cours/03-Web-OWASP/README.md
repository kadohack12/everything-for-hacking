# 03 — Web : OWASP Top 10

[← Programme](../README.md)

## Objectifs

Comprendre les 10 catégories de risques OWASP, savoir les détecter avec un proxy et les exploiter
dans un lab, puis proposer la contre-mesure côté code et côté configuration.

## Prérequis

- Module [01 — Réseau](../01-Reseau-Bases/README.md) (HTTP/HTTPS)
- Bases HTML/JS et un langage serveur (PHP ou Python)

## Plan — OWASP Top 10 (2021)

| # | Catégorie | Idée clé | Lab |
| --- | --- | --- | --- |
| 3.1 | A01 Broken Access Control | IDOR, élévation horizontale/verticale | changer un `id` dans une requête |
| 3.2 | A02 Cryptographic Failures | stockage, transport, hachage faible | casser un MD5 salé/non salé |
| 3.3 | A03 Injection | SQLi, NoSQL, commande, template | SQLi union + aveugle |
| 3.4 | A04 Insecure Design | absence de contrôle métier | contourner une limite d'usage |
| 3.5 | A05 Security Misconfiguration | en-têtes, CORS, debug, backups | `.git/` exposé |
| 3.6 | A06 Vulnerable Components | dépendances obsolètes | `npm audit`, CVE connue |
| 3.7 | A07 Auth Failures | brute force, session, MFA | attaque par dictionnaire |
| 3.8 | A08 Data Integrity Failures | désérialisation, CI/CD | JWT `alg:none` |
| 3.9 | A09 Logging Failures | détection, journalisation | logs manquants sur une attaque |
| 3.10 | A10 SSRF | requêtes serveur forgées | SSRF vers métadonnées internes |

## Méthode d'audit

1. Cartographier : endpoints, rôles, paramètres, cookies.
2. Tester chaque entrée : injection, contrôle d'accès, logique.
3. Prouver : capture de la requête et de la réponse.
4. Corriger : patch + règle de détection.

## Outils

`Burp Suite` · `ffuf` · `sqlmap` · `nuclei` · `jwt_tool` · `OWASP ZAP`

## Ressources

- [OWASP Top 10](https://owasp.org/Top10/)
- PortSwigger Web Security Academy (labs gratuits)
- Dépôt `OWAPS-Top10`

## Notes

> Pour chaque faille : payload minimal, preuve, impact, remédiation, et la requête HTTP brute
> dans un bloc de code.
