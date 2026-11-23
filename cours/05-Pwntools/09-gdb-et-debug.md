# 09 — GDB et debug

[← Module](README.md)

## Objectif

Observer l'état du programme au moment exact qui compte : registres, pile, code exécuté. Et
savoir brancher gdb sur un processus lancé par pwntools.

## gdb en mode batch

Pour une question ponctuelle, pas besoin de session interactive : `-batch` exécute des commandes
et rend la main.

```bash
gdb -q -batch -ex 'b vuln' -ex 'run < /dev/null' \
    -ex 'info registers rsp rbp' -ex 'x/6gx $rsp' -ex 'x/2i $pc' ./ret2win
```

```text
Breakpoint 1 at 0x401193
Breakpoint 1, 0x0000000000401193 in vuln ()
rsp            0x7fffffffd660      0x7fffffffd660
rbp            0x7fffffffd660      0x7fffffffd660
0x7fffffffd660: 0x00007fffffffd670      0x00000000004011e6
0x7fffffffd670: 0x0000000000000001      0x00007ffff7df4ca8
0x7fffffffd680: 0x00007fffffffd770      0x00000000004011b0
=> 0x401193 <vuln+4>:   sub    $0x40,%rsp
   0x401197 <vuln+8>:   lea    -0x40(%rbp),%rax
```

Ce que ça montre : `rbp` vaut `0x7fffffffd660`, l'adresse de retour vers `main` est à `rbp+8`,
et le tampon sera à `rbp-0x40`. On en déduit l'offset 72 sans exécuter l'exploit.

## Les commandes à connaître

| Commande | Effet |
| --- | --- |
| `b *0x401164` | point d'arrêt sur une adresse |
| `b vuln` | point d'arrêt sur un symbole |
| `run < fichier` | exécute avec une entrée depuis un fichier |
| `info registers rsp rbp rip` | registres |
| `x/6gx $rsp` | six mots de 8 octets en hexadécimal |
| `x/2i $pc` | deux instructions à l'endroit courant |
| `x/s 0x404000` | chaîne à une adresse |
| `p/x $rbp-0x80` | calcul d'adresse |
| `vmmap` | carte mémoire : où est la libc, la pile, le tas |
| `disassemble vuln` | désassemblage d'une fonction |

`vmmap` est la commande la plus sous-estimée : elle donne les plages exactes, et permet de vérifier
si une adresse lue correspond bien à la libc ou à la pile.

## Brancher gdb depuis pwntools

Deux fonctions, deux usages.

`gdb.attach(io)` ouvre une session dans un terminal séparé et attache le processus. Pratique pour
explorer à la main :

```python
io = process("./ret2win")
gdb.attach(io, gdbscript="""
b vuln
c
""")
io.recvuntil(b"Entree :\n")
```

`gdb.debug("./ret2win", gdbscript="...")` lance le binaire **sous** gdb et renvoie un tube : le
script continue de dialoguer normalement, ce qui permet de garder l'exploit automatisé.

```python
io = gdb.debug("./ret2win", gdbscript="b vuln\nc")
```

Les deux exigent un terminal (pas de sortie redirigée) et un `gdb` dans le `PATH`. Dans une session
SSH sans TTY, `gdb.attach` échoue : il reste `gdb -batch` avec des fichiers d'entrée.

## Observer la fuite du chapitre 07

Le point délicat d'un ret2libc est de vérifier que la valeur reçue est bien l'adresse de `puts`.
Dans gdb, au moment du `puts(puts@got)`, on peut comparer :

```bash
gdb -q -batch -ex 'b *0x401030' -ex 'run < /tmp/stage1.bin' \
    -ex 'info registers rdi' -ex 'x/gx $rdi' -ex 'vmmap' ./ret2libc
```

`rdi` doit pointer sur `puts@got` (`0x404000`), et la valeur lue doit tomber dans la plage de la
libc affichée par `vmmap`. Si elle tombe ailleurs, la chaîne ROP est décalée.

## Désactiver l'ASLR

gdb désactive l'ASLR par défaut (`set disable-randomization on`). C'est pratique pour explorer,
dangereux pour conclure : un exploit validé seulement sous gdb peut échouer en dehors, parce que
les adresses réelles diffèrent.

Pour reproduire un environnement sans ASLR en dehors de gdb :

```bash
setarch x86_64 -R ./ret2win
```

Sur un système où `/proc/sys` est inscriptible, `sysctl -w kernel.randomize_va_space=0` fait la
même chose globalement. Dans un conteneur, cette écriture est souvent refusée.

## Pièges

| Symptôme | Cause |
| --- | --- |
| `ptrace: Operation not permitted` | conteneur sans `SYS_PTRACE`, ou `yama/ptrace_scope` restrictif |
| `gdb.attach` sans effet | pas de TTY, ou `context.terminal` non configuré |
| Adresses différentes de l'exploit | ASLR : gdb la coupe, pas le shell |
| `x/s` affiche du binaire illisible | mauvaise adresse : vérifier avec `vmmap` |

## À retenir

- `gdb -batch` répond aux questions ponctuelles sans session interactive.
- `vmmap` dit dans quelle plage on se trouve ; `x/…gx` lit la pile mot par mot.
- `gdb.attach` pour explorer, `gdb.debug` pour automatiser.
- gdb coupe l'ASLR : un succès sous gdb n'est pas une preuve hors gdb.
