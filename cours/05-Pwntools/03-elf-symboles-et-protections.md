# 03 — ELF, symboles et protections

[← Module](README.md)

## Objectif

Lire un binaire avec pwntools et répondre, avant d'écrire une ligne d'exploit : quelles
protections sont actives, quels symboles sont disponibles, où se trouvent le PLT et le GOT.

## checksec en une commande

```bash
pwn checksec ./ret2win
```

```text
[*] 'ret2win'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
```

Chaque ligne se traduit en contrainte concrète :

| Ligne | Ce que ça m'impose |
| --- | --- |
| `No PIE` | les adresses sont fixes : `0x401156` restera `0x401156` |
| `NX enabled` | pas de shellcode sur la pile : il faut du ROP |
| `No canary` | le débordement peut écraser le retour sans détection |
| `Partial RELRO` | la GOT est lisible et partiellement réinscriptible |
| `No` (Stripped) | les noms de fonctions sont dans l'ELF, donc réutilisables |

Le binaire `shellcode` du lab affiche une ligne de plus, qui change tout :

```text
    NX:         NX enabled on new kernels
    Stack:      Executable
    RWX:        Has RWX segments
```

`Stack: Executable` signifie que `-z execstack` a été utilisé : la pile est exécutable, le
shellcode redevient possible.

## Lire les symboles

```python
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
print("win :", hex(elf.symbols["win"]))
print("vuln:", hex(elf.symbols["vuln"]))
print("main:", hex(elf.symbols["main"]))
print("puts@plt:", hex(elf.plt["puts"]))
print("puts@got:", hex(elf.got["puts"]))
```

```text
win : 0x401156
vuln: 0x40118f
main: 0x4011b0
puts@plt: 0x401030
puts@got: 0x404000
```

Trois dictionnaires suffisent pour la majorité des cas :

- `elf.symbols` : les fonctions et variables du binaire (`win`, `vuln`, `main`, `target`).
- `elf.plt` : les stubs de la PLT, utilisés pour **appeler** une fonction de la libc.
- `elf.got` : les entrées de la GOT, utilisées pour **lire l'adresse réelle** d'une fonction.

La distinction PLT/GOT est le cœur du chapitre 07 : `elf.plt["puts"]` sert à appeler `puts`,
`elf.got["puts"]` sert à fuiter l'adresse de `puts` dans la libc.

## Vérifier avec readelf

pwntools peut se tromper si le binaire est exotique. Le contrôle croisé coûte deux secondes :

```bash
readelf -hW ./ret2win | grep -E 'Type:|Machine:'
readelf -sW ./ret2win | grep -E ' win$| vuln$'
```

```text
  Type:                              EXEC (Executable file)
  Machine:                           Advanced Micro Devices X86-64
    22: 000000000040118f    33 FUNC    GLOBAL DEFAULT   13 vuln
    30: 0000000000401156    57 FUNC    GLOBAL DEFAULT   13 win
```

`Type: EXEC` confirme l'absence de PIE. `DYN` indiquerait un binaire à adresses aléatoires, et
tous les offsets devraient alors être calculés à partir d'une fuite.

## Ce que pwntools ne dit pas

`checksec` résume, il n'explique pas. Trois protections ne s'y lisent pas directement :

- **ASLR** est une propriété du noyau, pas du binaire : `cat /proc/sys/kernel/randomize_va_space`
  (`2` = activé). Elle randomise la pile, la libc et le tas.
- **Full RELRO** rend la GOT en lecture seule : un débordement ne peut plus la réécrire, il faut
  passer par une autre cible.
- **CET/IBT** (endbr64, ombres de pile matérielles) peut bloquer le ROP sur les systèmes récents.

## Pièges

| Symptôme | Cause |
| --- | --- |
| `KeyError` sur `elf.symbols["win"]` | binaire strippé : chercher dans `elf.functions` ou par chaîne |
| Adresses qui changent d'un run à l'autre | PIE actif : il faut une fuite, pas une constante |
| `elf.plt["system"]` absent | la fonction n'est jamais appelée par le binaire : la PLT n'existe pas |
| `NX enabled` alors qu'on veut du shellcode | recompiler avec `-z execstack` (lab uniquement) |

## À retenir

- `pwn checksec` d'abord, toujours : il décide de la stratégie.
- `elf.symbols` pour les fonctions du binaire, `elf.plt` pour appeler, `elf.got` pour fuiter.
- `Type: EXEC` = adresses fixes ; `DYN` = tout se calcule à partir d'une fuite.
- ASLR est côté noyau : le binaire peut être non-PIE et la libc randomisée.
