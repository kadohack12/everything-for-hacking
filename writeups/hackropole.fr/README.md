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

```bash
cp -r ../../_template Challenges/crypto/NomChallenge
```

Nommage : `Challenges/<catégorie>/<nom-du-challenge>/`. Le champ `platform` du frontmatter vaut
`"Hackropole"` et `category` la catégorie du challenge.
