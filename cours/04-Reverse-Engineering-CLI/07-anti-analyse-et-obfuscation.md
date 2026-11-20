# 4.7 — Anti-analyse et obfuscation

> Fiche du chapitre 4.7 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- retrouver `main` dans un binaire **strippé** (`gcc -s`) en partant du point d'entrée, avec
  `readelf`, `objdump`, `radare2` et `gdb` ;
- expliquer ce qui disparaît dans un binaire **statique et strippé** (`-static -s`) — `ltrace`,
  `sym.imp.*` — et m'orienter quand même : `iz`, `axt`, filtrage du bruit de la libc ;
- décrire les deux anti-debug Linux classiques (`ptrace(PTRACE_TRACEME)`, `TracerPid` de
  `/proc/self/status`) et savoir **pourquoi l'ordre des tests compte** ;
- contourner chacun en **CLI** : `gdb` (`catch syscall ptrace`, `$rax = 0`, `finish`), `LD_PRELOAD`,
  puis patch binaire à `r2 -w` ;
- récupérer une chaîne **XORée** ou une **stack string** en dynamique, sans réécrire le
  déchiffrement ;
- réparer un **UPX** dont la signature a été altérée, puis le décompresser ;
- résoudre un crackme `-O0 -s` qui combine anti-debug et chaîne chiffrée.

Tout est vérifié sur Debian 13 avec `gcc 14.2`, `binutils 2.44`, `gdb 16.3`, `upx 4.2.4` et
`radare2`. Les sorties montrées sont celles de mes exécutions.

## 1. Binaire strippé : retrouver `main` sans symboles

`gcc -s` supprime la table `.symtab`. Le binaire reste parfaitement exécutable, mais `nm` ne
répond plus rien : plus de `main`, plus de noms de fonctions.

```bash
mkdir -p ~/rev-lab/47 && cd ~/rev-lab/47

cat > hello.c <<'EOF'
#include <stdio.h>
#include <string.h>

int main(void) {
    char nom[32];

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    if (strcmp(nom, "admin") == 0)
        puts("bienvenue");
    else
        puts("inconnu");

    return 0;
}
EOF

gcc -O0 -o hello hello.c            # avec symboles
gcc -O0 -s -o hello_s hello.c       # strippé, dynamique
gcc -O0 -static -s -o hello_ss hello.c   # strippé, statique

echo admin > in.txt                 # entrée utilisée plus bas sous gdb
```

```text
$ ls -l hello hello_s hello_ss | awk '{print $5, $9}'
16200 hello
14504 hello_s
676288 hello_ss
```

Le binaire strippé perd 1,7 ko de symboles ; le statique en gagne 660 ko de libc.

### Ce qui reste, ce qui part

```text
$ file hello_s
hello_s:  ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=9b9cf435b0ec165841f17085d144cb99ab784b9d, for GNU/Linux 3.2.0, stripped

$ nm hello_s
nm: hello_s: no symbols

$ nm -D hello_s | head -4
                 w _ITM_deregisterTMCloneTable
                 w _ITM_registerTMCloneTable
                 w __cxa_finalize@GLIBC_2.2.5
                 w __gmon_start__
```

`nm -D` lit `.dynsym`, la table **dynamique** : celle dont l'éditeur de liens a besoin à
l'exécution. Elle n'est jamais supprimée par `-s`. On y trouve les imports (`puts`, `strcmp`…),
donc les fonctions de la libc, mais **pas** `main`.

```text
$ readelf -S hello_s | grep -E '\.symtab|\.dynsym'
  [ 5] .dynsym           DYNSYM           00000000000003d8  000003d8
```

Plus de `.symtab`, `.dynsym` intact.

### Le point d'entrée est toujours là

```text
$ readelf -h hello_s | grep -E 'Type|Entry'
  Type:                              DYN (Position-Independent Executable file)
  Entry point address:               0x1090
```

`0x1090` est `_start`, le code que le noyau exécute en premier (après le chargeur dynamique pour
un PIE). `objdump` désassemble à cette adresse même sans symboles :

```bash
objdump -d -M intel --start-address=0x1090 --stop-address=0x10b2 hello_s
```

```text
0000000000001090 <.text>:
    1090:       31 ed                   xor    ebp,ebp
    1092:       49 89 d1                mov    r9,rdx
    1095:       5e                      pop    rsi
    1096:       48 89 e2                mov    rdx,rsp
    1099:       48 83 e4 f0             and    rsp,0xfffffffffffffff0
    109d:       50                      push   rax
    109e:       54                      push   rsp
    109f:       45 31 c0                xor    r8d,r8d
    10a2:       31 c9                   xor    ecx,ecx
    10a4:       48 8d 3d ce 00 00 00    lea    rdi,[rip+0xce]        # 1179 <__cxa_finalize@plt+0xf9>
    10ab:       ff 15 0f 2f 00 00       call   QWORD PTR [rip+0x2f0f]        # 3fc0 <__cxa_finalize@plt+0x2f40>
    10b1:       f4                      hlt
```

C'est le **prologue standard** de `_start` : il prépare les arguments puis appelle
`__libc_start_main`. Le premier argument de cette fonction, passé dans **`rdi`**, est l'adresse de
`main`. Ici : `0x1179`.

La preuve se fait sur le binaire non strippé, qui porte encore les noms :

```text
$ nm hello | grep -E ' _start$| main$'
0000000000001090 T _start
0000000000001179 T main
```

`0x1179` : exactement la valeur chargée par `lea rdi`. C'est la technique à retenir — elle
fonctionne sur **tout** binaire ELF dynamique compilé par gcc ou clang.

### Les trois outils, dans l'ordre

**`radare2` automatise ce raisonnement.** `aaa` reconnaît le motif `__libc_start_main` et nomme
`main` tout seul :

