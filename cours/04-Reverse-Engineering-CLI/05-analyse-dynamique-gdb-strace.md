# 4.5 — Analyse dynamique : `strace`, `ltrace`, `gdb`

> Fiche du chapitre 4.5 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- expliquer **ce que l'exécution apporte** que la lecture statique ne peut pas donner ;
- tracer les **appels système** avec `strace` (`-f`, `-e trace=…`, `-s`, `-T`, `-c`, `-o`) et lire
  le format `appel(args) = retour` ;
- repérer dans une trace un **fichier manquant** (`ENOENT`) et un **appel bloquant** ;
- tracer les **appels de bibliothèque** avec `ltrace`, et surtout savoir **quand il ne montre
  rien** (`-static`, comparaison écrite à la main) ;
- mener une session `gdb` reproductible en `-batch -ex` : points d'arrêt, pas à pas, inspection
  des registres et de la mémoire, cartographie d'un binaire PIE ;
- **modifier un programme à la volée** (`set`, `jump`) sans réécrire le fichier ;
- résoudre un crackme dont la clé n'existe qu'en mémoire, avec des commandes `gdb` documentées.

## 1. Pourquoi passer à l'exécution

L'analyse statique répond à « que **peut** faire ce fichier ». L'analyse dynamique répond à
« que **fait**-il, avec quelles valeurs ». Quatre situations rendent la seconde indispensable.

| Situation | Statique | Dynamique |
| --- | --- | --- |
| La clé est calculée à partir de l'entrée ou du temps | on lit une formule, sans résultat | on lit la valeur au moment du `cmp` |
| La chaîne est déchiffrée en mémoire | on voit un blob XORé et la routine | on lit le clair dans la pile après déchiffrement |
| Savoir ce que le binaire touche vraiment | on voit les appels possibles | on voit les fichiers, sockets et processus réels |
| Du code jamais atteint | indiscernable du code actif | la trace montre qu'il n'est pas exécuté |

Un binaire peut contenir cent fonctions et n'en appeler que trois. `objdump` et `radare2` les
affichent toutes ; `strace`, `ltrace` et `gdb` montrent celles qui tournent réellement.

Chaque outil répond à une question différente, et l'ordre compte :

| Question | Outil | Niveau observé |
| --- | --- | --- |
| Quels fichiers, sockets, processus ? | `strace` | appels système (noyau) |
| Quels appels de bibliothèque, avec quels arguments ? | `ltrace` | appels dynamiques (libc) |
| Quelles valeurs dans les registres et la mémoire ? | `gdb` | instructions et données |

> **Sécurité — à lire avant d'exécuter quoi que ce soit.** Un binaire inconnu s'exécute dans une
> **machine virtuelle** ou un conteneur jetable, jamais sur votre poste, jamais avec vos
> identifiants montés. Un crackme peut effacer des fichiers, ouvrir un socket ou lancer un
> `rm -rf`. Les traces et le débogueur ne protègent de rien : ils **observent** le programme, ils
> ne le neutralisent pas. Pour un conteneur jetable :
>
> ```bash
> docker run --rm -it -v "$PWD:/work:ro" -w /work debian:13 bash
> ```
>
> Le montage en `:ro` empêche le binaire d'écrire dans votre répertoire courant.

Les exemples de cette fiche tournent dans un conteneur Debian 13, sur un binaire que j'ai
compilé moi-même. Les adresses et les PID diffèrent chez vous ; les instructions et la logique,
non.

## 2. `strace` : voir les appels système

`strace` s'attache au processus via `ptrace` et journalise chaque **appel système** : c'est la
frontière entre le programme et le noyau. Tout ce qui touche le monde extérieur passe par là —
fichiers, réseau, processus, mémoire.

### Le format

Une ligne = un appel, ses arguments, puis sa valeur de retour :

```text
openat(AT_FDCWD, "absent.txt", O_RDONLY) = -1 ENOENT (No such file or directory)
^appel   ^premier argument     ^chemin     ^drapeaux  ^retour ^errno ^message
```

Un retour **négatif** est une erreur : `-1 ENOENT` veut dire « ce fichier n'existe pas ». Un
retour positif est souvent un descripteur de fichier (`= 3`) ou un nombre d'octets lus.

### Un programme qui fait tout ce qui compte

```c
#include <stdio.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int main(void) {
    FILE *f = fopen("config.ini", "r");
    if (!f) perror("config.ini");
    else { fclose(f); puts("config.ini lu"); }

    f = fopen("absent.txt", "r");
    if (!f) perror("absent.txt");

    int s = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in a = {0};
    a.sin_family = AF_INET;
    a.sin_port = htons(9999);
    a.sin_addr.s_addr = inet_addr("127.0.0.1");
    connect(s, (struct sockaddr *)&a, sizeof a);
    close(s);

    if (fork() == 0) {
        execl("/bin/true", "true", (char *)NULL);
        _exit(127);
    }
    return 0;
}
```

