# Autres plateformes et CTFs

Retour à l'[index des writeups](../README.md) · [Comment contribuer](../../CONTRIBUTING.md)

Writeups de challenges qui ne dépendent pas des trois plateformes principales
([Hack The Box](../hackthebox/), [TryHackMe](../tryhackme/), [Hackropole](../hackropole.fr/)) :
plateformes d'apprentissage, CTFs archivés, environnements vulnérables à installer soi-même.

Chaque writeup vit dans `autres/<plateforme-ou-ctf>/<nom-du-challenge>/`, avec son `README.md`
et ses captures dans `assets/`.

## ⚠️ Ce qui est accepté, ce qui est refusé

| Bienvenu | Refusé |
| --- | --- |
| PicoCTF | **Tout CTF encore en cours** |
| PortSwigger Web Security Academy | Toute plateforme qui **interdit la publication** de solutions |
| OverTheWire (Bandit, Natas, Leviathan…) | Root-Me (ses règles interdisent la publication de solutions) |
| VulnHub | Flags d'épreuves encore ouvertes |
| CTFs archivés : 404CTF, épreuves terminées de CTFtime… | Cibles réelles, contenu illégal |

Deux règles, et elles suffisent :

1. **L'épreuve doit être terminée.** Un CTF en cours, c'est du spoil pour les joueurs qui planchent
   encore — même si le challenge est public.
2. **Les règles de la plateforme priment.** Si elle interdit la publication de solutions
   (Root-Me), le writeup n'a pas sa place ici, même après la clôture de l'épreuve.

Un doute sur un cas limite ? Ouvre une issue **Suggérer un writeup ou un cours** avant de rédiger,
plutôt que de découvrir le refus en review.

## Challenges publiés

<!-- INDEX:START -->

| Plateforme / CTF | Challenge | Catégorie | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |  |

<!-- INDEX:END -->

## Ajouter un writeup

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # choisir « autres », puis le nom de la plateforme
```

Ou à la main :

```bash
cp -r writeups/_template writeups/autres/picoctf/nom-du-challenge
$EDITOR writeups/autres/picoctf/nom-du-challenge/README.md
python3 scripts/update_index.py
```

Le dossier de plateforme est en kebab-case minuscule (`picoctf`, `portswigger`, `404ctf-2025`),
mais le champ `platform` du frontmatter porte le **vrai nom** (`PicoCTF`, `PortSwigger`,
`404CTF 2025`) : c'est lui qui s'affiche dans la colonne « Plateforme / CTF ».

Renseigne aussi `category` (`web`, `crypto`, `reverse`, `pwn`, `forensics`, `misc`…) et
`difficulty` : ce sont les colonnes qui permettent de retrouver un writeup dans l'index.
