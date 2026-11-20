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
| À l'aise | crypto | 2022 | [Kadohack12](https://github.com/kadohack12) | 2026-11-20 | [Writeup](Challenges/crypto/a-laise/) |

<!-- INDEX:END -->

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