```bash
gcc -O0 -o trace trace.c
echo 'config=ok' > config.ini
strace -f -o trace.log -e trace=file,network,process -s 200 ./trace
grep -E 'execve\("\./trace"|config\.ini|absent\.txt|socket\(|connect\(|clone\(|execve\("/bin/true"' trace.log
```

```text
16678 execve("./trace", ["./trace"], 0x7ffee88cebb8 /* 78 vars */) = 0
16678 openat(AT_FDCWD, "config.ini", O_RDONLY) = 3
16678 openat(AT_FDCWD, "absent.txt", O_RDONLY) = -1 ENOENT (No such file or directory)
16678 socket(AF_INET, SOCK_STREAM, IPPROTO_IP) = 3
16678 connect(3, {sa_family=AF_INET, sin_port=htons(9999), sin_addr=inet_addr("127.0.0.1")}, 16) = -1 ECONNREFUSED (Connection refused)
16678 clone(child_stack=NULL, flags=CLONE_CHILD_CLEARTID|CLONE_CHILD_SETTID|SIGCHLD, child_tidptr=0x722a7426ea10) = 16679
16679 execve("/bin/true", ["true"], 0x7ffc4c297058 /* 78 vars */ <unfinished ...>
```

Cette trace courte raconte tout le programme :

1. `execve("./trace", …) = 0` : le noyau a chargé le binaire (PID 16678).
2. `openat(… "config.ini" …) = 3` : le fichier existe, descripteur 3.
3. `openat(… "absent.txt" …) = -1 ENOENT` : **le fichier n'existe pas** — c'est exactement ce
   qu'on cherche quand un programme « ne trouve pas » sa configuration.
4. `socket(…) = 3` puis `connect(…) = -1 ECONNREFUSED` : une connexion TCP vers `127.0.0.1:9999`
   a échoué, personne n'écoute. Le port et l'adresse sont lisibles en clair : c'est souvent le
   premier indice d'un binaire qui « phone home ».
5. `clone(…) = 16679` : un `fork()`. Grâce à `-f`, strace suit l'enfant, et la dernière ligne
   montre son `execve("/bin/true")`.

Le préfixe `16678` est le **PID** : il n'apparaît que parce que `-f` suit les processus fils. Sans
`-f`, la trace s'arrête au `fork`.

### Les options qui servent vraiment

| Option | Effet | Quand l'utiliser |
| --- | --- | --- |
| `-f` | suit les processus fils et les threads | dès qu'il y a `fork`, `clone`, `execve` |
| `-e trace=file` | seulement les appels qui prennent un chemin | « quels fichiers ouvre-t-il ? » |
| `-e trace=network` | seulement les appels réseau | « à qui parle-t-il ? » |
| `-e trace=process` | seulement `fork`/`clone`/`execve`/`exit` | « lance-t-il un autre programme ? » |
| `-s 200` | affiche jusqu'à 200 octets de chaque chaîne | par défaut, coupé à 32 |
| `-T` | durée de chaque appel entre `< >` | trouver ce qui bloque |
| `-c` | tableau récapitulatif par appel | vue d'ensemble, sans le détail |
| `-o fichier` | écrit dans un fichier | éviter le mélange avec la sortie du programme |
| `-p PID` | s'attache à un processus déjà lancé | programme qui tourne déjà |

`-e trace=…` accepte aussi une liste d'appels précis : `-e trace=openat,read,write`.

### La troncature des chaînes

Par défaut, `strace` coupe les chaînes à 32 caractères. Sur une entrée de 120 `A` :

```text
$ strace -e trace=read ./readwait < long.txt
read(0, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"..., 4096) = 121
```

Les `...` signalent la coupe. Avec `-s 200`, la chaîne entière apparaît :

```text
$ strace -s 200 -e trace=read ./readwait < long.txt
read(0, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n", 4096) = 121
```

Pour un binaire qui compare un mot de passe, `-s 200` est souvent l'option qui fait la différence
entre « je vois `"AAAA..."` » et « je vois le mot de passe ».

### Trouver l'appel qui bloque

Un programme qui « ne fait rien » est souvent arrêté sur un `read`, un `accept` ou un `connect`
qui attend. Sans `-T`, on voit l'appel sans sa durée. Avec `-T`, le temps passé apparaît entre
chevrons :

```bash
( sleep 2; echo bonjour ) | strace -T -e trace=read ./readwait
```

```text
entrez quelque chose : read(0, "bonjour\n", 4096)              = 8 <1.978435>
recu : bonjour
+++ exited with 0 +++
```

