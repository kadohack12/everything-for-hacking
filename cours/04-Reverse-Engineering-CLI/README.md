# 04 — Reverse Engineering en ligne de commande

[← Programme](../README.md)

## Objectifs

À la fin du module, je dois pouvoir **comprendre un binaire que je n'ai pas écrit, sans jamais
ouvrir d'interface graphique** : le trier sans l'exécuter, lire sa structure ELF à la main, suivre
sa logique d'assemblage en assemblant, et retrouver la valeur qui débloque un crackme — le tout
depuis un terminal, y compris à travers une session SSH sans affichage.

Concrètement, je dois être capable de :

- **trier** un fichier inconnu (type réel, architecture, packer, chaînes lisibles) avant toute
  exécution, et justifier pourquoi je ne l'ai pas lancé ;
- **lire un ELF** : en-tête, segments, sections, symboles, dépendances dynamiques, et dire ce que
  chaque zone signifie pour le reverse ;
- **lire de l'assembleur x86-64** au niveau nécessaire : appels de fonction, comparaisons,
  boucles, accès mémoire, conventions d'appel ;
- **désassembler et naviguer** dans un binaire en CLI (radare2/rizin, `objdump`), poser des
  commentaires, renommer, suivre les renvois ;
- **exécuter sous contrôle** (`gdb`, `strace`, `ltrace`) pour observer la vérification au moment
  où elle se produit, poser des points d'arrêt et modifier l'état ;
- **décompiler en CLI** et **patcher** un binaire (`r2`, `objcopy`, `dd`) pour court-circuiter un
  test, ou résoudre un problème par solveur (`z3`) quand la vérification est arithmétique ;
- **reconnaître les défenses** : anti-debug, binaires strippés, code obfusqué, packing, et savoir
  quelle technique employer pour chacune ;
- **écrire un writeup reproductible** : commandes exactes, sorties, raisonnement, et la preuve
  que la solution fonctionne.

Le fil rouge est un **crackme** : un binaire qui demande un mot de passe et refuse tout le reste.
Chaque chapitre ajoute une couche d'outillage et de raisonnement sur le même objet.

> **Périmètre.** Le module couvre le reverse *défensif et pédagogique* : mes propres binaires, des
> crackmes d'entraînement, des challenges CTF terminés. Pas de contournement de licence, pas
> d'analyse de binaire trouvé sur une machine qui ne m'appartient pas. Les techniques sont les
> mêmes que celles d'un analyste malware — c'est justement pour ça qu'elles s'apprennent dans un
> lab isolé.

## Prérequis

- **Linux x86-64** (Debian/Ubuntu, ou Arch). Les exemples sont testés sur Debian ; les écarts
  Arch sont signalés.
- Savoir **compiler un programme C** : `gcc -o hello hello.c` ne doit pas être une découverte.
- Lire du C simple (pointeurs, tableaux, `if`, boucles) et compter en hexadécimal.
- Notions de binaire : octet, mot de 64 bits, complément à deux, little-endian.
- **Aucune interface graphique requise.** Tout doit fonctionner en SSH pur, sans X11 : c'est le
  critère de validation de chaque chapitre.

Un dossier de travail jetable, jamais mélangé avec le reste :

```bash
mkdir -p ~/rev-lab && cd ~/rev-lab
```

Et une règle d'hygiène : les binaires inconnus s'exécutent dans une **VM ou un conteneur**, jamais
sur la machine de travail (chapitre 4.1).

## Boîte à outils CLI

Tout est en ligne de commande, installable en une passe. Les outils graphiques (Ghidra GUI, IDA,
Binary Ninja, Cutter) sont **hors périmètre** : ils sont excellents, mais ils ne passent pas en SSH.

### Debian / Ubuntu

```bash
sudo apt update
sudo apt install -y \
    binutils file xxd strace ltrace gdb upx-ucl binwalk patchelf \
    python3-pip

# xxd vient du paquet « xxd » (Debian 12+) ; sur les versions plus anciennes :
# sudo apt install -y vim-common

# z3 (solveur SMT), pwntools (checksec, ROP, tubes), capstone (désassembleur Python)
python3 -m pip install --user z3-solver pwntools capstone
```

