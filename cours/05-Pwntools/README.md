# 05 — Pwntools : exploitation binaire en pratique

[← Programme](../README.md)

## Objectifs

À la fin du module, je dois pouvoir **écrire un exploit complet, reproductible et lisible** contre
un binaire Linux x86-64, en utilisant pwntools de bout en bout : dialogue avec le processus,
lecture de l'ELF, recherche de gadgets, génération de shellcode, calcul d'offset, chaîne ROP,
fuite d'adresse libc et écriture par format string.

Concrètement, je dois être capable de :

- **piloter un binaire** comme un humain le ferait au clavier, mais par script (`process`,
  `remote`, `sendlineafter`, `recvuntil`), et rendre ce script rejouable en local comme à distance ;
- **lire un ELF avec pwntools** : symboles, PLT, GOT, protections (`checksec`), et savoir ce que
  chaque protection m'interdit ;
- **assembler et désassembler** à la volée (`asm`, `disasm`), générer du shellcode
  (`shellcraft`) et le placer correctement en mémoire ;
- **trouver un offset** de débordement avec `cyclic`, sans tâtonner, et le prouver dans `gdb` ;
- **construire une chaîne ROP** : `ret2win` d'abord, puis `ret2libc` avec fuite d'adresse et calcul
  de la base libc, en gérant l'alignement de pile ;
- **exploiter une format string** avec `fmtstr_payload`, après avoir localisé l'argument fautif ;
- **déboguer un exploit qui ne marche pas** : distinguer un mauvais offset, un gadget absent, un
  problème d'alignement, une protection active ou une fuite mal parsée.

## Plan

| # | Chapitre | Ce que je sais faire après |
| --- | --- | --- |
| 01 | [Installation et contexte](01-installation-et-contexte.md) | Installer pwntools, régler `context`, écrire le squelette d'un exploit |
| 02 | [Tubes : process et remote](02-tubes-process-et-remote.md) | Dialoguer avec un binaire local ou distant, sans race |
| 03 | [ELF, symboles et protections](03-elf-symboles-et-protections.md) | Lire un binaire et dire ce qu'il m'autorise |
| 04 | [Assembleur et shellcode](04-asm-disasm-et-shellcode.md) | Assembler à la volée et exécuter du shellcode |
| 05 | [Cyclic et offsets](05-cyclic-et-offsets.md) | Trouver l'offset exact, et le prouver |
| 06 | [Ret2win](06-ret2win.md) | Détourner l'exécution vers une fonction existante |
| 07 | [Ret2libc](07-ret2libc.md) | Fuiter une adresse, calculer la base, appeler `system` |
| 08 | [Format strings](08-format-strings.md) | Écrire en mémoire avec `%n` |
| 09 | [GDB et debug](09-gdb-et-debug.md) | Observer l'état au bon moment |
| 10 | [Méthode et gabarit](10-methode-et-gabarit.md) | Enchaîner les étapes dans le bon ordre |

## Le binaire de lab

Tous les chapitres utilisent les mêmes quatre binaires, compilés à partir des sources données
dans les chapitres. Ils sont volontairement minimalistes : une seule faille à la fois.

| Binaire | Faille | Protection retirée |
| --- | --- | --- |
| `ret2win` | débordement de pile | canary, PIE |
| `ret2libc` | débordement de pile | canary, PIE |
| `fmt` | format string | — |
| `shellcode` | débordement + pile exécutable | canary, PIE, NX |

```bash
mkdir lab && cd lab
# recopier les sources de chaque chapitre, puis :
gcc -fno-stack-protector -no-pie -o ret2win ret2win.c
gcc -fno-stack-protector -no-pie -o ret2libc ret2libc.c
gcc -fno-stack-protector -no-pie -o fmt fmt.c
gcc -fno-stack-protector -no-pie -z execstack -o shellcode shellcode.c
```

Les avertissements `-Wstringop-overflow` sont attendus : le compilateur signale exactement la
faille qu'on va exploiter.

## Environnement de référence

Les sorties de ce module ont été produites dans cet environnement. Les adresses libc en dépendent :
sur une autre distribution, elles diffèrent, et c'est normal.

| Élément | Version |
| --- | --- |
| Système | Debian 13 (trixie), x86-64 |
| Python | 3.13.5, dans un venv |
| pwntools | 4.15.1 |
| glibc | 2.41 |
| gcc | 14.2.0 |

## Boîte à outils

| Outil | Usage |
| --- | --- |
| `pwn checksec ./bin` | protections d'un binaire |
| `pwn cyclic 200` | motif unique pour trouver un offset |
| `ROPgadget --binary ./bin` | gadgets, en complément de `ROP(elf)` |
| `gdb` | observation, points d'arrêt, registres |
| `socat` | exposer un binaire en TCP pour tester `remote` |
| `readelf -h/-S/-s` | contrôle croisé de ce que pwntools affiche |

## Règle du module

Tous les labs tournent sur **mes propres binaires**, compilés localement. Une cible distante ne
s'exploite qu'avec une autorisation écrite : CTF en cours, plateforme d'entraînement, ou machine
qui m'appartient.

## Pour aller plus loin

- [pwntools-tutorial](https://github.com/Gallopsled/pwntools-tutorial) (MIT) : les chapitres
  officiels, plus détaillés sur `tubes`, `elf` et `rop`. Ce module est une mise en pratique en
  français, avec ses propres labs.
- [ROP Emporium](https://ropemporium.com/) : exercices progressifs de ROP.
- [pwn.college](https://pwn.college/) : programme universitaire complet, gratuit.