`<1.978435>` : le `read` a attendu presque deux secondes avant de recevoir la ligne. C'est la
signature d'un appel **bloquant**. La même mesure sur un `connect` qui n'aboutit jamais vous
donne le temps exact d'un timeout réseau.

### Le récapitulatif `-c`

Pour une vue d'ensemble plutôt que le détail :

```bash
strace -c ./trace
```

```text
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
  0.00    0.000000           0         1           read
  0.00    0.000000           0         2           write
  0.00    0.000000           0         4           close
  0.00    0.000000           0         2           fstat
  0.00    0.000000           0         7           mmap
  0.00    0.000000           0         3           mprotect
  0.00    0.000000           0         3           brk
  0.00    0.000000           0         2           rt_sigprocmask
```

Les colonnes `calls` et `errors` suffisent souvent : un binaire qui appelle 300 fois `openat`
avec 298 erreurs est en train de chercher quelque chose.

### Ce que `strace` ne montre pas

`strace` s'arrête à la frontière du noyau. Il ne voit **ni** les appels de bibliothèque internes
(`strcmp`, `memcpy`), **ni** les valeurs manipulées dans les registres. Un `strcmp` sur un mot de
passe n'apparaît pas : tout se passe en espace utilisateur. C'est le travail de `ltrace`, puis de
`gdb`.

## 3. `ltrace` : voir les appels de bibliothèque

`ltrace` journalise les appels aux **fonctions des bibliothèques partagées** (libc en tête). Il
s'appuie sur les entrées PLT/GOT du binaire : chaque appel qui passe par la bibliothèque
dynamique est intercepté, avec ses arguments et sa valeur de retour.

### Le cas d'école : `strcmp` révèle le mot de passe

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[64];

    printf("mot de passe : ");
    if (!fgets(buf, sizeof buf, stdin))
        return 1;
    buf[strcspn(buf, "\n")] = 0;

    if (strcmp(buf, "s3cr3t!") == 0)
        puts("acces autorise");
    else
        puts("refuse");

    return 0;
}
```

```bash
gcc -O0 -o login login.c
echo 'mauvais' | ltrace -s 200 ./login
```

```text
printf("mot de passe : ")                        = 15
fgets("mauvais\n", 64, 0x747e70f6a8e0)           = 0x7ffee4b90870
strcspn("mauvais\n", "\n")                       = 7
strcmp("mauvais", "s3cr3t!")                     = -6
puts("refuse")                                   = 7
mot de passe : refuse
+++ exited (status 0) +++
```

Tout est là. Le mot de passe n'est jamais écrit en clair dans le code source compilé sous cette
forme — mais `strcmp` reçoit **les deux chaînes en argument**, et `ltrace` les affiche. La valeur
de retour `-6` est la différence des premiers caractères différents (`'m' - 's' = 109 - 115`).

L'option `-s 200` allonge les chaînes affichées, exactement comme pour `strace`.

### Les options utiles

| Option | Effet |
| --- | --- |
| `-s 200` | jusqu'à 200 octets par chaîne (32 par défaut) |
| `-i` | affiche l'adresse d'instruction de l'appel |
| `-C` | démasque les noms C++ (`_ZN…` → `nom(...)`) |
| `-e 'strcmp+strncmp'` | ne trace que les fonctions listées |
| `-p PID` | s'attache à un processus en cours |
| `-o fichier` | écrit la trace dans un fichier |

`-i` est précieux pour recouper avec `objdump` : on obtient l'adresse exacte de l'appel, donc on
peut retrouver la fonction qui l'a émis.

### Démonstration de ses limites

`ltrace` ne voit que ce qui **passe par la bibliothèque dynamique**. Deux constructions très
courantes le rendent muet.

**Limite 1 — le binaire est lié statiquement.** Plus de PLT, plus d'appels interceptables :

```bash
gcc -O0 -static -o login_static login.c
echo 'mauvais' | ltrace -s 200 ./login_static
```

```text
Couldn't find .dynsym or .dynstr in "/proc/17802/exe"
mot de passe : refuse
```

`ltrace` ne peut même pas s'initialiser : un binaire `-static` n'a pas de table de symboles
dynamiques. Le programme tourne normalement, la trace est vide.

**Limite 2 — la comparaison est écrite à la main.** Remplaçons `strcmp` par une boucle (dans
`main`, le `if (strcmp(buf, "s3cr3t!") == 0)` devient `if (verifie(buf))`) :

```c
static int verifie(const char *s) {
    static const char k[] = "s3cr3t!";
    for (int i = 0; k[i]; i++)
        if (s[i] != k[i])
            return 0;
    return 1;
}
```

```bash
gcc -O0 -o login_byte login_byte.c
echo 'mauvais' | ltrace -s 200 ./login_byte
```

```text
printf("mot de passe : ")                        = 15
fgets("mauvais\n", 64, 0x73d2745938e0)           = 0x7ffe914951b0
strcspn("mauvais\n", "\n")                       = 7
puts("refuse")                                   = 7
mot de passe : refuse
+++ exited (status 0) +++
```

Plus aucun `strcmp` : la comparaison est une suite de `cmp` en assembleur, à l'intérieur du
programme. `ltrace` ne voit rien parce qu'il n'y a rien à voir au niveau des bibliothèques.

> **Leçon.** `ltrace` est un raccourci, pas une méthode. Dès qu'un binaire est statique ou
> compare ses données lui-même, il faut `gdb` — et c'est précisément ce que fait l'exercice de
> cette fiche.

## 4. `gdb` en ligne de commande

`gdb` observe et **contrôle** l'exécution : il peut arrêter le programme à une instruction, lire
et écrire les registres et la mémoire, puis repartir. C'est le seul des trois outils qui permet
de répondre à « quelle est cette valeur, ici, maintenant ».

### Le mode reproductible : `-batch -ex`

Une session interactive ne se recopie pas dans un writeup. `-batch` exécute une liste de
commandes puis quitte ; `-ex` en ajoute une :

```bash
gdb -q -batch \
    -ex 'set disassembly-flavor intel' \
    -ex 'break main' \
    -ex 'run' \
    -ex 'info registers rip' \
    ./login
