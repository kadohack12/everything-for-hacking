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

| Challenge | Catégorie | Édition | Date | Writeup |
| --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |

<!-- INDEX:END -->

## Ajouter un challenge

```bash
cp -r ../../_template Challenges/crypto/NomChallenge
python3 ../../../scripts/update_index.py
```

Nommage : `Challenges/<catégorie>/<nom-du-challenge>/`. Le champ `platform` du frontmatter vaut
`"Hackropole"`, `category` la catégorie du challenge et `edition` l'édition du FCSC (`2024`, `2025`…).
