# Hack The Box

Retour à l'[index des writeups](../README.md)

Machines résolues sur [Hack The Box](https://www.hackthebox.com/), classées dans `Machines/<NomMachine>/`.

## Machines publiées

<!-- INDEX:START -->

| Machine | OS | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |

<!-- INDEX:END -->

## Ajouter une machine

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # assistant : pose les questions et crée le dossier
```

Ou à la main :

```bash
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
$EDITOR writeups/hackthebox/Machines/nom-machine/README.md
python3 scripts/update_index.py
```

Chaque dossier contient le writeup (`README.md`) et ses captures (`assets/`).
La machine n'apparaît ci-dessus qu'une fois son frontmatter passé en `status: published`.