```

- `-q` : pas de bannière.
- `-batch` : quitte à la fin (pas de prompt).
- `-ex 'cmd'` : une commande, dans l'ordre.

Toute la fiche utilise cette forme : chaque bloc est une commande complète, copiable, dont la
sortie est vérifiable. Sur Debian, `gdb` affiche au démarrage deux lignes `libthread_db` sans
rapport avec le programme analysé ; je les omets dans les extraits suivants pour garder la lecture
claire.

### Syntaxe Intel

`gdb` affiche par défaut la syntaxe AT&T (`mov %edi,-0x4(%rbp)`). Pour lire la même chose que
`objdump -M intel` et `radare2` :

```text
(gdb) set disassembly-flavor intel
```

À mettre en tête de chaque session `-batch`, ou une fois pour toutes dans `~/.gdbinit` :

```text
set disassembly-flavor intel
set pagination off
```

### Points d'arrêt

| Commande | Arrête sur |
| --- | --- |
| `break main` | la première instruction de `main` (symbole) |
| `break login.c:12` | la ligne 12 (nécessite les infos de debug, `-g`) |
| `break *main+113` | `main` + 113 octets, indépendant des infos de debug |
| `break *0x4011e5` | une adresse absolue (binaire non PIE) |
| `hbreak *main+113` | idem, mais avec un point d'arrêt **matériel** |
| `watch buf[0]` | l'**écriture** dans une variable (watchpoint) |
| `rwatch x` / `awatch x` | la lecture / lecture-écriture |
| `info breakpoints` | la liste des points d'arrêt posés |

La différence entre `break` et `hbreak` : un point d'arrêt logiciel remplace l'octet par
l'instruction `int3` (`0xcc`) et le remet ensuite ; un point d'arrêt matériel utilise les
registres de debug du processeur et ne modifie pas le code — indispensable sur du code
auto-modifiant ou en ROM.

> **Vérifié sur cette machine.** `hbreak` échoue ici :
>
> ```text
> (gdb) hbreak *main+113
> No hardware breakpoint support in the target.
> ```
>
> C'est une limitation de l'environnement (conteneur, `ptrace` restreint), pas de `gdb`. Sur un
> poste classique, la même commande fonctionne. Retenez le symptôme : « hardware breakpoint
> support » absent = utilisez `break`, ou changez d'environnement.

### Avancer : `run`, `continue`, `nexti`, `stepi`, `finish`

| Commande | Abréviation | Effet |
| --- | --- | --- |
| `run` | `r` | lance le programme jusqu'au premier arrêt |
| `continue` | `c` | repart jusqu'au prochain arrêt |
| `nexti` | `ni` | exécute **une** instruction, sans entrer dans les `call` |
| `stepi` | `si` | exécute **une** instruction, en entrant dans les `call` |
| `finish` | | exécute jusqu'au retour de la fonction courante |
| `until *addr` | | exécute jusqu'à l'adresse |

Sur l'appel à `strcmp`, la différence `si` / `ni` saute aux yeux :

```bash
gdb -q -batch -ex 'set disassembly-flavor intel' \
    -ex 'break *main+108' -ex 'run < in.txt' \
    -ex 'x/i $pc' -ex 'stepi' -ex 'x/i $pc' \
    -ex 'finish' -ex 'x/i $pc' -ex 'info registers eax' \
    ./login
