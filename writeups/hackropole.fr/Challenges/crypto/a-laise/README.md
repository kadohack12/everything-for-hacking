---
title: "À l'aise"
platform: "Hackropole"
category: "crypto"
edition: "2022"
difficulty: "Intro"
date: 2026-11-20
author: "Kadohack12"
author_github: "kadohack12"
tags: [vigenere, crypto-symetrique, python, fcsc2022]
status: published
source: "https://hackropole.fr/fr/challenges/crypto/fcsc2022-crypto-a-laise/"
---

# À l'aise — Hackropole (FCSC 2022, crypto, intro)

> **TL;DR** — Chiffre de Vigenère, clé donnée dans l'énoncé : on soustrait `FCSC`
> lettre par lettre et le message apparaît en clair. La ville est **Nantes**.

## Énoncé

> Cette épreuve vous propose de déchiffrer un message chiffré avec la méthode inventée par
> Blaise de Vigénère. La clé est `FCSC` et le message chiffré est :
>
> ```text
> Gqfltwj emgj clgfv ! Aqltj rjqhjsksg ekxuaqs, ua xtwk n'feuguvwb gkwp xwj,
> ujts f'npxkqvjgw nw tjuwcz ugwygjtfkf qz uw efezg sqk gspwonu.
> Jgsfwb-aqmu f Pspygk nj 29 cntnn hqzt dg igtwy fw xtvjg rkkunqf.
> ```
>
> Le flag est le nom de la ville mentionnée dans ce message.

Catégorie : crypto / symétrique · difficulté : intro · auteur : Cryptanalyse · édition : FCSC 2022.

## Analyse

Aucune cryptanalyse à faire : l'algorithme et la clé sont fournis. Deux points d'attention
suffisent à ne pas se tromper.

1. **Le décalage ne s'applique qu'aux lettres.** Les espaces, la ponctuation et les chiffres
   sont recopiés tels quels et **ne consomment pas** de caractère de clé. C'est l'erreur
   classique : en incrémentant l'index de clé à chaque caractère du texte, on obtient du
   charabia dès le premier mot.
2. **Vigenère = soustraction, pas addition.** Chiffrement : `C = P + K`. Déchiffrement :
   `P = C − K`, le tout modulo 26, en repartant de `A`/`a` selon la casse.

La clé `FCSC` se répète sur tout le message : `F`, `C`, `S`, `C`, `F`, `C`, `S`, `C`…

## Déchiffrement

```python
def vigenere_decrypt(ciphertext, key):
    out, key_index = [], 0
    key = key.upper()

    for char in ciphertext:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord("A")
            base = ord("A") if char.isupper() else ord("a")
            out.append(chr((ord(char) - base - shift) % 26 + base))
            key_index += 1
        else:
            out.append(char)  # la ponctuation ne consomme pas de clé

    return "".join(out)


ciphertext = (
    "Gqfltwj emgj clgfv ! Aqltj rjqhjsksg ekxuaqs, ua xtwk n'feuguvwb gkwp xwj, "
    "ujts f'npxkqvjgw nw tjuwcz ugwygjtfkf qz uw efezg sqk gspwonu. "
    "Jgsfwb-aqmu f Pspygk nj 29 cntnn hqzt dg igtwy fw xtvjg rkkunqf."
)

print(vigenere_decrypt(ciphertext, "FCSC"))
```

Sortie brute, conservée dans [`assets/decrypt-output.txt`](assets/decrypt-output.txt) :

```text
Bonjour cher agent ! Votre prochaine mission, si vous l'acceptez bien sur, sera
d'infiltrer le reseau souterrain ou se cache nos ennemis. Rendez-vous a Nantes le
29 avril pour le debut de votre mission.
```

Le texte en clair a été chiffré **sans accents** (l'alphabet de Vigenère est réduit à 26
lettres), d'où `reseau`, `ou`, `debut` : la conversion n'a pas introduit d'erreur. On remet
les accents à la lecture :

> Bonjour cher agent ! Votre prochaine mission, si vous l'acceptez bien sûr, sera d'infiltrer
> le réseau souterrain où se cachent nos ennemis. Rendez-vous à **Nantes** le 29 avril pour le
> début de votre mission.

## Flag

La ville mentionnée est **Nantes** ; le flag est ce nom dans le format FCSC :

```text
FCSC{...}
```

Le flag complet n'est pas recopié ici : il se reconstitue avec la ville ci-dessus.
(Convention du dépôt : aucun flag en clair, pour ne pas apparaître dans les dumps de flags.)

## Leçons

- Une clé fournie transforme un exercice de cryptanalyse en simple exercice d'implémentation :
  le seul risque est l'index de clé mal incrémenté sur les caractères non alphabétiques.
- Vigenère est polyalphabétique, donc immunisé contre l'analyse de fréquence simple — mais
  **pas** contre Kasiski ni l'indice de coïncidence dès que le message est assez long pour la
  longueur de clé (ici 4 caractères, donc très redondant).
- Réflexe utile : écrire le déchiffrement en quelques lignes plutôt que d'ouvrir un outil, ça
  évite les surprises de normalisation (accents, casse, ponctuation).

## Références

- [Épreuve sur Hackropole](https://hackropole.fr/fr/challenges/crypto/fcsc2022-crypto-a-laise/)
- [Chiffre de Vigenère — Wikipédia](https://fr.wikipedia.org/wiki/Chiffre_de_Vigen%C3%A8re)
