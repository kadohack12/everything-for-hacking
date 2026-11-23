# TryHackMe

Retour à l'[index des writeups](../README.md)

Rooms suivies sur [TryHackMe](https://tryhackme.com/), classées dans `Rooms/<NomRoom>/`.

## Rooms publiées

<!-- INDEX:START -->

| Room | Thème | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| panda (KoTH) | Room | Medium | [kadohack12](https://github.com/kadohack12) | 2026-11-22 | [Writeup](Rooms/panda/) |
| Daily Bugle | Room | — | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Rooms/daily-bugle/) |
| Pickle Rick | Room | — | [Alexis Dubus](https://github.com/breaching) | 2026-11-20 | [Writeup](Rooms/pickle-rick/) |

<!-- INDEX:END -->

## Crédits

Les writeups de **Daily Bugle** et **Pickle Rick** viennent du dépôt
[breaching/ctf-writeups](https://github.com/breaching/ctf-writeups), publié sous licence **MIT**
(© 2026 Alexis Dubus). Seul le frontmatter de ce dépôt a été ajouté, et les captures déplacées
dans les `assets/` des rooms.

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