```text
$ r2 -2 -q -c 'aaa; afl' hello_s | head -8
0x00001030    1      6 sym.imp.puts
0x00001040    1      6 sym.imp.printf
0x00001050    1      6 sym.imp.strcspn
0x00001060    1      6 sym.imp.fgets
0x00001070    1      6 sym.imp.strcmp
0x00001080    1      6 sym.imp.__cxa_finalize
0x00001090    1     33 entry0
0x00001179    7    156 main
```

Et `entry0` montre le lien explicitement :

```text
$ r2 -2 -q -c 'aaa; s entry0; pdf' hello_s | tail -3
│           0x000010a2      31c9           xor ecx, ecx
│           0x000010a4      488d3dce00..   lea rdi, [main]             ; 0x1179
└           0x000010ab      ff150f2f0000   call qword [reloc.__libc_start_main] ; [0x3fc0:8]=0
```

**`gdb` refait le chemin à la main.** Sur un PIE, l'adresse de chargement sous `gdb` est
`0x555555554000` (ASLR désactivé par défaut). On casse à l'entrée, on avance jusqu'à l'appel, on
lit `rdi` :

```bash
gdb -q -batch -ex 'b *(0x555555554000+0x1090)' -ex 'run < in.txt' \
    -ex 'si 10' -ex 'x/i $pc' -ex 'p/x $rdi' -ex 'x/3i $rdi' ./hello_s 2>/dev/null
```

```text
Breakpoint 1 at 0x555555555090

Breakpoint 1, 0x0000555555555090 in ?? ()
0x00005555555550ab in ?? ()
=> 0x5555555550ab:      call   *0x2f0f(%rip)        # 0x555555557fc0
$1 = 0x555555555179
   0x555555555179:      push   %rbp
   0x55555555517a:      mov    %rsp,%rbp
   0x55555555517d:      sub    $0x20,%rsp
```

`$rdi` vaut `0x555555555179`, et `x/3i $rdi` affiche le prologue d'une fonction C (`push rbp` /
`mov rsp,rbp` / `sub rsp,N`) : on est dans `main`. Notez les `?? ()` : `gdb` n'a aucun nom à
donner, c'est normal et sans conséquence.

| Question | Outil | Réponse |
| --- | --- | --- |
| Où commence le programme ? | `readelf -h` | `Entry point address: 0x1090` |
| Où est `main` ? | `objdump` / `gdb` | argument `rdi` de `__libc_start_main` |
| Et si je ne veux pas calculer ? | `r2 -c 'aaa; afl'` | `main` est déjà nommé |

## 2. Statique et strippé : quand presque tout disparaît

Un binaire `-static -s` est le cas le plus pauvre : pas de symboles, et la libc est **dedans**.

```text
$ file hello_ss
hello_ss:  ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, BuildID[sha1]=ddfca011a75d1848d850313828aee38df4b78a7e, for GNU/Linux 3.2.0, stripped
```

### Deux outils tombent en panne, un résiste

```text
$ echo admin | ltrace -s 30 ./hello_ss
Couldn't find .dynsym or .dynstr in "/proc/29884/exe"
```

`ltrace` s'appuie sur `.dynsym` pour intercepter les appels de bibliothèque. En statique, il n'y a
plus de bibliothèque : la trace est vide. `strace`, lui, regarde le noyau et continue de
fonctionner — les appels système existent toujours.

```text
$ echo admin | strace -o /tmp/st.txt -e trace=read,write ./hello_ss > /dev/null
$ grep -E 'read\(0|write\(1' /tmp/st.txt
read(0, "admin\n", 4096)                = 6
write(1, "nom : bienvenue\n", 16)       = 16
```

Deux détails qui surprennent :

- `read(0, …, 4096)` : `fgets` lit par **blocs** de 4096 octets dans le tampon de `FILE *`, pas
  caractère par caractère.
- un seul `write` de 16 octets : `stdout` n'est pas un terminal, donc stdio est en mode
  **entièrement tamponné** et fusionne `"nom : "` et `"bienvenue\n"` avant d'écrire. `stdbuf -o0`
  ne change rien ici : il repose sur `LD_PRELOAD`, inopérant sur un binaire statique.

### `radare2` : 569 fonctions, aucune n'est nommée

```text
$ r2 -2 -q -c 'aaa; afl' hello_ss | wc -l
569
$ r2 -2 -q -c 'aaa; afl~sym.imp' hello_ss | wc -l
0
```

569 fonctions, zéro `sym.imp.*` : les appels à `printf` ou `strcmp` pointent maintenant vers du
code **dans** le binaire, que r2 nomme `fcn.0040b340` par exemple. Sur un `pdf`, on lit donc
`call fcn.0040b340` là où le binaire dynamique affichait `call sym.imp.puts`.

### La chaîne comme point d'entrée

Sans nom de fonction, on part du **texte**. `iz` liste les chaînes de `.rodata` avec leur adresse ;
le filtre `~004770` garde celles du voisinage de notre zone :

```text
$ r2 -2 -q -c 'aaa; iz~004770' hello_ss
0    0x0007700e 0x0047700e 7   9    .rodata      ascii   @@nom :
1    0x00077019 0x00477019 5   6    .rodata      ascii   admin
2    0x0007701f 0x0047701f 9   10   .rodata      ascii   bienvenue
3    0x00077029 0x00477029 7   8    .rodata      ascii   inconnu
```

Puis `axt` (cross-références vers) donne le code qui la lit :

```text
$ r2 -2 -q -c 'aaa; axt @ 0x477010' hello_ss
main 0x40178d [DATA:r--] lea rax, [0x00477010]
```

`aaa` a quand même reconnu `main` (motif `__libc_start_main`), mais c'est `axt` qui donne
**l'instruction exacte** : `0x40178d` charge l'adresse de `"nom : "`, trois instructions avant le
`call` du `printf`. Sans cette référence, les 569 fonctions seraient interchangeables.

### Deux artefacts à connaître

**`@@` devant la chaîne.** Les octets réels autour de `0x47700e` :