```

```text
Breakpoint 1 at 0x11e5: file login.c, line 12.
Breakpoint 1, 0x00005555555551e5 in main () at login.c:12
12          if (strcmp(buf, "s3cr3t!") == 0)
=> 0x5555555551e5 <main+108>:   call   0x555555555070 <strcmp@plt>
0x0000555555555070 in strcmp@plt ()
=> 0x555555555070 <strcmp@plt>: jmp    QWORD PTR [rip+0x2faa]        # 0x555555558020 <strcmp@got.plt>
0x00005555555551ea in main () at login.c:12
12          if (strcmp(buf, "s3cr3t!") == 0)
=> 0x5555555551ea <main+113>:   test   eax,eax
eax            0xfffffffa          -6
```

Trois leçons dans ces dix lignes :

1. `stepi` sur un `call …@plt` n'entre pas dans libc : il atterrit dans le **stub PLT**, qui est
   un simple `jmp` vers la GOT. Il faut un second `si` pour atteindre la vraie fonction.
2. `finish` revient à l'instruction qui **suit** l'appel, dans `main`.
3. `eax = 0xfffffffa` = `-6` : la valeur de retour de `strcmp`, exactement ce que `ltrace`
   affichait. La différence est qu'ici on peut la **modifier**.

### Le confort : `pwndbg` et `gef`

`gdb` nu est austère. Deux extensions le rendent agréable, sans changer les commandes :

| Extension | Apport |
| --- | --- |
| [`pwndbg`](https://github.com/pwndbg/pwndbg) | contexte automatique (registres, pile, code), `heap`, `vis_heap_chunks`, `telescope` |
| [`gef`](https://github.com/hugsy/gef) | même idée, `checksec`, `vmmap`, `pattern create/search`, `got` |

Ils ajoutent des commandes **en plus** : `break`, `si`, `x/…` restent valables. Les exemples de
cette fiche n'en dépendent pas — c'est volontaire : une commande `gdb` standard fonctionne
partout, y compris sur une machine où rien n'est installé.

### Inspecter : registres, mémoire, code

| Commande | Ce qu'elle affiche |
| --- | --- |
| `info registers` / `i r` | tous les registres |
| `i r eax rsp rip` | seulement ceux demandés |
| `x/20gx $rsp` | 20 *giant words* (8 octets) en hexadécimal, à partir de `rsp` |
| `x/8wx $rsp` | 8 mots de 4 octets |
| `x/16bx $rsp` | 16 octets |
| `x/s $rdi` | la chaîne pointée par `rdi` |
| `x/8cb $rdi` | 8 octets, en caractères |
| `x/i $pc` | l'instruction courante |
| `disas main` | tout `main`, désassemblé |
| `disas /r main` | idem, avec les octets machine |

Le format de `x` se lit `x/<nombre><taille><format>` : `g` = 8 octets, `w` = 4, `b` = 1 ;
`x` = hexadécimal, `d` = décimal, `s` = chaîne, `i` = instruction, `c` = caractère.

À l'arrêt juste avant `strcmp`, les arguments de la fonction sont dans `rdi` et `rsi` — c'est la
convention System V vue au chapitre 4.3 :

```bash
gdb -q -batch -ex 'set disassembly-flavor intel' \
    -ex 'break *main+108' -ex 'run < in.txt' \
    -ex 'x/s $rdi' -ex 'x/s $rsi' -ex 'x/8gx $rsp' \
    ./login
```

```text
Breakpoint 1, 0x00005555555551e5 in main () at login.c:12
12          if (strcmp(buf, "s3cr3t!") == 0)
0x7fffffffd4d0: "mauvais"
0x555555556016: "s3cr3t!"
0x7fffffffd4d0: 0x007369617675616d      0x0000000000000000
0x7fffffffd4e0: 0x0000000000000000      0x0000000000000000
0x7fffffffd4f0: 0x0000000000000000      0x00007ffff7fe5600
0x7fffffffd500: 0x0000000000000000      0x00007fffffffd5a0
```

`x/s $rdi` donne l'entrée (« mauvais »), `x/s $rsi` donne **le secret** (« s3cr3t! »). Sans
`ltrace`, sans `strcmp`, en lisant simplement les deux arguments.

Le premier *giant word* de la pile mérite un détour : `0x007369617675616d`. En little-endian, les
octets se lisent à l'envers : `6d 61 75 76 61 69 73 00` = `m a u v a i s \0`. **C'est le buffer
lui-même**, écrit par `fgets` juste avant. Savoir lire un `gx` en little-endian évite bien des
contresens.

### Le décalage PIE : adresse du fichier contre adresse en mémoire

`break main` a annoncé `0x11e5`, mais le programme s'arrête à `0x00005555555551e5`. Le binaire est
PIE : le noyau le charge à une base aléatoire, et toutes les adresses sont décalées.

```bash
gdb -q -batch -ex 'break main' -ex 'run < in.txt' -ex 'info proc mappings' ./login
```

```text
Breakpoint 1 at 0x1181: file login.c, line 7.
Breakpoint 1, main () at login.c:7
process 27607
Mapped address spaces:

