# Hackropole (FCSC)

Retour à l'[index des writeups](../README.md)

Challenges de [hackropole.fr](https://hackropole.fr/), la plateforme d'entraînement du
**France Cybersecurity Challenge (FCSC)**, classés par catégorie :

| Dossier | Catégorie |
| --- | --- |
| [`Challenges/crypto/`](Challenges/crypto/) | Cryptographie |
| [`Challenges/web/`](Challenges/web/) | Web |
| [`Challenges/reverse/`](Challenges/reverse/) | Reverse engineering |
| [`Challenges/pwn/`](Challenges/pwn/) | Exploitation binaire |
| [`Challenges/forensics/`](Challenges/forensics/) | Forensic |
| [`Challenges/hardware/`](Challenges/hardware/) | Hardware |
| [`Challenges/misc/`](Challenges/misc/) | Divers |

## Challenges publiés

<!-- INDEX:START -->

| Challenge | Catégorie | Édition | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| AdveRSArial Crypto (Infant) | crypto | 2024 | [Kadohack12](https://github.com/kadohack12) | 2026-11-20 | [Writeup](Challenges/crypto/adversarial-crypto-infant/) |
| Bubulle Corp (1/2) | web | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/web/bubulle-corp-2026/) |
| Extensif | reverse | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/reverse/extensif-2026/) |
| Forenzeek — compromission initiale | forensics | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/forensics/forenzeek-compromission-2026/) |
| Forenzeek — latéralisation | forensics | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/forensics/forenzeek-lateralisation-2026/) |
| Grhelp — connect back | forensics | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/forensics/grhelp-connectback-2026/) |
| Grhelp — exfiltration | forensics | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/forensics/grhelp-exfiltration-2026/) |
| RemoBLE Control | hardware | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/hardware/remoble-control-2026/) |
| This is fine | crypto | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/crypto/this-is-fine-2026/) |
| Tortoise Say | hardware | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/hardware/tortoise-say-2026/) |
| Web Logs | forensics | 2026 | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Challenges/forensics/web-logs-2026/) |
| À l'aise | crypto | 2022 | [Kadohack12](https://github.com/kadohack12) | 2026-11-20 | [Writeup](Challenges/crypto/a-laise/) |

<!-- INDEX:END -->

## Crédits

Les 10 writeups du **FCSC 2026** viennent du dépôt
[breaching/ctf-writeups](https://github.com/breaching/ctf-writeups), publié sous licence **MIT**
(© 2026 Alexis Dubus).

**Modifications apportées** : ajout du frontmatter de ce dépôt et troncature des flags FCSC
(`FCSC{…}`), la CI refusant les flags en clair. Le raisonnement et les commandes sont intacts.

## Ajouter un challenge

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # assistant : pose les questions et crée le dossier
```

Ou à la main :

```bash
cp -r writeups/_template writeups/hackropole.fr/Challenges/crypto/nom-challenge
$EDITOR writeups/hackropole.fr/Challenges/crypto/nom-challenge/README.md
python3 scripts/update_index.py
```

Nommage : `Challenges/<catégorie>/<nom-du-challenge>/`. Le champ `platform` du frontmatter vaut
`"Hackropole"`, `category` la catégorie du challenge et `edition` l'édition du FCSC (`2024`, `2025`…).