```text
$ r2 -2 -q -c 'px 48 @ 0x477000' hello_ss
- offset -   0 1  2 3  4 5  6 7  8 9  A B  C D  E F  0123456789ABCDEF
0x00477000  0100 0200 0000 0000 0000 803f 0000 4040  ...........?..@@
0x00477010  6e6f 6d20 3a20 000a 0061 646d 696e 0062  nom : ...admin.b
0x00477020  6965 6e76 656e 7565 0069 6e63 6f6e 6e75  ienvenue.inconnu
```

Les deux `@` sont la fin d'une constante flottante voisine : `00 00 40 40` = `3.0f`. `0x40` est un
caractère imprimable, donc `iz` (comme `strings`) démarre la chaîne deux octets trop tôt. La
chaîne utile commence bien à `0x477010` (`nom : `).

**Le bruit de la libc.** Sur 1516 chaînes, la quasi-totalité vient de la libc liée en dur
(`chunksize_nomask (p) == (0 | PREV_INUSE)`, messages d'assertion, noms de locale…). Le filtrage
utile reste le même qu'en dynamique :

```bash
# chaînes qui ressemblent à un chemin, une URL, un message applicatif
r2 -2 -q -c 'aaa; iz' hello_ss | grep -E '(/proc|/etc|http|nom|admin|cle|flag|pass)'
# fonctions : on ne garde que ce qui est joignable depuis l'entrée
r2 -2 -q -c 'aaa; afl~main' hello_ss
```

| Situation | Ce qui marche | Ce qui ne marche plus |
| --- | --- | --- |
| `-s` (dynamique) | `nm -D`, `ltrace`, `sym.imp.*` | `nm`, noms de fonctions internes |
| `-static -s` | `strace`, `iz` + `axt`, `afl` | `ltrace`, `nm -D` utile, `sym.imp.*` |
| Les deux | `objdump`, `readelf`, `r2`, `gdb` | — |

## 3. Anti-debug sous Linux

Un crackme protégé commence souvent par demander au système : « suis-je en train d'être
traqué ? ». Deux moyens classiques, tous les deux en CLI.

```bash
cat > anti1.c <<'EOF'
#include <stdio.h>
#include <string.h>
#include <sys/ptrace.h>

int main(void) {
    char nom[32];

    if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) {
        puts("debug detecte");
        return 1;
    }

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    puts(strcmp(nom, "admin") == 0 ? "bienvenue" : "inconnu");
    return 0;
}
EOF

cat > anti2.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int debogue(void) {
    FILE *f = fopen("/proc/self/status", "r");
    char ligne[256];
    int pid = 0;

    if (!f)
        return 0;
    while (fgets(ligne, sizeof ligne, f)) {
        if (strncmp(ligne, "TracerPid:", 10) == 0) {
            pid = atoi(ligne + 10);
            break;
        }
    }
    fclose(f);
    return pid != 0;
}

int main(void) {
    char nom[32];

    if (debogue()) {
        puts("debug detecte");
        return 1;
    }

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    puts(strcmp(nom, "admin") == 0 ? "bienvenue" : "inconnu");
    return 0;
}
EOF

gcc -O0 -s -o anti1 anti1.c
gcc -O0 -s -o anti2 anti2.c
```

Hors debugger, les deux fonctionnent normalement :

```text
$ echo admin | ./anti1
nom : bienvenue
$ echo admin | ./anti2
nom : bienvenue
```

Sous `gdb`, les deux refusent :

```text
$ echo admin | gdb -q -batch -ex 'run < in.txt' ./anti1 2>/dev/null | tail -2
debug detecte
[Inferior 1 (process 37289) exited with code 01]
$ echo admin | gdb -q -batch -ex 'run < in.txt' ./anti2 2>/dev/null | tail -2
debug detecte
[Inferior 1 (process 37303) exited with code 01]
```

### 3.1 Pourquoi `PTRACE_TRACEME` ne se contente pas de poser une question

`PTRACE_TRACEME` ne réussit que si le processus **n'est pas déjà tracé** : il déclare « je veux être
tracé par mon père ». Si un debugger est déjà attaché, le noyau répond `EPERM` et l'appel renvoie
`-1`.

Le piège : l'appel **établit la relation de traçage**. Le programme devient donc tracé par son
père, et `TracerPid` cesse d'être nul. Un programme qui fait `TRACEME` **puis** lit `TracerPid`
se détecte lui-même.

```bash
cat > tp.c <<'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/ptrace.h>

static void affiche(const char *quand) {
    FILE *f = fopen("/proc/self/status", "r");
    char l[256];
    if (!f)
        return;
    while (fgets(l, sizeof l, f))
        if (!strncmp(l, "TracerPid:", 10)) {
            l[strcspn(l, "\n")] = 0;
            printf("%-18s %s (moi: %d)\n", quand, l, getpid());
            break;
        }
    fclose(f);
}

int main(void) {
    affiche("avant TRACEME:");
    printf("ptrace(TRACEME) = %ld\n", ptrace(PTRACE_TRACEME, 0, 0, 0));
    affiche("apres TRACEME:");
    return 0;
}
EOF

gcc -O0 -o tp tp.c && ./tp
```

```text
avant TRACEME:     TracerPid:   0 (moi: 29693)
ptrace(TRACEME) = 0
apres TRACEME:     TracerPid:   201 (moi: 29693)
```

Le même processus, avant et après : `0`, puis `201` (le shell). **L'ordre des deux tests compte.**
Un anti-debug correct lit `TracerPid` d'abord, puis tente `TRACEME` ; inversé, le second test est
toujours vrai et le programme se bloque lui-même.

### 3.2 Contournement 1 : `gdb`, sans toucher au binaire

Le premier réflexe : voir l'anti-debug, puis lui **mentir**. Sur `anti1`, la preuve du refus :

```text
$ gdb -q -batch -ex 'run < in.txt' ./anti1 2>/dev/null | tail -2
debug detecte
[Inferior 1 (process 33153) exited with code 01]
```

`catch syscall ptrace` arrête le programme **à l'entrée et à la sortie** de l'appel système :

```bash
gdb -q -batch -ex 'catch syscall ptrace' -ex 'run < in.txt' \
    -ex 'continue' -ex 'p (long)$rax' -ex 'continue' ./anti1 2>/dev/null
```

```text
Catchpoint 1 (syscall 'ptrace' [101])

Catchpoint 1 (call to syscall ptrace), 0x00007ffff7ed8608 in ptrace () from /usr/lib/x86_64-linux-gnu/libc.so.6

Catchpoint 1 (returned from syscall ptrace), 0x00007ffff7ed8608 in ptrace () from /usr/lib/x86_64-linux-gnu/libc.so.6
$1 = -1
debug detecte
[Inferior 1 (process 33166) exited with code 01]
```

`$1 = -1` : c'est `EPERM`, la réponse du noyau quand le processus est déjà tracé. Le programme ne
teste que cette valeur. On la remplace à la sortie de l'appel :

```bash
gdb -q -batch -ex 'catch syscall ptrace' -ex 'run < in.txt' \
    -ex 'continue' -ex 'set $rax = 0' -ex 'continue' ./anti1 2>/dev/null
```

```text
Catchpoint 1 (syscall 'ptrace' [101])

Catchpoint 1 (call to syscall ptrace), 0x00007ffff7ed8608 in ptrace () from /usr/lib/x86_64-linux-gnu/libc.so.6

Catchpoint 1 (returned from syscall ptrace), 0x00007ffff7ed8608 in ptrace () from /usr/lib/x86_64-linux-gnu/libc.so.6
nom : bienvenue
[Inferior 1 (process 33178) exited normally]
```

Deux `continue` : le premier va de l'entrée à la sortie de l'appel système, le second repart. Entre
les deux, `set $rax = 0` réécrit la valeur de retour. Le programme croit que `ptrace` a réussi.

`anti2` ne fait aucun `ptrace` : `catch syscall ptrace` ne déclencherait rien. La preuve du
mécanisme est dans le status du processus, que `gdb` sait lire avec `info proc status` :

```bash
gdb -q -batch -ex 'break fopen' -ex 'run < in.txt' -ex 'info proc status' ./anti2 2>/dev/null
```

```text
Name:   anti2
TracerPid:      33207
```

`TracerPid` n'est pas nul : `gdb` est bien le traceur. Pour passer, on n'a pas besoin de connaître
le nom `debogue` — il suffit de casser sur `fopen`, une fonction **de la libc**, donc toujours
nommée, et de remonter de deux crans :

```bash
gdb -q -batch -ex 'break fopen' -ex 'run < in.txt' \
    -ex 'finish' -ex 'bt 2' -ex 'finish' -ex 'set $eax = 0' -ex 'continue' ./anti2 2>/dev/null
```

```text
Breakpoint 1 at 0x10a0

Breakpoint 1, 0x00007ffff7e49690 in fopen64 () from /usr/lib/x86_64-linux-gnu/libc.so.6
0x00005555555551dd in ?? ()
#0  0x00005555555551dd in ?? ()
#1  0x0000555555555272 in ?? ()
0x0000555555555272 in ?? ()
nom : bienvenue
[Inferior 1 (process 33203) exited normally]
```

Lecture : le premier `finish` sort de `fopen` et retombe dans `debogue` (`0x…51dd`) ; le second sort
de `debogue` et retombe dans `main` (`0x…5272`). À cet instant, **`eax` porte la valeur de retour**
de `debogue` : `set $eax = 0` et le programme est convaincu qu'il n'est pas tracé. Les `?? ()`
confirment que le binaire est strippé ; `bt` fonctionne quand même, sur les adresses.

> **Ce que ce conteneur autorise.** `cat /proc/sys/kernel/yama/ptrace_scope` vaut `1` : seul le
> père peut tracer. `gdb` lance le programme lui-même, il est donc le père — tout fonctionne.
> En revanche `hbreak` répond `No hardware breakpoint support in the target.`, alors que `watch`
> crée bien un « Hardware watchpoint ». Les points d'arrêt **logiciels** restent la solution
> portable.

### 3.3 Contournement 2 : `LD_PRELOAD`

Pas besoin de debugger si on peut remplacer la fonction. `LD_PRELOAD` charge une bibliothèque
avant les autres ; ses symboles passent devant ceux de la libc.

```bash
cat > no_ptrace.c <<'EOF'
/* LD_PRELOAD : neutralise ptrace() pour tout programme dynamique */
long ptrace(int request, ...) {
    (void)request;
    return 0;
}
EOF

gcc -shared -fPIC -O2 -o no_ptrace.so no_ptrace.c
```

**Le piège à éviter.** Si on exporte `LD_PRELOAD` avant de lancer `gdb`, c'est `gdb` lui-même qui
est préchargé : ses propres appels `ptrace` partent dans le vide et il ne trace plus rien.

```text
$ LD_PRELOAD=./no_ptrace.so gdb -q -batch -ex 'break main' -ex 'run < in.txt' -ex 'bt 1' ./anti1
Make breakpoint pending on future shared library load? (y or [n]) [answered N; input not from terminal]
nom : bienvenue
```

Le point d'arrêt n'est même pas posé. Le programme affiche `bienvenue` parce qu'il **n'est plus
tracé du tout** : ce n'est pas le contournement, c'est la suppression du debugger.

**La bonne méthode** : demander à `gdb` de précharger la bibliothèque **pour le programme
seulement**, via `set exec-wrapper`.

```bash
gdb -q -batch -ex 'set exec-wrapper env LD_PRELOAD=./no_ptrace.so' \
    -ex 'run < in.txt' ./anti1
```

```text
nom : bienvenue
[Inferior 1 (process 33512) exited normally]
```

Cette fois `gdb` trace normalement (il affiche le code de sortie), le programme est bien sous
debugger, et il ne le sait pas : `ptrace` a répondu `0` sans appeler le noyau.

Trois limites à connaître :

- **binaire statique** : `LD_PRELOAD` ne s'applique pas, il n'y a pas d'édition de liens dynamique ;
- **appel direct au noyau** (`syscall(SYS_ptrace, …)` en assembleur en ligne) : le PLT est contourné,
  l'interposition ne voit rien ;
- `anti2` lit un **fichier** : interposer `ptrace` ne suffit pas, il faudrait interposer `fopen` et
  renvoyer `NULL` pour `/proc/self/status`.

### 3.4 Contournement 3 : patcher le binaire

Le plus solide, parce qu'il ne dépend ni du debugger ni du chargeur. On patche une **copie** (voir
[4.6](06-decompilation-cli-patching-z3.md) pour les règles de taille).