Start Addr         End Addr           Size               Offset             Perms File
0x0000555555554000 0x0000555555555000 0x1000             0x0                r--p  /tmp/rev45/login
0x0000555555555000 0x0000555555556000 0x1000             0x1000             r-xp  /tmp/rev45/login
0x0000555555556000 0x0000555555557000 0x1000             0x2000             r--p  /tmp/rev45/login
0x0000555555557000 0x0000555555558000 0x1000             0x2000             r--p  /tmp/rev45/login
0x0000555555558000 0x0000555555559000 0x1000             0x3000             rw-p  /tmp/rev45/login
```

La base est `0x555555554000` : c'est la première ligne `r--p` avec `Offset 0x0`. On vérifie :

```text
0x555555554000 + 0x1181 = 0x555555555181
```

soit exactement l'adresse où `main` s'est arrêté. Les cinq lignes correspondent aux segments du
fichier : `r--` (en-têtes), `r-x` (code), `r--` (données en lecture seule), `rw-` (données
modifiables). `Offset` est l'offset **dans le fichier** ; `Start Addr` l'adresse **en mémoire**.

Sous `gdb`, ASLR est désactivé par défaut : la base est presque toujours `0x555555554000`. Lancé
normalement, le même binaire tombe ailleurs à chaque exécution — c'est le sujet de la section 8
du chapitre 4.4.

### Watchpoint : qui écrit dans cette variable ?

Un point d'arrêt arrête sur une **instruction**. Un watchpoint arrête sur un **accès mémoire** :
c'est la bonne réponse à « à quel moment cette variable change-t-elle ? ».

```bash
gdb -q -batch -ex 'break 8' -ex 'run < in.txt' \
    -ex 'watch buf[0]' -ex 'continue' -ex 'bt 3' -ex 'frame 2' -ex 'x/s &buf' \
    ./login
```

```text
Breakpoint 1 at 0x1195: file login.c, line 8.
[Thread debugging using libthread_db enabled]
Using host libthread_db library "/usr/lib/x86_64-linux-gnu/libthread_db.so.1".

Breakpoint 1, main () at login.c:8
8           if (!fgets(buf, sizeof buf, stdin))
Hardware watchpoint 2: buf[0]

Hardware watchpoint 2: buf[0]

Old value = 0 '\000'
New value = 109 'm'
0x00007ffff7e4a603 in _IO_getline_info () from /usr/lib/x86_64-linux-gnu/libc.so.6
#0  0x00007ffff7e4a603 in _IO_getline_info () from /usr/lib/x86_64-linux-gnu/libc.so.6
#1  0x00007ffff7e4942a in fgets () from /usr/lib/x86_64-linux-gnu/libc.so.6
#2  0x00005555555551ad in main () at login.c:8
#2  0x00005555555551ad in main () at login.c:8
8           if (!fgets(buf, sizeof buf, stdin))
0x7fffffffd4d0: "m"
```

Le watchpoint s'est déclenché **dans libc**, au moment où `fgets` écrit le premier octet du
buffer. `bt 3` montre la chaîne d'appel complète (`_IO_getline_info` → `fgets` → `main`), puis
`frame 2` replace `gdb` dans le contexte de `main` — d'où la ligne `#2` répétée, suivie du code
source. `x/s &buf` affiche alors `"m"` : le buffer commence à `0x7fffffffd4d0`.

C'est la façon la plus rapide de découvrir où une valeur est écrite — et donc, souvent, où se
trouve la logique de vérification. Les deux lignes `libthread_db` sont normales sur Debian ; elles
n'ont aucun rapport avec le programme analysé.

### Modifier à la volée

`gdb` écrit dans le processus comme dans un fichier. Trois gestes couvrent presque tout.

**1. Changer un registre** — ici la valeur de retour de `strcmp`, juste avant le `test` qui
décide :

```bash
gdb -q -batch -ex 'break *main+113' -ex 'run < in.txt' \
    -ex 'set $eax = 0' -ex 'continue' ./login
```

```text
Breakpoint 1, 0x00005555555551ea in main () at login.c:12
12          if (strcmp(buf, "s3cr3t!") == 0)
mot de passe : acces autorise
```

L'entrée était « mauvais ». En forçant `eax` à 0 (ce que renvoie `strcmp` quand les chaînes sont
égales), le programme affiche « acces autorise ». Aucun fichier n'a été modifié : le patch vit
dans le processus.

**2. Changer la mémoire** — réécrire l'entrée avant qu'elle ne soit comparée :

