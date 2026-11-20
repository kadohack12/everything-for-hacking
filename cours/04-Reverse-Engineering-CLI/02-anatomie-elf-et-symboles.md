# 4.2 — Anatomie ELF et inspection des symboles

> Fiche du chapitre 4.2 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- décrire un ELF par ses **trois vues** : en-tête, segments (program headers) et sections ;
- lire `readelf -h`, `-l`, `-S`, `-s`, `-r`, `-d` et dire ce que chaque sortie prouve ;
- nommer le rôle des sections qui comptent en reverse (`.text`, `.rodata`, `.data`, `.bss`,
  `.plt`, `.got`) et prédire où chercher une donnée ;
- expliquer la différence entre binaire **dynamique**, **statique** et **strippé**, et l'impact de
  chacun sur la stratégie d'analyse ;
- **ne jamais** lancer `ldd` sur un binaire non fiable, et savoir par quoi le remplacer.

## 1. Pourquoi l'ELF compte en reverse

Un binaire n'est pas un bloc opaque : c'est un conteneur structuré, avec un sommaire (l'en-tête),
une table des matières pour l'exécution (les segments) et une pour l'édition de liens (les
sections). Savoir où est quoi permet de répondre à des questions concrètes :

| Question | Réponse dans l'ELF |
| --- | --- |
| Où commence l'exécution ? | `e_entry` de l'en-tête |
| Quel code est exécutable ? | segment `LOAD` avec le droit `E` |
| Où sont mes chaînes en clair ? | section `.rodata` |
| Pourquoi `nm` ne montre rien ? | table `.symtab` absente (strippé) |
| Quelles bibliothèques sont chargées ? | entrées `NEEDED` de `.dynamic` |
| Où est appelée `printf` ? | `.plt` + `.got` |

Les trois vues, du plus général au plus fin :

```text
En-tête (readelf -h)      → méta-informations : type, machine, point d'entrée, offsets
Segments (readelf -l)     → ce que le chargeur mappe en mémoire (LOAD, INTERP, GNU_STACK…)
Sections (readelf -S)     → ce que l'éditeur de liens et l'analyseur voient (.text, .data…)
```

**Point clé :** le noyau et le loader utilisent les **segments**. Les sections sont une vue
d'analyse — elles peuvent même être absentes (binaire UPX : `no section header`) sans empêcher
l'exécution.

## 2. L'en-tête — `readelf -h`

```bash
readelf -h demo
```

```text
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF64
  Data:                              2's complement, little endian
  Version:                           1 (current)
  OS/ABI:                            UNIX - System V
  ABI Version:                       0
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Version:                           0x1
  Entry point address:               0x1050
  Start of program headers:          64 (bytes into file)
  Start of section headers:          14000 (bytes into file)
  Flags:                             0x0
  Size of this header:               64 (bytes)
  Size of program headers:           56 (bytes)
  Number of program headers:         14
  Size of section headers:           64 (bytes)
  Number of section headers:         31
  Section header string table index: 30
```

| Champ | Valeur ici | Ce qu'il faut en retenir |
| --- | --- | --- |
| `Magic` | `7f 45 4c 46` | `\x7fELF` : c'est ce que `file` lit en premier |
| `Class` | `ELF64` | pointeurs 64 bits, registres `rax`…`r15` |
| `Data` | little endian | les entiers multi-octets se lisent à l'envers |
| `Type` | `DYN` | exécutable **PIE** : base aléatoire, adresses non stables |
| `Machine` | `X86-64` | jeu d'instructions visé |
| `Entry point` | `0x1050` | **première instruction exécutée** — mais pas `main` |
| `Number of program headers` | 14 | taille de la vue « segments » |
| `Number of section headers` | 31 | taille de la vue « sections » |

`Type: DYN` sur un exécutable surprend : un PIE est techniquement une **shared object** avec un
point d'entrée. C'est pour ça que `file` dit `pie executable` et que `readelf` dit `DYN`. Pour
obtenir un binaire à adresses fixes (plus simple à patcher), on compile avec `-no-pie` :

```bash
gcc -O0 -no-pie -o demo-nopie demo.c   # Type: EXEC, adresses stables
```

> **`e_entry` n'est pas `main`.** Le point d'entrée est `_start` (dans la libc ou dans le
> `crt`), qui prépare la pile et appelle `__libc_start_main`, laquelle appelle `main`. C'est
> pourquoi un `break *0x1050` dans `gdb` arrête avant tout code applicatif.

## 3. Segments — `readelf -l`

```bash
readelf -l demo
```

```text
Elf file type is DYN (Position-Independent Executable file)
Entry point 0x1050
There are 14 program headers, starting at offset 64

Program Headers:
  Type           Offset             VirtAddr           PhysAddr
                 FileSiz            MemSiz              Flags  Align
  PHDR           0x0000000000000040 0x0000000000000040 0x0000000000000040
                 0x0000000000000310 0x0000000000000310  R      0x8
  INTERP         0x0000000000000394 0x0000000000000394 0x0000000000000394
                 0x000000000000001c 0x000000000000001c  R      0x1
      [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
  LOAD           0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000628 0x0000000000000628  R      0x1000
  LOAD           0x0000000000001000 0x0000000000001000 0x0000000000001000
                 0x000000000000017d 0x000000000000017d  R E    0x1000
  LOAD           0x0000000000002000 0x0000000000002000 0x0000000000002000
                 0x0000000000000134 0x0000000000000134  R      0x1000
  LOAD           0x0000000000002dd0 0x0000000000003dd0 0x0000000000003dd0
                 0x0000000000000248 0x0000000000000250  RW     0x1000
  DYNAMIC        0x0000000000002de0 0x0000000000003de0 0x0000000000003de0
                 0x00000000000001e0 0x00000000000001e0  RW     0x8
  NOTE           0x0000000000000350 0x0000000000000350 0x0000000000000350
                 0x0000000000000020 0x0000000000000020  R      0x8
  GNU_EH_FRAME   0x0000000000002014 0x0000000000002014 0x0000000000002014
                 0x0000000000000034 0x0000000000000034  R      0x4
  GNU_STACK      0x0000000000000000 0x0000000000000000 0x0000000000000000
                 0x0000000000000000 0x0000000000000000  RW     0x10
  GNU_RELRO      0x0000000000002dd0 0x0000000000003dd0 0x0000000000003dd0
                 0x0000000000000230 0x0000000000000230  R      0x1
```

Ce qui compte pour le reverse :

- **`LOAD` avec le flag `E`** (`R E`) : c'est la région exécutable, donc le code. Ici
  `0x1000`–`0x117d`.
- **`LOAD` `R` seul** : données en lecture seule — c'est là que vivent les chaînes (`.rodata`).
- **`LOAD` `RW`** : données modifiables (`.data`, `.bss`, `.got`). Le `MemSiz` (0x250) est
  supérieur au `FileSiz` (0x248) : les 8 octets d'écart sont le `.bss`, qui n'occupe **rien** sur
  le disque.
- **`INTERP`** : le loader demandé. C'est ce chemin que `ldd` exécute (section 8).
- **`GNU_STACK` `RW`** : pile non exécutable (NX). S'il était `RWE`, le binaire accepterait du
  shellcode sur la pile — un indice de binaire ancien ou volontairement permissif.
- **`GNU_RELRO`** : zone rendue en lecture seule après les relocations (durcissement).

### La table de correspondance sections → segments

`readelf -l` affiche aussi le mapping, qui répond à « si je patche `.text`, dans quel segment
est-ce ? » :

```text
 Section to Segment mapping:
  Segment Sections...
   00
   01     .interp
   02     .note.gnu.property .note.gnu.build-id .interp .gnu.hash .dynsym .dynstr .gnu.version .gnu.version_r .rela.dyn .rela.plt
   03     .init .plt .plt.got .text .fini
   04     .rodata .eh_frame_hdr .eh_frame .note.ABI-tag
   05     .init_array .fini_array .dynamic .got .got.plt .data .bss
```

Lecture immédiate : le segment 03 (exécutable) contient `.init .plt .plt.got .text .fini`. Le
segment 04 (lecture seule) contient `.rodata`. Le segment 05 (lecture/écriture) contient `.data`,
`.bss`, `.got`. Une modification d'octet dans `.rodata` est donc une modification dans un segment
`R` : elle reste lisible au chargement, mais le programme ne peut pas l'écrire lui-même.

## 4. Sections — `readelf -S`

```bash
readelf -S demo | grep -E '\.(text|rodata|data|bss|plt|got|init|fini)\b'
```

```text
[10] .rela.plt         RELA             0000000000000610  00000610
[11] .init             PROGBITS         0000000000001000  00001000
[12] .plt              PROGBITS         0000000000001020  00001020
[13] .plt.got          PROGBITS         0000000000001040  00001040
[14] .text             PROGBITS         0000000000001050  00001050
[15] .fini             PROGBITS         0000000000001174  00001174
[16] .rodata           PROGBITS         0000000000002000  00002000
[23] .got              PROGBITS         0000000000003fc0  00002fc0
[24] .got.plt          PROGBITS         0000000000003fe8  00002fe8
[25] .data             PROGBITS         0000000000004008  00003008
[26] .bss              NOBITS           0000000000004018  00003018
```

| Section | Contenu | Intérêt en reverse |
| --- | --- | --- |
| `.text` | code machine | désassembler, patcher un test (`jne` → `je`) |
| `.rodata` | constantes en lecture seule | **chaînes en clair**, tables, clés statiques |
| `.data` | variables initialisées, modifiables | état global, pointeurs |
| `.bss` | variables non initialisées (`NOBITS`) | taille en mémoire seulement, zéro sur disque |
| `.init` / `.fini` | code de démarrage / de fin | rarement utile, sauf anti-debug placé là |
| `.plt` | stubs d'appel aux fonctions externes | voir où `printf` est appelé |
| `.got` / `.got.plt` | adresses résolues des fonctions externes | cible classique de hook / `LD_PRELOAD` |
| `.dynsym` / `.dynstr` | symboles et chaînes **dynamiques** | survivent au `strip` |
| `.symtab` / `.strtab` | symboles **complets** | disparaissent au `strip` |
| `.rela.dyn` / `.rela.plt` | relocations | comprennent comment les adresses sont fixées |
| `.comment` | version du compilateur | indice de chaîne de compilation |
| `.eh_frame` | infos de déroulement de pile | aide `gdb`, rarement une cible |

Deux détails qui piègent :

- **`NOBITS`** (`.bss`) : la section a une adresse et une taille, mais **aucun octet dans le
  fichier**. Chercher son contenu dans `xxd` est vain — elle est à zéro par définition.
- **Les tailles** : `readelf -S` affiche `Address` (en mémoire) et `Offset` (dans le fichier).
  Pour un patch à l'octet, c'est l'**Offset** qu'il faut (chapitre 4.6), pas l'adresse.

`objdump -x` donne une vue équivalente, pratique quand on veut tout d'un coup :

```text
$ objdump -x demo | head -6

demo:     file format elf64-x86-64
demo
architecture: i386:x86-64, flags 0x00000150:
HAS_SYMS, DYNAMIC, D_PAGED
start address 0x0000000000001050
```

## 5. `.plt` et `.got` — comment un appel à `printf` devient une adresse

Le programme ne connaît pas l'adresse de `printf` à la compilation : elle est dans `libc.so.6`,
chargée à l'exécution. La chaîne est :

```text
call printf@plt  →  .plt saute vers l'adresse stockée dans .got.plt  →  libc
```

Les relocations décrivent cette résolution :

```bash
readelf -r demo | head -8
```

```text
Relocation section '.rela.dyn' at offset 0x550 contains 8 entries:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000003dd0  000000000008 R_X86_64_RELATIVE                    1130
000000003dd8  000000000008 R_X86_64_RELATIVE                    10f0
000000004010  000000000008 R_X86_64_RELATIVE                    4010
000000003fc0  000100000006 R_X86_64_GLOB_DAT 0000000000000000 __libc_start_main@GLIBC_2.34 + 0
```

- `R_X86_64_RELATIVE` : « ajoute la base de chargement à cette adresse » — typique du PIE.
- `R_X86_64_GLOB_DAT` / `JUMP_SLOT` : « écris ici l'adresse du symbole ».

En reverse, cette mécanique sert à trois choses : repérer **quelles** fonctions externes sont
utilisées (`readelf -r`, `nm -D`), intercepter un appel (`LD_PRELOAD`, `gdb` breakpoint), et
comprendre pourquoi un patch dans `.got` « prend » alors qu'un patch dans `.text` est écrasé.

## 6. Symboles — `nm`, `readelf -s`, `c++filt`

Un symbole est un nom associé à une adresse. C'est ce qui transforme `0x1139` en `helper`.

```bash
nm demo | grep -E 'helper|main'
```

```text
0000000000001139 T helper
0000000000001147 T main
```

Le **type** de symbole est une information :

| Lettre | Sens | Exemple |
| --- | --- | --- |
| `T` / `t` | fonction dans `.text` (majuscule = globale, minuscule = locale) | `T main` |
| `U` | non défini, fourni par une bibliothèque | `U printf@GLIBC_2.2.5` |
| `w` / `W` | weak, résolu s'il existe | `w __gmon_start__` |
| `D` / `d` | donnée initialisée | `D banner` |
| `B` / `b` | donnée non initialisée (`.bss`) | `B buffer` |
| `R` / `r` | donnée en lecture seule (`.rodata`) | `R secret` |

`readelf -s` donne les mêmes symboles avec plus de colonnes (taille, section, visibilité) :

```text
$ readelf -s demo | grep -E 'helper| main$'
    31: 0000000000001147    43 FUNC    GLOBAL DEFAULT   14 main
    34: 0000000000001139    14 FUNC    GLOBAL DEFAULT   14 helper
```

`14` est l'index de section : `.text` (voir `readelf -S`). La taille (43 et 14 octets) permet de
savoir où s'arrête la fonction — utile pour délimiter un patch.

### `nm -D` : les symboles dynamiques

```text
$ nm -D demo
                 w _ITM_deregisterTMCloneTable
                 w _ITM_registerTMCloneTable
                 w __cxa_finalize@GLIBC_2.2.5
                 w __gmon_start__
                 U __libc_start_main@GLIBC_2.34
                 U printf@GLIBC_2.2.5
```

`-D` lit `.dynsym` : **uniquement** les symboles visibles à l'édition de liens dynamique. Ce sont
les seuls qui survivent à un `strip`, et ils révèlent quelles fonctions de la libc le programme
utilise. C'est souvent suffisant pour deviner le comportement : `printf` + `fgets` + `strcmp` =
lecture d'un mot de passe et comparaison.

### C++ : le démangling

Les noms C++ sont **mangés** pour encoder namespaces, classes et types de paramètres.

```text
$ nm demo-cpp | grep decode
0000000000001219 T _ZN3rev6decodeERKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE
```

Deux façons de le rendre lisible :

```text
$ nm -C demo-cpp | grep decode
0000000000001219 T rev::decode(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)

$ nm demo-cpp | grep decode | c++filt
0000000000001219 T rev::decode(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)
```

`nm -C` et `c++filt` font le même travail ; `c++filt` est pratique pour démangler une sortie
d'`objdump` ou de `gdb` :

```bash
objdump -d demo-cpp | c++filt | less
```

Un nom démanglé dit souvent tout : `check_password`, `decrypt_flag`, `validate_serial`. C'est la
première chose à chercher quand les symboles sont présents.

## 7. Dynamique, statique, strippé — et ce que ça change

Le même code, compilé de trois façons :

```bash
gcc -O0 -o demo demo.c                    # dynamique, avec symboles
gcc -O0 -s -o demo-stripped demo.c        # dynamique, sans table de symboles
gcc -O0 -static -o demo-static demo.c     # tout lié dans le binaire
```

```text
$ file demo demo-stripped demo-static
demo:          ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, …, not stripped
demo-stripped: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, …, stripped
demo-static:   ELF 64-bit LSB executable, x86-64, version 1 (GNU/Linux), statically linked, …, not stripped
```

(sortie abrégée : les `BuildID[sha1]` sont omis.)

```text
$ stat -c '%s %n' demo demo-stripped demo-static
15984 demo
14472 demo-stripped
754328 demo-static
```

| Variante | Taille | Symboles | Dépendances | Conséquence en reverse |
| --- | --- | --- | --- | --- |
| dynamique | 16 Ko | `.symtab` + `.dynsym` | `libc.so.6` | le plus facile : `nm`, `ltrace`, `LD_PRELOAD` |
| `-s` (strippé) | 14 Ko | `.dynsym` seul | `libc.so.6` | pas de noms internes : analyse par structure |
| `-static` | 754 Ko | tout, y compris la libc | aucune | énorme, mais **tout** est dans le binaire |

### Strippé : ce qui reste, ce qui disparaît

```text
$ nm demo-stripped
nm: demo-stripped: no symbols

$ readelf -s demo-stripped | grep -c ' main'
0
```

`main` et `helper` ont disparu. Mais :

- `nm -D demo-stripped` montre toujours `printf`, `__libc_start_main`… ;
- `strings` donne toujours les chaînes ;
- **le code est identique** : le strip ne retire que la table des noms, pas les instructions.

Conséquence pratique : sur un binaire strippé, on perd les noms mais pas les points d'appui. On
retrouve `main` en partant de `__libc_start_main` dans `gdb`, ou en repérant le premier argument
passé à `__libc_start_main` (`r2` fait ça automatiquement, chapitre 4.4).

### Statique : plus gros, mais autonome

Un binaire statique embarque la libc, donc des milliers de fonctions nommées (`nm` en sort des
dizaines de milliers de lignes). Deux conséquences :

1. **Les noms de la libc sont là** : `printf` est une vraie fonction du binaire, pas un stub
   `.plt`. Un `nm | grep -i strcmp` donne directement une adresse utilisable.
2. **`ltrace` ne montre plus rien** (aucun appel de bibliothèque dynamique) : il faut `strace`
   ou `gdb`.

Le repérage du code applicatif au milieu de la libc est le vrai travail : chercher `main` par
`__libc_start_main`, ou partir des chaînes de l'application et remonter les références.

## 8. Sécurité : ne jamais lancer `ldd` sur un binaire non fiable

`ldd` n'est pas un outil de lecture : il **exécute le loader** du binaire pour lui demander la
liste de ses dépendances. Le manuel de `ldd` le dit explicitement — selon la façon dont le
programme désigne son interpréteur, `ldd` peut finir par exécuter du code du binaire lui-même.

Autrement dit : `ldd inconnu` est équivalent à « exécute ce binaire, dans une variante ».
Sur un échantillon malveillant, c'est exactement ce qu'on veut éviter (chapitre 4.1).

Deux mécanismes sont en cause :

- le binaire peut déclarer un **`INTERP`** arbitraire (`readelf -l`), et c'est ce programme-là que
  `ldd` lance ;
- il peut déclarer un `NEEDED` avec un **chemin** (et non un simple nom), ce qui force le
  chargement d'une bibliothèque choisie par l'attaquant.

### Les équivalents sûrs

| Au lieu de… | Utiliser | Ce qu'on obtient |
| --- | --- | --- |
| `ldd binaire` | `readelf -d binaire \| grep NEEDED` | liste des bibliothèques, **sans exécution** |
| `ldd binaire` | `objdump -p binaire \| grep NEEDED` | idem, via `objdump` |
| `ldd binaire` | `patchelf --print-needed binaire` | idem, lisible |
| `ldd binaire` | `readelf -l binaire \| grep interpreter` | l'interpréteur qui **serait** lancé |

```text
$ readelf -d demo | head -4

Dynamic section at offset 0x2de0 contains 26 entries:
  Tag        Type                         Name/Value
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
```

```text
$ objdump -p demo | grep NEEDED
  NEEDED               libc.so.6
```

> **Règle.** Sur un binaire dont je ne connais pas la provenance : `readelf`, `objdump`, `nm`,
> `strings`, `xxd`. Jamais `ldd`, jamais `./binaire`, jamais `strace ./binaire` avant d'avoir
> décidé, en connaissance de cause, de l'exécuter dans un environnement isolé.

## 9. Exercice pratique

### Le code

```c
#include <stdio.h>

int helper(int x) { return x * 2; }

int main(void) {
    printf("resultat: %d\n", helper(21));
    return 0;
}
```

### Compilation des trois variantes

```bash
gcc -O0 -o demo demo.c
gcc -O0 -s -o demo-stripped demo.c
gcc -O0 -static -o demo-static demo.c
```

### Questions

1. Dans `readelf -h demo`, quels champs indiquent un binaire 64 bits et un exécutable
   position-independent ?
2. Combien de segments `LOAD` y a-t-il, et lequel contient le code ? Comment le sait-on ?
3. Dans quel segment se trouve `.rodata` ? Que peut-on en déduire sur la modification d'une
   chaîne à l'exécution ?
4. Que renvoie `nm demo-stripped` ? Le code a-t-il changé pour autant ? Comment le prouver ?
5. Pourquoi `demo-static` fait-il presque 50 fois la taille de `demo` ? Quel outil devient inutile
   dessus ?

<details>
<summary>Correction</summary>

**1. Champs de l'en-tête**

```text
Class:                             ELF64
Data:                              2's complement, little endian
Type:                              DYN (Position-Independent Executable file)
```

`ELF64` pour la largeur, `DYN` pour le PIE (un exécutable PIE est techniquement une shared object
avec un point d'entrée). `Data: little endian` confirme l'ordre des octets.

**2. Segments `LOAD`**

```bash
readelf -l demo | grep -c '^  LOAD'
```

→ **4** segments `LOAD`. Le code est dans celui qui porte le flag `E` :

```text
  LOAD           0x0000000000001000 0x0000000000001000 0x0000000000001000
                 0x000000000000017d 0x000000000000017d  R E    0x1000
```

`R E` = lisible et exécutable. La table de mapping le confirme :
`03 .init .plt .plt.got .text .fini`.

**3. `.rodata`**

```text
   04     .rodata .eh_frame_hdr .eh_frame .note.ABI-tag
```

Segment 04, qui est `LOAD` avec le seul droit `R`. Une chaîne de `.rodata` est donc en **lecture
seule** : le programme ne peut pas la modifier lui-même à l'exécution. Pour la changer, il faut
patcher le fichier sur disque (chapitre 4.6), pas compter sur un `strcpy`.

**4. Strippé**

```text
$ nm demo-stripped
nm: demo-stripped: no symbols
```

La table `.symtab` a été retirée, donc plus aucun nom interne. Le code, lui, est identique : on le
prouve en comparant les octets de `.text` ou le désassemblage de `main` entre les deux binaires
(les adresses peuvent différer, les instructions non) :

```bash
objdump -d --no-show-raw-insn demo | sed -n '/<main>:/,/^$/p'
objdump -d --no-show-raw-insn demo-stripped | sed -n '/^0000000000001147/,/^$/p'
```

Et `nm -D demo-stripped` montre toujours `printf` et `__libc_start_main` : les symboles dynamiques
survivent au strip.

**5. Statique**

`demo-static` embarque la libc entière (allocateur, `printf`, locales, `dlopen`…) : d'où les
754 328 octets. `ltrace` devient inutile — il n'y a plus d'appels de bibliothèque dynamique à
intercepter, tout est résolu à l'édition de liens. On passe à `strace` (appels système) ou `gdb`.

</details>

## 10. Ce que je retiens

- Un ELF a **trois vues** : en-tête (méta), segments (exécution), sections (analyse). Le loader
  utilise les segments ; les sections peuvent disparaître (UPX) sans casser le binaire.
- `e_entry` n'est pas `main` : c'est `_start`, qui passe par `__libc_start_main`.
- `.rodata` = chaînes en lecture seule ; `.data` = modifiable ; `.bss` = `NOBITS`, zéro octet sur
  le disque.
- `.plt`/`.got` expliquent comment un appel à `printf` trouve son adresse : c'est aussi la cible
  des hooks.
- `nm` = symboles complets, `nm -D` = dynamiques (survivent au strip), `nm -C` / `c++filt` =
  noms C++ lisibles.
- **Strippé ≠ différent** : le code est identique, seuls les noms manquent. Le reverse continue.
- **Jamais `ldd` sur un binaire non fiable** : `readelf -d`, `objdump -p | grep NEEDED`,
  `patchelf --print-needed` donnent la même information sans exécuter quoi que ce soit.

## Références

- `man readelf`, `man objdump`, `man nm`, `man ldd` (section « Security »)
- [ELF — spécification](https://refspecs.linuxfoundation.org/elf/elf.pdf)
- [System V ABI x86-64](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [Itanium C++ ABI — name mangling](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#mangling)
