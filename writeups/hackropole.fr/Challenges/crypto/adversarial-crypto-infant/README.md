---
title: "AdveRSArial Crypto (Infant)"
platform: "Hackropole"
category: "crypto"
edition: "2024"
difficulty: "Intro"
date: 2026-11-20
author: "Kadohack12"
author_github: "kadohack12"
tags: [rsa, nombre-premier, indicatrice-euler, fcsc2024]
status: published
source: "https://hackropole.fr/fr/challenges/crypto/fcsc2024-crypto-adversarial-crypto-1/"
---

# AdveRSArial Crypto (Infant) — Hackropole (FCSC 2024, crypto, Intro)

> **TL;DR** — le module `n` est un **nombre premier**. Donc `φ(n) = n - 1`, la clé privée se calcule
> directement et il n'y a aucune factorisation à faire. Le piège n'est pas cryptographique, il est
> dans la génération des paramètres.

## Énoncé

> Je viens de suivre un cours sur RSA mais je crois que j'ai oublié quelque chose. Il me semble que
> le prof parlait de deux trucs, mais je ne sais plus exactement quoi. Vous pouvez m'aider ?

Deux fichiers, avec les empreintes affichées par Hackropole (utiles pour vérifier qu'on travaille
sur les bons fichiers) :

| Fichier | Taille | SHA-256 |
| --- | --- | --- |
| `adversarial-crypto-infant.py` | 243 o | `c04cc880…c3ad29` |
| `output.txt` | 1,22 Kio | `44dd99c0…7a7e4090` |

## 1. Lecture du script

```python
from Crypto.Util.number import getStrongPrime, bytes_to_long, long_to_bytes

n = getStrongPrime(2048)
e = 2 ** 16 + 1

flag = bytes_to_long(open("flag.txt", "rb").read())
c = pow(flag, e, n)

print(f"{n = }")
print(f"{e = }")
print(f"{c = }")
```

« Le prof parlait de deux trucs » : ce sont `p` et `q`. Le script n'en produit **qu'un seul**.
`getStrongPrime(2048)` renvoie un unique nombre premier de 2048 bits, affecté directement à `n` :
il n'y a jamais de multiplication, donc jamais de module RSA.

C'est exactement le genre d'erreur qu'on ne voit pas en lisant le chiffrement : `pow(flag, e, n)`
est un RSA parfaitement correct. Tout se joue une ligne plus haut.

## 2. Pourquoi c'est cassé

| | RSA correct | Ce challenge |
| --- | --- | --- |
| module | `n = p * q` | `n` premier |
| indicatrice d'Euler | `φ(n) = (p-1)(q-1)` | `φ(n) = n - 1` |
| clé privée | `d = e⁻¹ mod φ(n)` | idem, mais `φ(n)` est connu d'avance |
| travail de l'attaquant | factoriser `n` | aucun |

Pour un nombre premier `p`, tous les entiers de `1` à `p-1` sont premiers avec `p`, donc
`φ(p) = p - 1`. Ici `n` joue le rôle de `p` : `φ(n)` tombe du ciel, sans factorisation.

La leçon du challenge : la solidité de RSA ne vient pas de la taille de `n`, mais du fait que
**factoriser `n` soit difficile**. Un module premier est le pire cas possible — et il reste
indétectable à l'œil nu : `n` fait bien 2048 bits, `e` vaut 65537, `c` est cohérent.

## 3. Exploitation

```python
import re

vals = dict(re.findall(r"^(\w+) = (\d+)$", open("output.txt").read(), re.M))
n, e, c = int(vals["n"]), int(vals["e"]), int(vals["c"])

d = pow(e, -1, n - 1)                 # φ(n) = n - 1 : aucune factorisation
m = pow(c, d, n)
print(m.to_bytes((m.bit_length() + 7) // 8, "big").decode())
```

`pow(e, -1, phi)` (inverse modulaire) demande Python ≥ 3.8. Sur une version plus ancienne,
l'algorithme d'Euclide étendu donne le même `d` — attention, `pow(e, phi - 2, phi)` ne marche pas
ici : `φ(n)` n'est pas premier.

Contrôle de la prémisse, une seconde de calcul :

```python
from Crypto.Util.number import isPrime
print(isPrime(n))     # True
```

Sans dépendance, un Miller-Rabin sur quelques bases suffit : le test n'est jamais le point
difficile, encore faut-il penser à le faire.

### Variante `p = q = n`

Plusieurs solutions publiées sur Hackropole (maxbekh, brf-f, guillp…) arrivent au même résultat en
posant `p = q = n`, ce qui donne `φ(n) = (n-1)²`. Ça fonctionne parce que `(n-1)²` est un multiple
de l'ordre du groupe multiplicatif : il suffit que `e·d ≡ 1 mod (n-1)`. Vérifié localement, les deux
variantes produisent le même clair.

## 4. Résultat

```text
FCSC{...}
```

Le flag est volontairement tronqué : ce dépôt n'héberge pas les flags en clair, pour ne pas
apparaître dans les dumps de flags ni spoiler les épreuves encore ouvertes. Il commence par
`d0bf` et fait 70 caractères — le déchiffrement ci-dessus le redonne intégralement.

<details>
<summary>output.txt fourni par le challenge (pour reproduire sans télécharger)</summary>

```text
n = 22914764349697556963541692665721076425490063991574936243571428156261302060328685591556514036751777776065771167330244010708082147401402002914377904950080486799957005111360365028092884367373338454223568447811216200859660057226322801828334633020895296785582519610777820724907394060126570265818769159991752144783469338557691407102432786644694590118176582000965124360500257946304028767088296724907062561163478654995994205065812479605136088813543435895840276066683243706020091519857275219422246006137390619897086478975872204136389082598585864385077220265194919486850918633328368814287347732293510186569121425821644289329813
e = 65537
c = 11189917160698738647911433493693285101538131455035611550077950709107429331298329502327358588774261161674422351739941120882289954400477590502272629693853242116507000433761914368814656180874783594812260498542390500221519883099478550863172147588922341571443502449435143090576514228274833316274013491937919397957017546671325357027765817692571583998487352090789855980131184451611087822399088669705683765370510052781742383736278295296012267794429263720509724794426552010741678342838319060084074826713065120930332229122961216786019982413982114571551833129932338204333681414465713448112309599140515483842800125894387412148599
```

</details>

## 5. Ce que je retiens

- **Premier réflexe** devant un triplet `(n, e, c)` : tester la primalité de `n`. C'est une ligne,
  et ça élimine d'un coup toute une famille de challenges « RSA cassé ».
- **Lire la génération des clés, pas seulement le chiffrement.** Un RSA correct sur un module
  invalide reste un module invalide.
- `getStrongPrime` est un générateur de nombre premier, pas un générateur de module RSA. Le nom
  trompe (« strong prime » ne veut pas dire « bon module »).
- **Les variantes équivalentes** sont une bonne manière de vérifier qu'on a compris : si deux
  chemins donnent le même clair, l'analyse tient.
- Un `e = 65537` et un `n` de 2048 bits ne garantissent rien : ce sont les *relations* entre les
  paramètres qui comptent.

## Références

- [Épreuve sur Hackropole](https://hackropole.fr/fr/challenges/crypto/fcsc2024-crypto-adversarial-crypto-1/)
- RFC 8017 (PKCS #1 v2.2), § 3 : définition de la génération de clés RSA
- Indicatrice d'Euler : `φ(p) = p - 1` pour `p` premier
