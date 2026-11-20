# Writeups

Retour à l'[accueil](../README.md) · Voir les [cours](../cours/README.md) ·
[Comment contribuer](../CONTRIBUTING.md)

Solutions détaillées, étape par étape : reconnaissance, exploitation, élévation de privilèges, leçons.
L'objectif n'est pas de donner le flag mais de montrer **le raisonnement** et les impasses.

Ce dossier est **ouvert aux contributions** : chaque writeup publié apparaît dans les tableaux
ci-dessous avec son auteur.

## Index

> Ces tableaux sont **générés automatiquement** par [`scripts/update_index.py`](../scripts/update_index.py)
> à partir du frontmatter de chaque writeup : seuls les `status: published` apparaissent.
> Ne pas les éditer à la main — ajouter le writeup, puis lancer `python3 scripts/update_index.py`.

### Hack The Box — Machines

<!-- INDEX:START:hackthebox -->

| Machine | OS | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |

<!-- INDEX:END:hackthebox -->

### TryHackMe — Rooms

<!-- INDEX:START:tryhackme -->

| Room | Thème | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| _aucun writeup publié pour le moment_ |  |  |  |  |  |

<!-- INDEX:END:tryhackme -->

### Hackropole (FCSC) — Challenges

<!-- INDEX:START:hackropole.fr -->

| Challenge | Catégorie | Édition | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- |
| AdveRSArial Crypto (Infant) | crypto | 2024 | [Kadohack12](https://github.com/kadohack12) | 2026-11-20 | [Writeup](hackropole.fr/Challenges/crypto/adversarial-crypto-infant/) |
| À l'aise | crypto | 2022 | [Kadohack12](https://github.com/kadohack12) | 2026-11-20 | [Writeup](hackropole.fr/Challenges/crypto/a-laise/) |

<!-- INDEX:END:hackropole.fr -->

## Comment est organisé un writeup

```text
<plateforme>/<type>/<nom>/
├── README.md      # le writeup complet
└── assets/        # 01-nmap.png, 02-exploit.png, 03-flag.png…
```

Le `README.md` suit le modèle [`_template/README.md`](_template/README.md) :

1. **En-tête YAML** — métadonnées obligatoires (plateforme, catégorie, difficulté, date, auteur, statut).
2. **TL;DR** — le chemin d'attaque en 3 lignes.
3. **Reconnaissance** — scan réseau, services, versions.
4. **Énumération** — web, SMB, DNS… et ce qu'on en déduit.
5. **Accès initial** — la faille, le payload, la preuve.
6. **Élévation de privilèges** — énumération locale, vecteur, exploitation.
7. **Flags** — `user.txt` / `root.txt` (tronqués).
8. **Leçons** — ce que je referais, ce que j'ai appris.

## Ajouter le tien

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # assistant : questions + frontmatter pré-rempli
```

Ou à la main :

```bash
cp -r writeups/_template writeups/hackthebox/Machines/nom-machine
$EDITOR writeups/hackthebox/Machines/nom-machine/README.md
python3 scripts/update_index.py
```

Le frontmatter démarre en `status: draft` : remplis `author` (et `author_github` si tu veux le
lien vers ton profil), puis passe en `published` quand le writeup est prêt. Détail des champs et
checklist complète : [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Règles

Bloquant (la CI refuse la PR) :

- **Aucun flag en clair** : `FCSC{...}`, `HTB{...}` — jamais la valeur complète.
- **Aucun lien mort** : les images référencées doivent exister dans `assets/`.

Conseillé (la CI le signale, sans bloquer) :

- **Nom de dossier** en kebab-case minuscule (`blue`, `a-laise`), plus simple en URL.
- **Frontmatter complet** (`title`, `platform`, `category`, `difficulty`, `date`, `author`,
  `status`) : c'est lui qui alimente l'index et affiche ton nom.
- **`draft` tant que la machine est active**, `published` ensuite.
- **Pas de spoiler gratuit** : le TL;DR reste vague, les flags sont tronqués.
- **Reproductibilité** : les commandes sont complètes et copiables.
- **Honnêteté** : les indices, les erreurs et les chemins abandonnés sont mentionnés.
- **Pas de contenu illégal** : uniquement des cibles autorisées (labs, plateformes d'entraînement).