Sur `anti1`, le test est un simple saut :

```text
│           0x000011aa      e8d1feffff     call sym.imp.ptrace
│           0x000011af      4883f8ff       cmp rax, 0xffffffffffffffff
│       ┌─< 0x000011b3      7519           jne 0x11ce
```

`75 19` (`jne`) devient `eb 19` (`jmp`) : le saut est inconditionnel, la détection est morte.

```bash
cp anti1 anti1_patch
r2 -2 -q -w -c 'wx eb19 @ 0x11b3' anti1_patch
objdump -d -M intel --start-address=0x11af --stop-address=0x11b6 anti1_patch
```

```text
11af:       48 83 f8 ff             cmp    rax,0xffffffffffffffff
11b3:       eb 19                   jmp    11ce <__cxa_finalize@plt+0x13e>
11b5:       48                      rex.W
```

```text
$ gdb -q -batch -ex 'run < in.txt' ./anti1_patch 2>/dev/null | tail -2
nom : bienvenue
[Inferior 1 (process 33267) exited normally]
```

Sur `anti2`, il n'y a pas de test à retourner : c'est un **appel de fonction** dont on jette le
résultat. On remplace `call debogue` (5 octets) par `xor eax,eax` + trois `nop` :

```text
│           0x0000126d      e847ffffff     call fcn.000011b9
│           0x00001272      85c0           test eax, eax
│       ┌─< 0x00001274      7419           je 0x128f
```

