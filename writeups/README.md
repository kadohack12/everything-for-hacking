# Writeups

Retour à l'[accueil](../README.md) · Voir les [cours](../cours/README.md)

Solutions détaillées, étape par étape : reconnaissance, exploitation, élévation de privilèges, leçons.
L'objectif n'est pas de donner le flag mais de montrer **le raisonnement** et les impasses.

## Index

> Ces tableaux sont **générés automatiquement** par [`scripts/update_index.py`](../scripts/update_index.py)
> à partir du frontmatter de chaque writeup : seuls les `status: published` apparaissent.
> Ne pas les éditer à la main — ajouter le writeup, puis lancer `python3 scripts/update_index.py`.

### Hack The Box — Machines

<!-- INDEX:START:hackthebox -->

| Machine | OS | Difficulté | Date | Writeup |
| --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |

<!-- INDEX:END:hackthebox -->

### TryHackMe — Rooms

<!-- INDEX:START:tryhackme -->

| Room | Thème | Difficulté | Date | Writeup |
| --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |

<!-- INDEX:END:tryhackme -->

### Hackropole (FCSC) — Challenges

<!-- INDEX:START:hackropole.fr -->

| Challenge | Catégorie | Édition | Date | Writeup |
| --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |

<!-- INDEX:END:hackropole.fr -->

## Comment est organisé un writeup

```text
Plateforme/Machines/NomMachine/
├── README.md      # le writeup complet
└── assets/        # 01-nmap.png, 02-exploit.png, 03-flag.png…
```

Le `README.md` suit le modèle [`_template/README.md`](_template/README.md) :

1. **En-tête YAML** — métadonnées (plateforme, OS, difficulté, tags, statut).
2. **TL;DR** — le chemin d'attaque en 3 lignes.
3. **Reconnaissance** — scan réseau, services, versions.
4. **Énumération** — web, SMB, DNS… et ce qu'on en déduit.
5. **Accès initial** — la faille, le payload, la preuve.
6. **Élévation de privilèges** — énumération locale, vecteur, exploitation.
7. **Flags** — `user.txt` / `root.txt` (tronqués).
8. **Leçons** — ce que je referais, ce que j'ai appris.

## Créer un nouveau writeup

```bash
cp -r _template hackthebox/Machines/NomMachine
python3 ../scripts/update_index.py      # depuis writeups/, ou depuis la racine : python3 scripts/update_index.py
```

Puis renommer les captures dans `assets/` et compléter le `README.md`.
Le frontmatter démarre en `status: draft` : l'index ne l'affiche qu'une fois passé en `published`.

## Règles

- **Pas de spoiler gratuit** : le TL;DR reste vague, les flags sont tronqués.
- **Reproductibilité** : les commandes sont complètes et copiables.
- **Honnêteté** : les indices, les erreurs et les chemins abandonnés sont mentionnés.
- **Pas de contenu illégal** : uniquement des cibles autorisées (labs, plateformes d'entraînement).
- **`draft` tant que la machine est active** : la CI refuse un `status: draft` sur `main`.
- **Aucun flag en clair** : la CI bloque `HTB{…}`, `THM{…}`, `FCSC{…}`, `CTF{…}` et les clés privées.