```bash
gdb -q -batch -ex 'break *main+108' -ex 'run < in.txt' \
    -ex 'x/s $rdi' \
    -ex 'set {char[8]} $rdi = "s3cr3t!"' \
    -ex 'x/s $rdi' -ex 'continue' ./login
```

```text
0x7fffffffd4d0: "mauvais"
0x7fffffffd4d0: "s3cr3t!"
mot de passe : acces autorise
```

`{char[8]}` est un **type** : `gdb` écrit 8 octets à l'adresse contenue dans `rdi`. La même
syntaxe sert pour un entier : `set *(int *)0x555555558010 = 1`, ou `set {int}$rsp = 0`.

**3. Sauter** — aller directement à une adresse, sans exécuter ce qui précède :

```bash
gdb -q -batch -ex 'break *main+108' -ex 'run < in.txt' \
    -ex 'jump *main+117' -ex 'continue' ./login
```

```text
mot de passe : acces autorise
[Inferior 1 (process 27428) exited normally]
The program is not being run.
```

`jump *main+117` place `rip` sur la première instruction du bloc « succès » et reprend
l'exécution. C'est le raccourci qui montre le plus vite qu'une vérification n'est qu'un saut. La
dernière ligne (`The program is not being run.`) vient du `continue` exécuté après la fin du
programme : sans effet, mais présente dans la sortie.

> **Attention.** `jump` ne « répare » pas l'état : si le bloc sauté attend des registres ou une
> pile préparés, le programme plante. C'est un outil d'exploration, pas un patch.

## 5. Exercice : la clé n'existe qu'en mémoire

Ce programme déchiffre sa clé au démarrage, la garde dans la pile, et compare l'entrée **octet par
octet**. Aucune chaîne secrète n'est présente dans le fichier, aucun `strcmp` n'est appelé :
`ltrace` ne montrera rien d'utile.

```c
#include <stdio.h>
#include <string.h>

int main(void) {
    char saisie[64];
    char cle[16];
    static const unsigned char blob[11] = {
        0x1f, 0x22, 0x35, 0x6f, 0x36, 0x6a, 0x2a, 0x2e, 0x68, 0x7a, 0x64
    };

    for (int i = 0; i < 11; i++)
        cle[i] = blob[i] ^ 0x5b;
    cle[11] = 0;

    printf("cle : ");
    if (!fgets(saisie, sizeof saisie, stdin))
        return 1;
    saisie[strcspn(saisie, "\n")] = 0;

    int ok = 1;
    for (int i = 0; i <= 11; i++) {
        if (saisie[i] != cle[i]) { ok = 0; break; }
        if (cle[i] == 0) break;
    }

    puts(ok ? "bravo" : "non");
    return 0;
}
```

```bash
gcc -O0 -o crackme_dyn crackme_dyn.c
echo 'mauvais' | ./crackme_dyn
echo 'mauvais' | ltrace -s 200 ./crackme_dyn
```

```text
cle : non
printf("cle : ")                                 = 6
fgets("mauvais\n", 64, 0x758d014fa8e0)           = 0x7ffd696466d0
strcspn("mauvais\n", "\n")                       = 7
puts("non")                                      = 4
cle : non
+++ exited (status 0) +++
```

`ltrace` voit l'entrée, mais **pas** la comparaison : elle n'appelle aucune fonction.

### Questions

1. Pourquoi `strings crackme_dyn` ne révèle-t-il pas la clé ?
2. Dans `main`, quelle instruction déchiffre chaque octet, et où le résultat est-il écrit ?
3. Pourquoi faut-il s'arrêter **après** `mov BYTE PTR [rbp-0x55],0x0` et non juste après la boucle ?
4. Donne la commande `gdb` qui affiche la clé, puis la clé elle-même.
5. Vérifie la clé sans `gdb`.

<details>
<summary>Correction</summary>

**1. `strings` ne trouve rien** parce que la clé n'est jamais stockée en clair dans le fichier :
seul le blob XORé l'est. `strings` lit `.rodata` sur le disque, pas la pile à l'exécution.

**2. Le déchiffrement** se lit dans `objdump -d -M intel crackme_dyn` :

```text
    1186:       0f b6 04 10             movzx  eax,BYTE PTR [rax+rdx*1]
    118a:       83 f0 5b                xor    eax,0x5b
    118d:       89 c2                   mov    edx,eax
    118f:       8b 45 fc                mov    eax,DWORD PTR [rbp-0x4]
    1192:       48 98                   cdqe
    1194:       88 54 05 a0             mov    BYTE PTR [rbp+rax*1-0x60],dl
```

`xor eax,0x5b` déchiffre un octet, `mov BYTE PTR [rbp+rax*1-0x60],dl` l'écrit dans `cle`, qui vit
donc à `rbp-0x60`. La boucle se termine par `jle 117a` à l'adresse `0x11a0`.