```bash
cp anti2 anti2_patch
r2 -2 -q -w -c 'wx 31c0909090 @ 0x126d' anti2_patch
```

```text
$ echo admin | ./anti2_patch
nom : bienvenue
$ gdb -q -batch -ex 'run < in.txt' ./anti2_patch 2>/dev/null | tail -2
nom : bienvenue
[Inferior 1 (process 33301) exited normally]
```

Le patch tient **hors** debugger et **sous** debugger : c'est la différence avec les deux
contournements précédents, qui ne valent que pendant la session.

| Méthode | Marche sous gdb | Marche hors gdb | Limite |
| --- | --- | --- | --- |
| `catch syscall` + `$rax = 0` | oui | non | dépend du debugger |
| `LD_PRELOAD` | oui | oui | binaire dynamique, appels via PLT |
| Patch `r2 -w` | oui | oui | il faut localiser le test |

## 4. Obfuscation : chaînes et code mort

Deux techniques très courantes pour cacher une chaîne attendue : la **chiffrer** et la déchiffrer
en mémoire, ou la **construire octet par octet** sur la pile. Une troisième consiste à semer de
**faux drapeaux** dans du code jamais exécuté. Dans les trois cas, `strings` ment.

### 4.1 XOR en mémoire

```bash
cat > xorstr.c <<'EOF'
#include <stdio.h>
#include <string.h>

static const unsigned char enc[] = { 0x3c, 0x7c, 0x2c, 0x3d, 0x7c, 0x3b, 0x00 };

int main(void) {
    char nom[32];
    char clair[16];
    size_t i;

    for (i = 0; i < sizeof enc - 1; i++)
        clair[i] = (char)(enc[i] ^ 0x4f);
    clair[sizeof enc - 1] = '\0';

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    puts(strcmp(nom, clair) == 0 ? "bienvenue" : "inconnu");
    return 0;
}
EOF

gcc -O0 -s -o xorstr xorstr.c
```

```text
$ echo 's3cr3t' | ./xorstr
nom : bienvenue
$ strings -a xorstr | grep -c s3cr3t
0
$ r2 -2 -q -c 'iz~s3cr3t' xorstr | wc -l
0
```

Le clair `s3cr3t` n'apparaît nulle part. On ne va pas réécrire la boucle XOR : on va **attendre**
que le programme l'ait fait. Au moment de la comparaison, les deux chaînes sont en mémoire.

```bash
printf 'mauvais\n' > in2.txt
gdb -q -batch -ex 'break strcmp' -ex 'run < in2.txt' \
    -ex 'x/s $rdi' -ex 'x/s $rsi' -ex 'x/8bx $rsi' ./xorstr 2>/dev/null
```

```text
Breakpoint 1 at 0x1070

Breakpoint 1, 0x00007ffff7f40040 in ?? () from /usr/lib/x86_64-linux-gnu/libc.so.6
0x7fffffffd3b0: "mauvais"
0x7fffffffd3a0: "s3cr3t"
0x7fffffffd3a0: 0x73    0x33    0x63    0x72    0x33    0x74    0x00    0x00
```

- `$rdi` : ce que j'ai tapé ;
- `$rsi` : la chaîne **déchiffrée**, sur la pile ;
- `x/8bx` : les octets, `73 33 63 72 33 74` = `s3cr3t`.

`strcmp` est un symbole de la libc : ce point d'arrêt fonctionne même sur un binaire `-s` et même
si la fonction appelante n'a pas de nom.

### 4.2 Stack strings

La variante sans table : chaque octet est écrit individuellement. Rien à déchiffrer, mais rien à
lire non plus dans le fichier.

