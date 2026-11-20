# Writeups

Retour à l'[accueil](../README.md) · Voir les [cours](../cours/README.md)

Solutions détaillées, étape par étape : reconnaissance, exploitation, élévation de privilèges, leçons.
L'objectif n'est pas de donner le flag mais de montrer **le raisonnement** et les impasses.

## Index

### Hack The Box — Machines

| Machine | OS | Difficulté | Techniques clés | Statut |
| --- | --- | --- | --- | --- |
| _à venir_ | | | | |

### TryHackMe — Rooms

| Room | Thème | Difficulté | Statut |
| --- | --- | --- | --- |
| _à venir_ | | | |

### Hackropole (FCSC) — Challenges

| Challenge | Catégorie | Édition | Statut |
| --- | --- | --- | --- |
| _à venir_ | | | |

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
```

Puis renommer les captures dans `assets/` et compléter le `README.md`.
Ne pas oublier d'ajouter la ligne dans le tableau ci-dessus.

## Règles

- **Pas de spoiler gratuit** : le TL;DR reste vague, les flags sont tronqués.
- **Reproductibilité** : les commandes sont complètes et copiables.
- **Honnêteté** : les indices, les erreurs et les chemins abandonnés sont mentionnés.
- **Pas de contenu illégal** : uniquement des cibles autorisées (labs, plateformes d'entraînement).
