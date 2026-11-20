# TryHackMe

Retour à l'[index des writeups](../README.md)

Rooms suivies sur [TryHackMe](https://tryhackme.com/), classées dans `Rooms/<NomRoom>/`.

## Rooms publiées

<!-- INDEX:START -->

| Room | Thème | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |

<!-- INDEX:END -->

## Ajouter une room

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # assistant : pose les questions et crée le dossier
```

Ou à la main :

```bash
cp -r writeups/_template writeups/tryhackme/Rooms/nom-room
$EDITOR writeups/tryhackme/Rooms/nom-room/README.md
python3 scripts/update_index.py
```

Pour les rooms purement théoriques, le writeup peut se limiter à des notes de cours structurées.