```bash
cat > stackstr.c <<'EOF'
#include <stdio.h>
#include <string.h>

int main(void) {
    char nom[32];
    char attendu[8];

    attendu[0] = 's';
    attendu[1] = '3';
    attendu[2] = 'c';
    attendu[3] = 'r';
    attendu[4] = '3';
    attendu[5] = 't';
    attendu[6] = '!';
    attendu[7] = '\0';

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    puts(strcmp(nom, attendu) == 0 ? "bienvenue" : "inconnu");
    return 0;
}
EOF

gcc -O0 -s -o stackstr stackstr.c
```

```text
$ echo 's3cr3t!' | ./stackstr
nom : bienvenue
$ strings -a stackstr | grep -c s3cr3t
0
```

```bash
gdb -q -batch -ex 'break strcmp' -ex 'run < in2.txt' -ex 'x/s $rsi' ./stackstr 2>/dev/null
```

```text
Breakpoint 1 at 0x1070

Breakpoint 1, 0x00007ffff7f40040 in ?? () from /usr/lib/x86_64-linux-gnu/libc.so.6
0x7fffffffd3b8: "s3cr3t!"
```

Même méthode, même résultat : la chaîne est reconstruite sur la pile, il suffit de regarder au bon
moment.

### 4.3 Code mort et faux drapeau

Variante inverse : la chaîne est **en clair**, bien visible dans `strings`, mais dans une branche
qui ne s'exécute jamais. Le piège vise le joueur pressé.

```bash
cat > dead.c <<'EOF'
#include <stdio.h>
#include <string.h>

static volatile int interrupteur = 0;   /* jamais mis a 1 */

int main(void) {
    char nom[32];

    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    if (interrupteur) {                 /* branche morte : jamais executee */
        if (strcmp(nom, "NOOB{ceci_est_un_piege}") == 0)
            puts("bravo");
        else
            puts("non");
        return 0;
    }

    puts(strcmp(nom, "admin") == 0 ? "bienvenue" : "inconnu");
    return 0;
}
EOF

gcc -O2 -s -o dead dead.c
printf 'NOOB{ceci_est_un_piege}\n' > in3.txt
```

```text
$ strings -a dead | grep -c 'NOOB'
1
$ echo 'NOOB{ceci_est_un_piege}' | ./dead
nom : inconnu
$ echo admin | ./dead
nom : bienvenue
```

Le drapeau est là, et il ne sert à rien. `volatile` empêche le compilateur de supprimer la
branche : elle reste dans le binaire, lisible et crédible.

La preuve par le code : la condition est une simple lecture d'un global.

```text
$ objdump -d -M intel dead | grep -A3 -m1 'mov.*eax.*rip'
    10cf:       8b 05 77 2f 00 00       mov    eax,DWORD PTR [rip+0x2f77]        # 404c <stdin@GLIBC_2.2.5+0xc>
    10d5:       85 c0                   test   eax,eax
    10d7:       75 2e                   jne    1107 <__cxa_finalize@plt+0x87>
    10d9:       48 89 e7                mov    rdi,rsp
```

```text
$ r2 -2 -q -c 'aaa; iz~NOOB' dead
3   0x0000201f 0x0000201f 23  24   .rodata ascii NOOB{ceci_est_un_piege}
$ r2 -2 -q -c 'aaa; axt @ 0x201f' dead
main 0x1107 [STRN:r--] lea rsi, str.NOOBceci_est_un_piege
```

`0x1107` est exactement la cible du `jne` : la chaîne n'est chargée que si le global est non nul.
Et `gdb` le confirme : même en tapant exactement le faux drapeau, un seul `puts` est atteint, et
`$rdi` pointe sur `"inconnu"`.

```text
$ gdb -q -batch -ex 'break puts' -ex 'run < in3.txt' -ex 'x/s $rdi' ./dead 2>/dev/null
Breakpoint 1 at 0x1030
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/usr/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, 0x00007ffff7e4b2c0 in puts () from /usr/lib/x86_64-linux-gnu/libc.so.6
0x55555555600e: "inconnu"
```

> **Réflexe.** Un drapeau trouvé dans `strings` n'est pas une victoire : c'est une **hypothèse**.
> On la teste (`echo 'NOOB{...}' | ./binaire`) avant de l'écrire dans un writeup. C'est aussi
> pourquoi la phase 1 de la méthodologie ([4.8](08-methodologie-crackme-et-autres-formats.md))
> finit par une exécution et pas par un `strings`.

> **La règle.** Une chaîne obfusquée doit **forcément** exister en clair à un instant : au moment
> de la comparaison, ou dans un buffer avant `write`. On ne casse pas l'obfuscation, on choisit le
> bon point d'arrêt. `break strcmp`, `break strncmp`, `break memcmp`, `break puts`, `break write` :
> une fonction de la libc est toujours nommée, même dans un binaire strippé.

## 5. Packer : UPX et signature altérée

Un packer compresse l'exécutable et ajoute une petite routine de décompression, le **stub**. Le
fichier sur disque ne contient presque plus le code d'origine.

```bash
gcc -O0 -o big hello.c
upx -9 -o hello.packed big
```

```text
$ ls -l big hello.packed | awk '{print $5, $9}'
16200 big
6168 hello.packed
$ file hello.packed
hello.packed: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), statically linked, no section header
```

`file` se trompe : il annonce « statically linked » parce que le binaire n'a **plus de section
headers** (`readelf -h` donne `Start of section headers: 0`) et plus d'interpréteur lisible. Les
en-têtes de programme, eux, suffisent au noyau pour l'exécuter.

### Reconnaître UPX et le défaire

```text
$ strings -a hello.packed | grep -i -m3 upx
UPX!
$Info: This file is packed with the UPX executable packer http://upx.sf.net $
$Id: UPX 4.24 Copyright (C) 1996-2024 the UPX Team. All Rights Reserved. $
```

```text
$ upx -d -o hello.unpacked hello.packed
        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
     25235 <-      6168   24.44%   linux/amd64   hello.unpacked

Unpacked 1 file.
```

Le `25235` est la taille **décompressée en mémoire** ; le fichier écrit fait bien 16200 octets et
est identique à l'original (`cmp big hello.unpacked` ne signale rien).