**3. L'octet nul.** Juste après la boucle, `0x11a2` exécute
`mov BYTE PTR [rbp-0x55],0x0` — c'est `cle[11] = 0`. Si on s'arrête **sur** cette instruction,
la chaîne n'est pas encore terminée et `x/s` déborde sur les octets voisins :

```text
0x7fffffffd6b0: 68 'D'  121 'y' 110 'n' 52 '4'  109 'm' 49 '1'  113 'q' 117 'u'
0x7fffffffd6b8: 51 '3'  33 '!'  63 '?'  -1 '\377'
0x7fffffffd6b0: "Dyn4m1qu3!?\377\377\177"
```

Il faut donc viser l'instruction **suivante**, à `main+0x3d` (`0x11a6`).

**4. La commande `gdb` et la clé** :

```bash
gdb -q -batch -ex 'set disassembly-flavor intel' \
    -ex 'break *main+0x3d' -ex 'run < /dev/null' \
    -ex 'x/12cb $rbp-0x60' -ex 'x/s $rbp-0x60' \
    ./crackme_dyn
```

```text
Breakpoint 1, 0x00005555555551a6 in main ()
0x7fffffffd6b0: 68 'D'  121 'y' 110 'n' 52 '4'  109 'm' 49 '1'  113 'q' 117 'u'
0x7fffffffd6b8: 51 '3'  33 '!'  63 '?'  0 '\000'
0x7fffffffd6b0: "Dyn4m1qu3!?"
```

La clé est **`Dyn4m1qu3!?`**. Les douze octets se lisent directement : `D y n 4 m 1 q u 3 ! ? \0`.

`run < /dev/null` fournit une entrée vide : on n'a pas besoin de saisir quoi que ce soit, le
programme s'arrête avant de lire.

**5. Vérification** :

```bash
$ echo 'Dyn4m1qu3!?' | ./crackme_dyn
cle : bravo
```

**Variante sans connaître l'offset.** Si le binaire est strippé, on retrouve la boucle par sa
constante : `objdump -d -M intel crackme_dyn | grep -n 'xor.*0x5b'`, puis on pose le point
d'arrêt sur l'instruction qui suit le `jle`. Sur un binaire plus gros, le watchpoint est plus
rapide : `watch` sur le premier octet de la zone suspecte, puis `bt` pour voir qui écrit.

</details>

## 6. Ce que je retiens

- L'analyse dynamique répond à « quelles **valeurs**, dans quel **ordre** ». Un binaire peut
  contenir du code jamais exécuté : seule la trace le dit.
- `strace` = frontière avec le noyau. Format `appel(args) = retour` ; un retour négatif est une
  erreur (`-1 ENOENT` = fichier absent). `-f` suit les fils, `-s 200` déplie les chaînes, `-T`
  mesure les blocages, `-c` résume.
- `ltrace` = appels de bibliothèque. Spectaculaire sur un `strcmp` (`strcmp("mauvais",
  "s3cr3t!")`), **muet** sur un binaire `-static` et sur une comparaison écrite à la main.
- `gdb -q -batch -ex '…'` est le seul format recopiable dans un writeup.
- `break` logiciel vs `hbreak` matériel : le second ne modifie pas le code, mais exige un support
  matériel (absent dans mon conteneur : « No hardware breakpoint support in the target »).
- `si` entre dans les appels, mais s'arrête d'abord dans le **stub PLT** ; `ni` passe par-dessus ;
  `finish` revient à l'appelant.
- `x/s $rdi` et `x/s $rsi` donnent les arguments d'une fonction avant son exécution : c'est le
  remplacement de `ltrace` quand `ltrace` ne voit rien.
- `info proc mappings` donne la base PIE ; `adresse en mémoire = base + offset du fichier`.
- `set $eax = …`, `set {char[8]} $rdi = …`, `jump *main+117` modifient le programme **dans le
  processus**, sans toucher au fichier.
- Une clé déchiffrée en mémoire se lit à l'endroit exact où le déchiffrement se termine — et il
  faut vérifier que le terminateur `\0` a bien été écrit.

## Références

- `man strace`, `man ltrace`, `man gdb` — les pages de manuel restent la référence exacte des
  options
- [GDB documentation](https://sourceware.org/gdb/current/onlinedocs/gdb/) — section « Examining
  Memory » et « Breakpoints »
- [pwndbg](https://github.com/pwndbg/pwndbg) et [gef](https://github.com/hugsy/gef) — extensions
  CLI pour le confort
- Chapitre [4.3 — Assembleur x86-64](03-assembleur-x86-64.md) : convention d'appel et pile
- Chapitre [4.4 — Désassemblage](04-desassemblage-radare2-rizin.md) : PIE et adresses de base

