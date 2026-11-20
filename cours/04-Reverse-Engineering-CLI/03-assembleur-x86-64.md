# 4.3 — Assembleur x86-64 appliqué au reverse

> Fiche du chapitre 4.3 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- lire du désassemblage dans les **deux syntaxes** (AT&T par défaut et Intel) sans confondre
  l'ordre des opérandes ;
- nommer les registres x86-64 et leurs tailles, et expliquer pourquoi `mov eax, 1` efface le haut
  de `rax` ;
- décoder un opérande mémoire `[base + index*échelle + déplacement]` et en déduire la structure C
  d'origine ;
- suivre une convention d'appel System V : où sont les arguments, où est le retour, qui doit
  sauvegarder quoi ;
- reconstituer la pile à un instant donné (`push`, `call`, prologue, `leave`) ;
- distinguer `mov` de `lea`, `cmp` de `test`, et **saut signé** de **saut non signé** — le piège
  classique des crackmes ;
- reconnaître à l'œil `if/else`, `for`, `while` et un accès tableau, y compris après optimisation.

## 1. Deux syntaxes pour un même octet

`objdump` affiche par défaut la syntaxe **AT&T**, héritée d'Unix. La syntaxe **Intel** est celle
des manuels et de la majorité des writeups. Le binaire est identique : seule la notation change.

```bash
objdump -d syntaxe.o              # AT&T (défaut)
objdump -d -M intel syntaxe.o     # Intel
```

Même fonction, deux écritures :

```text
0000000000000000 <double_it>:
   0:   55                      push   %rbp
   1:   48 89 e5                mov    %rsp,%rbp
   4:   89 7d fc                mov    %edi,-0x4(%rbp)
   7:   8b 45 fc                mov    -0x4(%rbp),%eax
   a:   01 c0                   add    %eax,%eax
   c:   5d                      pop    %rbp
   d:   c3                      ret
```

```text
0000000000000000 <double_it>:
   0:   55                      push   rbp
   1:   48 89 e5                mov    rbp,rsp
   4:   89 7d fc                mov    DWORD PTR [rbp-0x4],edi
   7:   8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
   a:   01 c0                   add    eax,eax
   c:   5d                      pop    rbp
   d:   c3                      ret
```

| Point | AT&T | Intel |
| --- | --- | --- |
| Ordre des opérandes | `source, destination` | `destination, source` |
| Préfixe registre | `%rax` | `rax` |
| Valeur immédiate | `$0x10` | `0x10` |
| Taille mémoire | suffixe (`movl`, `movq`) | `DWORD PTR`, `QWORD PTR` |
| Déplacement | `-0x4(%rbp)` | `[rbp-0x4]` |
| Index | `(%rax,%rbx,4)` | `[rax+rbx*4]` |

La règle à retenir : **en Intel, la destination est à gauche**. `mov eax, [rbp-0x4]` charge la
mémoire dans le registre ; en AT&T, la même instruction s'écrit `mov -0x4(%rbp), %eax`.

> **Choisir une syntaxe et s'y tenir.** Dans ce module, tout est en `-M intel` : c'est la syntaxe
> de radare2, de Ghidra, d'IDA et des manuels Intel. Mélanger les deux dans un writeup est la
> première source d'erreur de lecture.

## 2. Registres x86-64

Seize registres généraux, chacun accessible en 64, 32, 16 et 8 bits. **Ce sont les mêmes
registres** : écrire dans `eax` modifie `rax`.

| 64 bits | 32 bits | 16 bits | 8 bits | Rôle historique / convention |
| --- | --- | --- | --- | --- |
| `rax` | `eax` | `ax` | `al` | accumulateur, **valeur de retour** |
| `rbx` | `ebx` | `bx` | `bl` | base, *callee-saved* |
| `rcx` | `ecx` | `cx` | `cl` | compteur, 4ᵉ argument |
| `rdx` | `edx` | `dx` | `dl` | données, 3ᵉ argument, 2ᵉ retour |
| `rsi` | `esi` | `si` | `sil` | source, 2ᵉ argument |
| `rdi` | `edi` | `di` | `dil` | destination, **1ᵉʳ argument** |
| `rbp` | `ebp` | `bp` | `bpl` | base de pile (*frame pointer*) |
| `rsp` | `esp` | `sp` | `spl` | sommet de pile (*stack pointer*) |
| `r8`–`r15` | `r8d`–`r15d` | `r8w`–`r15w` | `r8b`–`r15b` | ajoutés par x86-64 |