### Quand `upx -d` refuse : signature modifiée

C'est le premier contournement anti-UPX : altérer le marqueur pour casser l'outil. Le marqueur
`UPX!` apparaît quatre fois :

```text
$ grep -abo 'UPX!' hello.packed
236:UPX!
3106:UPX!
6124:UPX!
6132:UPX!
```

- `236` : le `l_info`, en tête (après les en-têtes ELF) ;
- `6132` : le `p_info`, en queue — c'est la **dernière** occurrence, à 36 octets de la fin.

```text
$ xxd -s 6112 -l 48 hello.packed
000017e0: 1a01 3f09 0000 00ff 0000 0000 5550 5821  ..?.........UPX!
000017f0: 0000 0000 5550 5821 0e16 0209 b856 fc37  ....UPX!.....V.7
```

On casse chaque marqueur dans une copie, avec Python :

```python
import pathlib

src = pathlib.Path("hello.packed").read_bytes()
for nom, off in [("corrupt_tail.packed", 6132), ("corrupt_head.packed", 236)]:
    d = bytearray(src)
    d[off:off + 4] = b"XXXX"
    pathlib.Path(nom).write_bytes(d)
```

Les deux erreurs sont **différentes** :

```text
$ upx -d -o t1 corrupt_tail.packed
        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
upx: corrupt_tail.packed: NotPackedException: not packed by UPX

Unpacked 0 files.

$ upx -d -o t2 corrupt_head.packed
        File size         Ratio      Format      Name
   --------------------   ------   -----------   -----------
upx: corrupt_head.packed: CantUnpackException: l_info corrupted

Unpacked 1 file: 0 ok, 1 error.
```

`NotPackedException` (marqueur de queue) : UPX ne reconnaît même pas un fichier packé.
`CantUnpackException: l_info corrupted` (marqueur de tête) : il reconnaît le format mais l'en-tête
est incohérent. Deux messages, deux endroits.

**Le point important** : le binaire **fonctionne toujours**. Le stub n'a pas besoin de la
signature pour décompresser, seulement UPX.

```text
$ chmod +x corrupt_tail.packed && echo admin | ./corrupt_tail.packed
nom : bienvenue
```

### Réparer, puis décompresser