### Arch

```bash
sudo pacman -S --needed binutils file xxd strace ltrace gdb upx binwalk patchelf \
    python-z3 python-pwntools python-capstone radare2 rizin
```

### Débogueur amélioré : pwndbg ou gef

`gdb` nu est utilisable, mais ces deux extensions affichent registres, pile, sections et
désassemblage à chaque arrêt — c'est ce qui rend le débogage en CLI supportable.

```bash
# pwndbg
git clone https://github.com/pwndbg/pwndbg ~/tools/pwndbg
cd ~/tools/pwndbg && ./setup.sh

# ou gef (plus léger)
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"
```

Vérification : `gdb -q ./binaire` puis `pwndbg` ou `gef` doit répondre à `help`.

### radare2 / rizin

Les paquets des distributions sont souvent anciens ; la compilation est rapide et évite les
incompatibilités de commandes.

```bash
# radare2
git clone --depth 1 https://github.com/radareorg/radare2 ~/tools/radare2
~/tools/radare2/sys/install.sh

# rizin (fork de r2, mêmes commandes à 90 %)
sudo apt install -y rizin        # ou : git clone https://github.com/rizinorg/rizin
```

### Récapitulatif

| Outil | Paquet | À quoi il sert dans ce module |
| --- | --- | --- |
| `file`, `sha256sum` | `file`, `coreutils` | identifier et empreindre un échantillon (4.1) |
| `strings`, `nm`, `objdump`, `readelf`, `objcopy`, `strip` | `binutils` | statique : chaînes, symboles, sections, patch (4.1, 4.2, 4.6) |
| `xxd`, `hexdump` | `xxd` / `util-linux` | hexadécimal, magic bytes, patch à l'octet (4.1, 4.6) |
| `binwalk` | `binwalk` | fichiers embarqués, entropie, détection de packer (4.1) |
| `upx` | `upx-ucl` | tester et décompresser un UPX (4.1, 4.7) |
| `strace`, `ltrace` | `strace`, `ltrace` | appels système et appels de bibliothèque (4.5) |
| `gdb` + `pwndbg`/`gef` | `gdb` + dépôt | points d'arrêt, registres, mémoire, patch en mémoire (4.5) |
| `radare2` / `rizin` | dépôt / `rizin` | désassemblage, graphe, émulation, décompilation (4.4, 4.6) |
| `z3` | `python3-z3` / `z3-solver` | résoudre les vérifications arithmétiques (4.6) |
| `patchelf` | `patchelf` | changer l'interpréteur ou les `NEEDED` (4.7) |

## Plan

| # | Chapitre | Contenu clé | Lab |
| --- | --- | --- | --- |
| 4.1 | [Triage et analyse statique de base](01-triage-et-analyse-statique.md) | `file`, `strings`, `xxd`, `binwalk`, `upx` — ne pas exécuter | trier un binaire et trouver une chaîne cachée |
| 4.2 | [Anatomie ELF et inspection des symboles](02-anatomie-elf-et-symboles.md) | en-tête, segments, sections, `nm`, stripped vs statique | comparer 3 compilations du même code |
| 4.3 | Assembleur x86-64 appliqué au reverse | registres, conventions d'appel, comparaisons, boucles | lire la fonction `check` à la main |
| 4.4 | Désassemblage et graphe en CLI | `r2`/`rizin`, `afl`, `pdf`, `VV`, renommage, xrefs | cartographier un crackme dans r2 |
| 4.5 | [Analyse dynamique et débogage CLI](05-analyse-dynamique-gdb-strace.md) | `strace`, `ltrace`, `gdb` en `-batch`, watchpoints, PIE, patch en mémoire | retrouver le mot de passe en mémoire |
| 4.6 | [Décompilation, patching et solveurs](06-decompilation-cli-patching-z3.md) | `pdc`/`pdg`, `r2 -w`, `patchelf`, `r2pipe`, `z3`, `angr` | patcher un test et résoudre par z3 |
| 4.7 | Anti-debug, binaires strippés et obfuscation | `ptrace`, `LD_PRELOAD`, packing, code mort, string encryption | désosser un binaire qui se défend |
| 4.8 | Méthodologie complète et autres formats CLI | PE, Mach-O, .NET, Python compilé, firmware, arbre de décision | crackme complet de bout en bout |