Registres spéciaux :

- **`rip`** : pointeur d'instruction. On ne l'écrit pas directement ; `lea rax, [rip+0xe23]`
  calcule une adresse relative au code courant (position-independent).
- **`rsp`** : sommet de pile. Il bouge à chaque `push`, `pop`, `call`, `ret`.
- **`rbp`** : base de la pile locale. Facultatif (compilé avec `-fomit-frame-pointer` à `-O2`).
- **`rflags`** : drapeaux (`ZF`, `CF`, `SF`, `OF`…), alimentés par les comparaisons.

### La règle qui surprend : écrire en 32 bits efface le haut

Toute écriture dans un registre 32 bits **met à zéro les 32 bits de poids fort** du registre 64
bits correspondant. Ce n'est pas une convention, c'est dans le silicium.

```c
unsigned long widen(unsigned int v) { return v; }
```

```bash
gcc -O2 -c conv.c -o conv.o
objdump -d -M intel conv.o
```

```text
0000000000000000 <widen>:
   0:   89 f8                   mov    eax,edi
   2:   c3                      ret
```

Une seule instruction : `mov eax, edi`. Elle copie les 32 bits bas de `rdi` dans `eax`, et **cet
écriture efface `rax[63:32]`**. C'est exactement la sémantique de `return (unsigned long)v` : la
conversion d'un `unsigned int` en `unsigned long` est un zéro-extension. Le compilateur n'a pas
besoin d'un `xor rax, rax` : le `mov` 32 bits fait le travail.

Conséquence pour le reverse : quand vous voyez `mov eax, [rbp-0x4]` puis un usage de `rax`, la
valeur est **tronquée à 32 bits puis zéro-étendue**. Si le programme manipule un pointeur ou un
`size_t`, un `mov` 32 bits au milieu est suspect — c'est parfois la faille (troncature d'adresse).

À l'inverse, `movsxd rax, eax` (sign-extend) et `cdqe` **propagent le signe** : `-1` en 32 bits
devient `0xffffffffffffffff`, pas `0x00000000ffffffff`.

## 3. Lire un opérande mémoire

Forme générale :

```text
[base + index * échelle + déplacement]
```

- `base` : registre contenant une adresse (souvent `rbp`, `rsp`, `rdi`, `rip`) ;
- `index` : registre d'indice, multiplié par une **échelle** valant 1, 2, 4 ou 8 ;
- `déplacement` : constante signée.

L'échelle trahit le type : ×1 = `char`, ×2 = `short`, ×4 = `int`/`float`, ×8 = `long`/pointeur.

```c
int get2(const int *p, int i) { return p[i + 2]; }
```

```text
0000000000000000 <get2>:
   0:   48 63 f6                movsxd rsi,esi
   3:   8b 44 b7 08             mov    eax,DWORD PTR [rdi+rsi*4+0x8]
   7:   c3                      ret
```

Traduction : `rdi` = `p`, `esi` = `i` (étendu en 64 bits par `movsxd`), `rsi*4` = l'indice en
octets, `+0x8` = les deux éléments d'avance (`i + 2` sur des `int` de 4 octets). Le `DWORD PTR`
confirme la lecture de 4 octets.