Le marqueur de queue est à position fixe depuis la fin. On le remet, on rend le bit exécutable
(que Python n'a pas conservé), et `upx -d` repart :

```python
data = bytearray(open("corrupt_tail.packed", "rb").read())
print("magic a -36 :", data[-36:-32])
data[-36:-32] = b"UPX!"
open("repare.packed", "wb").write(data)
print("magic apres :", data[-36:-32])
```

```text
magic a -36 : bytearray(b'XXXX')
magic apres : bytearray(b'UPX!')
```

```text
$ chmod +x repare.packed
$ upx -d -o repare.orig repare.packed
     25235 <-      6168   24.44%   linux/amd64   repare.orig

Unpacked 1 file.
$ chmod +x repare.orig && echo admin | ./repare.orig
nom : bienvenue
```

> **Note pour les writeups.** Si le marqueur de queue a été déplacé (packer modifié), on le
> retrouve avec `grep -abo 'UPX!'` : c'est la dernière occurrence, et le `p_info` a une taille
> connue (36 octets ici pour UPX 4.x sur ELF). Si le stub a été réécrit, `upx -d` échouera quoi
> qu'on fasse : il faut alors dumper la mémoire du processus après décompression
> (`gcore`, puis `objdump` sur le dump).

## 6. Exercice guidé : crackme anti-debug et chaîne chiffrée

Ce programme cumule tout le chapitre : strippé, deux anti-debug (dans le bon ordre), une clé XORée
et un message de succès. Objectif : retrouver la clé et obtenir `bravo`.

```bash
cat > crackme.c <<'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>

static int trace_pid(void) {
    FILE *f = fopen("/proc/self/status", "r");
    char ligne[256];
    int pid = 0;

    if (!f)
        return 0;
    while (fgets(ligne, sizeof ligne, f)) {
        if (strncmp(ligne, "TracerPid:", 10) == 0) {
            pid = atoi(ligne + 10);
            break;
        }
    }
    fclose(f);
    return pid;
}

static int piege(void) {
    if (trace_pid() != 0)
        return 1;
    return ptrace(PTRACE_TRACEME, 0, 0, 0) == -1;
}

int main(void) {
    static const unsigned char enc[] = {
        0x33, 0x5b, 0x19, 0x46, 0x5f, 0x0a, 0x05, 0x1f, 0x5a, 0x00
    };
    char cle[16];
    char nom[64];
    size_t i;

    if (piege()) {
        puts("non.");
        return 1;
    }

    for (i = 0; i < sizeof enc - 1; i++)
        cle[i] = (char)(enc[i] ^ 0x6b);
    cle[sizeof enc - 1] = '\0';

    printf("cle : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;

    puts(strcmp(nom, cle) == 0 ? "bravo" : "non.");
    return 0;
}
EOF
```

Questions, dans l'ordre :

1. Sans debugger, quel message obtient-on avec `X0r-4ant1` ? Pourquoi `strings` ne dit-il rien ?
2. Sous `gdb`, le programme s'arrête-t-il sur `cle :` ? Quel message, quel code de sortie ?
3. Où se trouve l'appel à la fonction anti-debug dans `main` ? À quelle adresse ?
4. Quel patch de 5 octets neutralise cet appel, et pourquoi exactement 5 octets ?
5. Une fois patché, comment lire la clé sans réécrire le XOR ?
6. La clé trouvée est-elle la seule ? Pourquoi ?

<details>
<summary>Correction détaillée</summary>

**Étape 0 — compiler.**

```bash
gcc -O0 -s -o crackme crackme.c
```

**Étape 1 — comportement de base.**

```text
$ echo 'X0r-4ant1' | ./crackme
cle : bravo
$ strings -a crackme | grep -c 'X0r-4ant1'
0
```

Le programme accepte la clé, mais elle n'existe pas en clair : elle est XORée avec `0x6b`
(`0x33 ^ 0x6b = 0x58` = `'X'`).

**Étape 2 — sous `gdb`, refus immédiat.**

```text
$ gdb -q -batch -ex 'run < in.txt' ./crackme 2>/dev/null | tail -2
non.
[Inferior 1 (process 33953) exited with code 01]
```

Pas de `cle :` : le programme s'arrête avant, dans `piege()`.

**Étape 3 — localiser l'appel.**

```text
$ r2 -2 -q -c 'aaa; s main; pdf' crackme | sed -n '5,8p'
│           0x000012ad      4889e5         mov rbp, rsp
│           0x000012b0      4883ec60       sub rsp, 0x60
│           0x000012b4      e8b5ffffff     call fcn.0000126e
│           0x000012b9      85c0           test eax, eax
```

`0x12b4` : `call fcn.0000126e`, c'est-à-dire `piege()`. Le `test eax, eax` qui suit confirme que
le résultat est un booléen.

**Étape 4 — patcher une copie.**

```bash
cp crackme crackme_patch
r2 -2 -q -w -c 'wx 31c0909090 @ 0x12b4' crackme_patch
```

`31 c0` = `xor eax, eax` (2 octets, `eax = 0`), puis `90 90 90` = trois `nop` : 5 octets en tout,
la taille exacte du `call`. Le programme croit que `piege()` a renvoyé 0.

**Étape 5 — lire la clé au bon moment.**

```bash
gdb -q -batch -ex 'break strcmp' -ex 'run < in2.txt' -ex 'x/s $rdi' -ex 'x/s $rsi' ./crackme_patch 2>/dev/null
```

```text
Breakpoint 1 at 0x1090

Breakpoint 1, 0x00007ffff7f40040 in ?? () from /usr/lib/x86_64-linux-gnu/libc.so.6
0x7fffffffd0c0: "mauvais"
0x7fffffffd100: "X0r-4ant1"
```

**Étape 6 — vérifier.**

```text
$ echo 'X0r-4ant1' | ./crackme_patch
cle : bravo
```

**Réponse 6.** Ici la clé est unique : 9 octets de clé pour 9 octets de table, XOR avec une
constante, c'est une bijection. Une validation plus lâche (somme, inégalités) laisserait plusieurs
solutions — voir [4.6](06-decompilation-cli-patching-z3.md).

**Variante sans patch.** On peut rester sous `gdb` et mentir deux fois : `break fopen` + deux
`finish` + `set $eax = 0` pour le test `TracerPid`, puis `catch syscall ptrace` + `set $rax = 0`
pour `TRACEME`. Six commandes au lieu d'un patch de 5 octets — d'où le choix du patch.

</details>

## 7. Ce que je retiens

- Un binaire `-s` garde son **point d'entrée** et `.dynsym` : `readelf -h`, `nm -D`, et l'argument
  `rdi` de `__libc_start_main` donnent `main` sans symboles.
- `r2 -c 'aaa; afl'` retrouve `main` tout seul ; `axt` passe d'une chaîne au code qui la lit.
- En **statique**, `ltrace` est aveugle (pas de `.dynsym`), mais `strace` et `iz` + `axt`
  fonctionnent. Le bruit de la libc se filtre, il ne se lit pas.
- `PTRACE_TRACEME` n'est pas une question : il **établit** le traçage, donc `TracerPid` devient non
  nul. L'ordre des deux tests décide de leur sens.
- Sous `gdb`, `catch syscall ptrace` + `set $rax = 0` annule le résultat du syscall ; `break fopen`
  + `finish` ×2 + `set $eax = 0` annule le résultat d'une fonction strippée.
- `LD_PRELOAD` doit viser **le programme**, pas `gdb` : `set exec-wrapper` est l'outil juste.
- Un **patch** est le seul contournement qui survit à la fin de la session.
- Une chaîne obfusquée existe en clair au moment de la comparaison : `break strcmp` + `x/s $rsi`
  suffit, sans réécrire le déchiffrement.
- `upx -d` refuse un marqueur altéré (`NotPackedException`, `l_info corrupted`) alors que le
  binaire continue de tourner : la signature sert à l'outil, pas au stub.

| Symptôme | Cause probable | Outil |
| --- | --- | --- |
| `strings` ne trouve rien | chaîne XORée / stack string | `break strcmp` + `x/s $rsi` |
| arrêt immédiat sous `gdb` | anti-debug `ptrace` / `TracerPid` | `catch syscall`, `finish`, patch |
| `ltrace` muet | binaire statique | `strace`, `iz` + `axt` |
| `upx -d` : `not packed by UPX` | marqueur de queue altéré | `grep -abo 'UPX!'`, réparer |
| `upx -d` : `l_info corrupted` | marqueur de tête altéré | réparer `[236:240]` |
| `file` dit « statically linked » | binaire packé, sans section headers | `readelf -h`, `strings` |

## Références

- [ptrace(2)](https://man7.org/linux/man-pages/man2/ptrace.2.html) — `PTRACE_TRACEME`, `EPERM`
- [proc_pid_status(5)](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html) — `TracerPid`
- [Yama LSM — `ptrace_scope`](https://www.kernel.org/doc/html/latest/admin-guide/LSM/Yama.html)
- [gdb — `catch syscall`](https://sourceware.org/gdb/onlinedocs/gdb/Set-Catchpoints.html) et
  `set exec-wrapper`
- [UPX](https://upx.github.io/) — `upx -d`, `-l`, `-9` ; format `p_info` / `l_info`
- [radare2 book](https://book.rada.re/) — `aaa`, `afl`, `axt`, `wx`, `pdf`
- Chapitres [4.4](04-desassemblage-radare2-rizin.md), [4.5](05-analyse-dynamique-gdb-strace.md),
  [4.6](06-decompilation-cli-patching-z3.md)