## Fiches de chapitre

Fiches détaillées, une par chapitre. Elles suivent toutes le même plan : objectifs, théorie courte,
commandes réelles, tableau de synthèse, pièges, exercice corrigé.

| Chapitre | Fiche | État |
| --- | --- | --- |
| 4.1 Triage et analyse statique | [01 — Triage et analyse statique](01-triage-et-analyse-statique.md) | rédigée |
| 4.2 Anatomie ELF et symboles | [02 — Anatomie ELF et symboles](02-anatomie-elf-et-symboles.md) | rédigée |
| 4.3 Assembleur x86-64 | [03 — Assembleur x86-64](03-assembleur-x86-64.md) | rédigée |
| 4.4 Désassemblage et graphe en CLI | [04 — Désassemblage radare2 / rizin](04-desassemblage-radare2-rizin.md) | rédigée |
| 4.5 Analyse dynamique et débogage | [05 — Analyse dynamique : strace, ltrace, gdb](05-analyse-dynamique-gdb-strace.md) | rédigée |
| 4.6 Décompilation, patching, solveurs | [06 — Décompilation, patching et solveurs](06-decompilation-cli-patching-z3.md) | rédigée |
| 4.7 Anti-analyse et obfuscation | — | à venir |
| 4.8 Méthodologie et autres formats | — | à venir |

## Labs récapitulatifs

- **Lab A — le crackme muet.** Un binaire sans symboles qui compare une entrée à une valeur
  construite à l'exécution. Objectif : retrouver la valeur sans jamais lancer `strings` avec
  succès, en combinant 4.2, 4.3 et 4.5.
- **Lab B — le binaire qui se défend.** Anti-debug (`ptrace`), code mort, chaînes chiffrées.
  Objectif : le contourner proprement et documenter chaque parade (4.7).
- **Lab C — le format inconnu.** Un exécutable Windows ou un script Python compilé. Objectif :
  appliquer la même méthodologie de triage et trouver l'outil CLI adapté (4.8).

## Outils

`file` · `strings` · `xxd` · `readelf` · `objdump` · `nm` · `binwalk` · `upx` · `strace` ·
`ltrace` · `gdb` (+ `pwndbg`/`gef`) · `radare2`/`rizin` (+ `pdc`/`pdg`) · `patchelf` ·
`r2pipe` · `z3` · `angr`

## Ressources

- [Intel SDM, volume 2](https://www.intel.com/sdm) — jeu d'instructions x86-64, la référence.
- [felixcloutier.com/x86](https://www.felixcloutier.com/x86/) — la même chose, en HTML navigable.
- [System V ABI x86-64](https://gitlab.com/x86-psABIs/x86-64-ABI) — conventions d'appel, registres.
- [radare2 book](https://book.radare.org/) — référence des commandes `r2`.
- [crackmes.one](https://crackmes.one/) — exercices légaux, classés par difficulté.

## Notes

> Un fichier par chapitre : `NN-nom-du-chapitre.md` (ex. `01-triage-et-analyse-statique.md`).
> Toute nouvelle fiche doit être ajoutée au tableau « Fiches de chapitre » ci-dessus.
>
> **Aucun binaire ni source compilée dans `cours/`.** Les programmes d'exercice sont donnés en
> bloc Markdown avec la commande `gcc` : le lecteur les compile lui-même dans son dossier de
> travail. C'est aussi une protection — un dépôt public qui héberge des exécutables finit par
> héberger autre chose.
>
> Après modification de `cours/`, régénérer l'empreinte : `python3 scripts/check_cours.py --update`.