| Écriture | Signification |
| --- | --- |
| `[rbp-0x10]` | variable locale à 16 octets sous la base de pile |
| `[rsp+0x8]` | 7ᵉ argument (au-dessus de l'adresse de retour) |
| `[rdi+rsi*4+0x8]` | `p[i+2]` pour un tableau d'`int` |
| `[rbp+rax*1-0x40]` | `buf[i]` où `buf` est à `rbp-0x40` |
| `[rip+0xe23]` | adresse d'une constante, calculée relativement au code |

Les tailles explicites (`BYTE PTR`, `WORD PTR`, `DWORD PTR`, `QWORD PTR`) valent 1, 2, 4 et 8
octets. Elles sont indispensables quand l'opérande est mémoire : `mov [rbp-0x4], 0` ne dit pas
combien d'octets écrire, `mov DWORD PTR [rbp-0x4], 0` si.

Exemple réel, tiré du chapitre 4.1 : `buf[strcspn(buf, "\n")] = 0` compile en

```text
mov byte [rbp+rax*1-0x40], 0x0
```

`rax` contient l'indice renvoyé par `strcspn`, `-0x40` est le début du tableau local, et
`byte` indique une écriture d'un seul octet — le `'\0'`.

## 4. Convention d'appel System V AMD64 (Linux)

Une fonction ne peut pas lire les arguments n'importe où : le compilateur et l'appelant suivent
une convention. Sur Linux x86-64, c'est la **System V ABI**.

| Argument | Registre | Taille |
| --- | --- | --- |
| 1 | `rdi` (`edi`, `di`, `dil`) | 8 / 4 / 2 / 1 octet |
| 2 | `rsi` | idem |
| 3 | `rdx` | idem |
| 4 | `rcx` | idem |
| 5 | `r8` | idem |
| 6 | `r9` | idem |
| 7 et + | pile, à partir de `[rsp+0x8]` à l'entrée | 8 octets chacun |

Valeur de retour : `rax` (et `rdx` pour un retour 128 bits, comme une `struct` de 16 octets).

```c
long add8(long a, long b, long c, long d, long e, long f, long g, long h) {
    return a + b + c + d + e + f + g + h;
}
```

```text
0000000000000010 <add8>:
  10:   48 01 f7                add    rdi,rsi        ; a + b
  13:   48 01 d7                add    rdi,rdx        ; + c
  16:   48 01 cf                add    rdi,rcx        ; + d
  19:   4c 01 c7                add    rdi,r8         ; + e
  1c:   4a 8d 04 0f             lea    rax,[rdi+r9*1] ; + f
  20:   48 03 44 24 08          add    rax,QWORD PTR [rsp+0x8]   ; + g
  25:   48 03 44 24 10          add    rax,QWORD PTR [rsp+0x10]  ; + h
  2a:   c3                      ret
```

Les six premiers arguments sont dans `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9` ; les deux suivants
sont sur la pile, à `[rsp+0x8]` et `[rsp+0x10]`. **Pourquoi `+0x8` et pas `+0x0` ?** Parce qu'à
l'entrée de la fonction, `[rsp]` contient l'**adresse de retour** poussée par `call`.

### Qui sauvegarde quoi

| Catégorie | Registres | Règle |
| --- | --- | --- |
| *caller-saved* (volatils) | `rax`, `rcx`, `rdx`, `rsi`, `rdi`, `r8`–`r11` | l'appelé peut les écraser ; l'appelant doit sauvegarder ce dont il a besoin |
| *callee-saved* (non volatils) | `rbx`, `rbp`, `r12`–`r15` | l'appelé doit les restaurer avant `ret` |
| spéciaux | `rsp` (doit revenir à sa valeur), `rflags` | restaurés par la convention |

Conséquence en reverse : si une fonction commence par `push rbx` / `push r12`, c'est qu'elle
utilise ces registres et les rendra à la fin (`pop r12` / `pop rbx`). Si vous voyez un `pop` sans
`push` correspondant, soit le binaire est patché, soit vous avez mal délimité la fonction.

> **`-mno-red-zone` et le red zone.** Les 128 octets sous `rsp` sont réservés au code feuille
> (pas d'appel) : il peut y écrire sans ajuster `rsp`. Un débogueur qui place un breakpoint dans
> cette zone peut donc voir des données « fantômes ». Rarement gênant, bon à savoir quand une
> variable semble exister avant son initialisation.

## 5. La pile en action

La pile grandit **vers les adresses basses**. `rsp` pointe toujours sur le dernier élément poussé.

```text
adresses hautes
        ┌──────────────────────┐
        │  arguments 8, 9…     │  ← [rsp+0x10], [rsp+0x8] à l'entrée
        ├──────────────────────┤
        │  adresse de retour   │  ← poussée par `call`
        ├──────────────────────┤
        │  rbp sauvegardé      │  ← `push rbp`
        ├──────────────────────┤  ← rbp
        │  variables locales   │  ← [rbp-0x4], [rbp-0x40]…
        ├──────────────────────┤  ← rsp
adresses basses
```

### `push`, `pop`, `call`, `ret`

| Instruction | Effet |
| --- | --- |
| `push rax` | `rsp -= 8` puis `[rsp] = rax` |
| `pop rax` | `rax = [rsp]` puis `rsp += 8` |
| `call f` | `push` de l'adresse de l'instruction suivante, puis saut vers `f` |
| `ret` | `pop` de l'adresse de retour dans `rip` |

`call` et `ret` ne sont donc que des `push`/`pop` déguisés. C'est ce qui rend les stack
overflows exploitables : si un `ret` lit une adresse que l'attaquant contrôle, le flot
d'exécution est détourné.

### Prologue et épilogue

```text
0000000000000000 <branch_signed>:
   0:   55                      push   rbp
   1:   48 89 e5                mov    rbp,rsp
   4:   48 83 ec 10             sub    rsp,0x10
   …
  37:   c9                      leave
  38:   c3                      ret
```

- **Prologue** : `push rbp` sauvegarde l'ancienne base, `mov rbp, rsp` fixe la nouvelle base,
  `sub rsp, 0x10` réserve 16 octets pour les locales.
- **Épilogue** : `leave` = `mov rsp, rbp` puis `pop rbp` (tout est rendu d'un coup), puis `ret`.

Repérer un prologue, c'est repérer le début d'une fonction — indispensable quand le binaire est
strippé (chapitre 4.4).

### `mov` contre `lea`

```c
int plus_one(int x) { return x + 1; }
int addr_of(int *p, int i) { return (int)(long)&p[i]; }
```

```text
0000000000000000 <plus_one>:
   0:   8d 47 01                lea    eax,[rdi+0x1]
   3:   c3                      ret

0000000000000010 <addr_of>:
  10:   8d 04 b7                lea    eax,[rdi+rsi*4]
  13:   c3                      ret
```

`mov eax, [rdi+1]` **lirait** la mémoire à l'adresse `rdi+1`. `lea eax, [rdi+1]` **calcule**
`rdi+1` et met le résultat dans `eax`, sans accès mémoire. D'où deux usages :

1. calcul d'adresse réelle (`&p[i]`) ;
2. arithmétique « gratuite » : `lea` n'affecte **aucun drapeau**, donc le compilateur l'utilise
   pour additionner sans casser un `cmp` précédent. `plus_one` en est l'exemple pur : aucun
   `mov`, aucun `add`, juste un `lea`.

## 6. Drapeaux et sauts conditionnels

`cmp a, b` calcule `a - b` et jette le résultat, en ne gardant que les drapeaux. `test a, b`
calcule `a & b` et fait de même. Aucun des deux ne modifie ses opérandes.

| Drapeau | Nom | Signification |
| --- | --- | --- |
| `ZF` | zéro | le résultat est nul (`a == b` après `cmp`) |
| `SF` | signe | le bit de poids fort est 1 (résultat négatif en signé) |
| `CF` | retenue | débordement non signé (emprunt pour une soustraction) |
| `OF` | débordement | débordement signé |
| `PF` | parité | parité du poids faible (rarement utile) |

### `cmp` vs `test`

```text
$ objdump -d -M intel cmp.o   (extraits)
0000000000000020 <gt_signed>:
  20:   31 c0                   xor    eax,eax
  22:   39 f7                   cmp    edi,esi
  24:   0f 9f c0                setg   al

0000000000000030 <gt_unsigned>:
  30:   31 c0                   xor    eax,eax
  32:   39 fe                   cmp    esi,edi
  34:   0f 92 c0                setb   al

0000000000000040 <is_zero>:
  40:   31 c0                   xor    eax,eax
  42:   85 ff                   test   edi,edi
  44:   0f 94 c0                sete   al
```

- `cmp edi, esi` + `setg` : `a > b` **signé**.
- `cmp esi, edi` + `setb` : le compilateur a **inversé les opérandes** (`b < a` non signé est
  équivalent à `a > b` non signé). Lire `setb` sans regarder l'ordre des opérandes donne un
  résultat faux.
- `test edi, edi` + `sete` : `x == 0`. `test r, r` est l'idiome du test de nullité (plus court
  qu'un `cmp r, 0`).

### Signé contre non signé : le piège classique

```c
#include <stdio.h>

void branch_signed(int a, int b) {
    if (a > b) puts("plus grand");
    else puts("plus petit ou egal");
}

void branch_unsigned(unsigned a, unsigned b) {
    if (a > b) puts("plus grand");
    else puts("plus petit ou egal");
}
```

```text
0000000000000000 <branch_signed>:
   e:   8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
  11:   3b 45 f8                cmp    eax,DWORD PTR [rbp-0x8]
  14:   7e 11                   jle    27 <branch_signed+0x27>

0000000000000039 <branch_unsigned>:
  47:   8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
  4a:   39 45 f8                cmp    DWORD PTR [rbp-0x8],eax
  4d:   73 11                   jae    60 <branch_unsigned+0x27>
```

Même source, même structure, **deux instructions différentes** :

| Condition | Saut si vrai (signé) | Saut si faux | Saut si vrai (non signé) | Saut si faux |
| --- | --- | --- | --- | --- |
| `a > b` | `jg` | `jle` | `ja` | `jbe` |
| `a >= b` | `jge` | `jl` | `jae` | `jb` |
| `a < b` | `jl` | `jge` | `jb` | `jae` |
| `a <= b` | `jle` | `jg` | `jbe` | `ja` |
| `a == b` | `je` | `jne` | `je` | `jne` |
| `a != b` | `jne` | `je` | `jne` | `je` |

Pourquoi c'est un grand classique de CTF : un `int` négatif comparé avec `ja` passe la
comparaison, car `0xffffffff` est le plus grand `unsigned`. Un vérificateur écrit
`if (len > 8) reject;` sur un `size_t` (non signé) se contourne avec une longueur négative qui
devient énorme — et en assembleur, la différence se voit uniquement au mnémonique (`ja` contre
`jg`).

À `-O2`, le compilateur remplace souvent le saut par un `cmov` (déplacement conditionnel), qui ne
crée pas de branche :

```text
0000000000000000 <max_signed>:
   0:   39 fe                   cmp    esi,edi
   2:   89 f8                   mov    eax,edi
   4:   0f 4d c6                cmovge eax,esi
   7:   c3                      ret
```

`cmovge` (signé) contre `cmova`/`cmovae` (non signé) : la même distinction, sans saut. Un graphe
de flot peut alors sembler linéaire alors que la logique est conditionnelle.

## 7. Reconnaître les structures C compilées

### `if / else`

```c
int classify(int x) {
    if (x < 0) return -1;
    else if (x == 0) return 0;
    else return 1;
}
```

```bash
gcc -O0 -c struct.c -o struct0.o && objdump -d -M intel struct0.o
gcc -O2 -c struct.c -o struct2.o && objdump -d -M intel struct2.o
```

```text
0000000000000000 <classify>:            ; -O0
   0:   55                      push   rbp
   1:   48 89 e5                mov    rbp,rsp
   4:   89 7d fc                mov    DWORD PTR [rbp-0x4],edi
   7:   83 7d fc 00             cmp    DWORD PTR [rbp-0x4],0x0
   b:   79 07                   jns    14 <classify+0x14>      ; x >= 0 → aller au test suivant
   d:   b8 ff ff ff ff          mov    eax,0xffffffff          ; return -1
  12:   eb 12                   jmp    26 <classify+0x26>
  14:   83 7d fc 00             cmp    DWORD PTR [rbp-0x4],0x0
  18:   75 07                   jne    21 <classify+0x21>      ; x != 0
  1a:   b8 00 00 00 00          mov    eax,0x0                 ; return 0
  1f:   eb 05                   jmp    26 <classify+0x26>
  21:   b8 01 00 00 00          mov    eax,0x1                 ; return 1
  26:   5d                      pop    rbp
  27:   c3                      ret
```

```text
0000000000000000 <classify>:            ; -O2
   0:   31 c0                   xor    eax,eax
   2:   85 ff                   test   edi,edi
   4:   ba ff ff ff ff          mov    edx,0xffffffff
   9:   0f 95 c0                setne  al
   c:   0f 48 c2                cmovs  eax,edx
   f:   c3                      ret
```

Lecture `-O0` : trois blocs, un `jns` (jump if not sign) qui envoie `x >= 0` vers la suite, un
`jne` pour distinguer zéro, et un `jmp` final vers le `ret` unique. Lecture `-O2` : plus aucun
saut. `xor eax,eax` + `setne al` produit 0 ou 1, puis `cmovs` écrase par `-1` si `x` est négatif.
Le `if/else` a disparu dans l'arithmétique.

### `for`

```c
int sum_array(const int *a, int n) {
    int s = 0;
    for (int i = 0; i < n; i++) s += a[i];
    return s;
}
```

```text
0000000000000028 <sum_array>:           ; -O0
  28:   55                      push   rbp
  29:   48 89 e5                mov    rbp,rsp
  2c:   48 89 7d e8             mov    QWORD PTR [rbp-0x18],rdi   ; a
  30:   89 75 e4                mov    DWORD PTR [rbp-0x1c],esi   ; n
  33:   c7 45 fc 00 00 00 00    mov    DWORD PTR [rbp-0x4],0x0    ; s = 0
  3a:   c7 45 f8 00 00 00 00    mov    DWORD PTR [rbp-0x8],0x0    ; i = 0
  41:   eb 1d                   jmp    60 <sum_array+0x38>        ; saut vers le test
  43:   8b 45 f8                mov    eax,DWORD PTR [rbp-0x8]    ; i
  46:   48 98                   cdqe
  48:   48 8d 14 85 00 00 00    lea    rdx,[rax*4+0x0]            ; i * sizeof(int)
  50:   48 8b 45 e8             mov    rax,QWORD PTR [rbp-0x18]   ; a
  54:   48 01 d0                add    rax,rdx                    ; &a[i]
  57:   8b 00                   mov    eax,DWORD PTR [rax]        ; a[i]
  59:   01 45 fc                add    DWORD PTR [rbp-0x4],eax    ; s += a[i]
  5c:   83 45 f8 01             add    DWORD PTR [rbp-0x8],0x1    ; i++
  60:   8b 45 f8                mov    eax,DWORD PTR [rbp-0x8]
  63:   3b 45 e4                cmp    eax,DWORD PTR [rbp-0x1c]
  66:   7c db                   jl     43 <sum_array+0x1b>        ; i < n → corps
  68:   8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
  6b:   5d                      pop    rbp
  6c:   c3                      ret
```

```text
0000000000000010 <sum_array>:           ; -O2
  10:   85 f6                   test   esi,esi
  12:   7e 1c                   jle    30 <sum_array+0x20>        ; n <= 0 → 0
  14:   48 63 f6                movsxd rsi,esi
  17:   31 c0                   xor    eax,eax
  19:   48 8d 14 b7             lea    rdx,[rdi+rsi*4]            ; fin = a + n
  1d:   0f 1f 00                nop    DWORD PTR [rax]
  20:   03 07                   add    eax,DWORD PTR [rdi]        ; s += *a
  22:   48 83 c7 04             add    rdi,0x4                    ; a++
  26:   48 39 d7                cmp    rdi,rdx
  29:   75 f5                   jne    20 <sum_array+0x10>        ; boucle
  2b:   c3                      ret
```

Les deux idiomes à reconnaître :

- **`-O0`** : un `jmp` vers le **test** en fin de corps, puis un saut **arrière** (`jl` vers une
  adresse plus basse) — la signature d'une boucle.
- **`-O2`** : plus d'indice. Le compilateur calcule la borne (`lea rdx,[rdi+rsi*4]`), incrémente
  le pointeur (`add rdi,0x4`) et compare pointeur et borne. Une boucle `for` peut donc
  parfaitement ne contenir **aucun** compteur visible.

### `while`

`while (cond) { corps }` compile comme `for`, avec le test en tête et le corps après. La
différence avec `for` est cosmétique : cherchez le saut arrière et le `cmp` qui le précède.

### Accès tableau et pointeur

| C | Assembleur typique |
| --- | --- |
| `a[i]` (`int`) | `mov eax, [rdi+rsi*4]` |
| `a[i+2]` | `mov eax, [rdi+rsi*4+0x8]` |
| `p->champ` | `mov eax, [rdi+0x10]` |
| `*p++` | `mov eax, [rdi]` puis `add rdi, 0x4` |
| `s.champ` (local) | `mov eax, [rbp-0x8]` |

### Tableau d'idiomes

| Motif observé | Structure C probable |
| --- | --- |
| `test eax, eax` + `je` | `if (!ptr)`, `if (x == 0)` |
| `cmp eax, 1` + `jne` | `if (x != 1)` |
| `xor eax, eax` en fin de fonction | `return 0` |
| `cmp` + saut arrière | boucle |
| `lea rax, [rdi+rsi*4]` | indexation d'un tableau d'`int` |
| `movzx eax, byte [rax]` | lecture d'un `char`/`unsigned char` |
| `imul` ou `shl`+`sub` | multiplication (par 31 = `shl 5` puis `sub`) |
| `push` en série avant un `call` | plus de 6 arguments |

## 8. Exercice pratique

### Le programme

Créer `verif.c` :

```c
#include <stdio.h>
#include <string.h>

static int checksum(const char *s) {
    int acc = 0;
    for (int i = 0; s[i]; i++)
        acc = acc * 31 + (unsigned char)s[i];
    return acc;
}

int main(void) {
    char buf[64];

    printf("cle: ");
    if (!fgets(buf, sizeof buf, stdin))
        return 1;
    buf[strcspn(buf, "\n")] = 0;

    if (strlen(buf) == 4 && checksum(buf) == 0x3593c2)
        puts("bravo");
    else
        puts("non");

    return 0;
}
```

```bash
gcc -O0 -o verif verif.c
./verif          # taper une clé au hasard
objdump -d -M intel verif
```

> Les adresses exactes (`1179`, `11d2`…) dépendent de votre version de gcc et de la libc. Les
> **instructions**, les **décalages** (`[rbp-0x40]`, `0x3593c2`) et la logique, eux, sont stables.

### Questions

1. Où est stocké le buffer saisi, et comment le voit-on dans `main` ?
2. Quelle condition porte sur la longueur ? Que se passe-t-il si elle est fausse ?
3. Dans `checksum`, comment `acc * 31` est-il calculé ? Pourquoi le compilateur n'utilise-t-il pas
   `imul` ?
4. Où la valeur finale est-elle comparée, et à quoi ?
5. En déduire une clé valide. Pourquoi `rv43` échoue-t-il alors que `rv42` passe ?

<details>
<summary>Correction</summary>

**1. Le buffer**

```text
11d6:   48 83 ec 40             sub    rsp,0x40
...
11f5:   48 8d 45 c0             lea    rax,[rbp-0x40]      ; &buf
11f9:   be 40 00 00 00          mov    esi,0x40             ; sizeof buf
1201:   e8 6a fe ff ff          call   1070 <fgets@plt>
```

`sub rsp, 0x40` réserve 64 octets, et `lea rax, [rbp-0x40]` charge l'adresse du buffer. Le même
`[rbp-0x40]` revient pour `strcspn` et `strlen` : c'est bien `buf`.

**2. La longueur**

```text
1234:   e8 07 fe ff ff          call   1040 <strlen@plt>
1239:   48 83 f8 04             cmp    rax,0x4
123d:   75 24                   jne    1263 <main+0x91>     ; → "non"
```

`strlen(buf) == 4`. Si la longueur diffère, le `jne` saute directement au bloc qui affiche
`non` : le `checksum` n'est même pas appelé.

**3. `acc * 31`**

```text
1191:   8b 55 fc                mov    edx,DWORD PTR [rbp-0x4]   ; acc
1194:   89 d0                   mov    eax,edx
1196:   c1 e0 05                shl    eax,0x5                  ; acc * 32
1199:   29 d0                   sub    eax,edx                  ; - acc  →  acc * 31
```

`31 = 32 - 1` : un `shl` de 5 bits suivi d'une soustraction, plus rapide qu'un `imul`. C'est un
motif très fréquent pour les multiplications par une constante (`*3`, `*5`, `*9`, `*31`, `*33`).
Le `acc` et l'indice `i` sont dans `[rbp-0x4]` et `[rbp-0x8]`.

**4. La comparaison finale**

```text
1246:   e8 2e ff ff ff          call   1179 <checksum>
124b:   3d c2 93 35 00          cmp    eax,0x3593c2
1250:   75 11                   jne    1263 <main+0x91>     ; → "non"
```

La valeur de retour (`eax`) est comparée à `0x3593c2`. En décimal : 3 511 234.

**5. La clé**

Deux contraintes : 4 caractères, et `checksum == 0x3593c2`, avec
`acc = acc*31 + c`. Il suffit de rejouer le calcul :

```python
import itertools, string

target = 0x3593c2
alpha = string.ascii_lowercase + string.digits

def ck(s):
    a = 0
    for c in s:
        a = (a * 31 + ord(c)) & 0xffffffff
    return a

for t in itertools.product(alpha, repeat=4):
    s = "".join(t)
    if ck(s) == target:
        print(s)
        break
```

```text
$ python3 brute.py
rtpp
```

```text
$ echo rtpp | ./verif
cle: bravo
```

**Attention :** `rtpp` n'est pas la clé « prévue » (`rv42`), mais elle passe aussi. Le checksum
est une fonction de 4 octets vers 32 bits : elle n'est pas injective, donc **plusieurs clés sont
valides**. C'est un comportement réaliste — et une leçon : dans un crackme, il n'y a pas
toujours *une* bonne réponse, il y a **toutes** les entrées qui satisfont la vérification. Un
writeup honnête le dit.

`rv43` échoue parce que son checksum vaut `0x3593c3` : un seul caractère change, mais le calcul
est sensible à chaque octet, et la comparaison finale échoue → `non`.

</details>

## 9. Ce que je retiens

- **Intel = destination à gauche.** Travailler en `-M intel` partout évite la moitié des erreurs.
- Les registres 32 bits sont des vues sur les 64 bits : écrire dans `eax` **efface** `rax[63:32]`.
  `movsxd` et `cdqe` propagent le signe, un `mov` 32 bits zéro-étend.
- `[base + index*échelle + déplacement]` : l'échelle donne la taille de l'élément (1, 2, 4, 8).
- Arguments : `rdi, rsi, rdx, rcx, r8, r9`, puis la pile à partir de `[rsp+0x8]`. Retour dans
  `rax`. `rbx`, `rbp`, `r12`–`r15` doivent être restaurés par l'appelé.
- `call` = `push` de l'adresse de retour + saut ; `ret` = `pop` dans `rip`. Le prologue
  `push rbp; mov rbp,rsp` et l'épilogue `leave; ret` délimitent une fonction.
- `mov` lit la mémoire, `lea` calcule une adresse — et ne touche pas aux drapeaux.
- `cmp`/`test` alimentent `ZF`, `SF`, `CF`, `OF`. **`jg` est signé, `ja` ne l'est pas** : c'est
  le piège de comparaison le plus exploité en CTF.
- À `-O2`, les sauts deviennent des `cmov`, les indices deviennent des pointeurs, et les
  multiplications par constante deviennent des `shl`/`sub`.

## Références

- [Intel SDM volume 2](https://www.intel.com/sdm) — jeu d'instructions complet
- [felixcloutier.com/x86](https://www.felixcloutier.com/x86/) — la même chose, navigable
- [System V ABI x86-64](https://gitlab.com/x86-psABIs/x86-64-ABI) — conventions d'appel
- [Agner Fog — optimisation de l'assembleur](https://www.agner.org/optimize/) — pourquoi le
  compilateur produit ces motifs
