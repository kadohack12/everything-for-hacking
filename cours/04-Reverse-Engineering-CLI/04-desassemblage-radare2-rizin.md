# 4.4 — Désassemblage et graphe en CLI (radare2 / rizin)

> Fiche du chapitre 4.4 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- dire **pourquoi** `objdump` ne suffit plus dès qu'un binaire dépasse quelques fonctions ;
- travailler dans `radare2` ou `rizin` en mode **non interactif** (`-q -c`) pour produire des
  sorties reproductibles dans un writeup ;
- naviguer avec la syntaxe modulaire `[action][cible]`, l'aide `?`, le calculateur et `s` ;
- cartographier un binaire en cinq commandes : `afl`, `pdf @ main`, `iz`/`izz`, `ii` ;
- suivre les **références croisées** (`axt`, `axf`) pour remonter d'une chaîne à la fonction qui
  la teste ;
- lire un **graphe de flot** en ASCII (`agf`) et en mode visuel (`VV`) ;
- annoter un binaire (`afn`, `afvn`, `CC`) et comprendre le **décalage PIE** entre adresse du
  fichier et adresse d'exécution.

## 1. Pourquoi quitter `objdump`

`objdump -d` fait un **balayage linéaire** : il désassemble octet après octet à partir du début de
`.text`. Rapide, fidèle au fichier, mais aveugle :

| Besoin | `objdump` | `radare2` / `rizin` |
| --- | --- | --- |
| Désassembler une fonction précise | il faut connaître ses bornes | `pdf @ main` |
| Savoir qui référence cette chaîne | impossible | `axt @ 0x2021` |
| Suivre la fonction appelée par un `call` | `grep` manuel | `s <addr>; pdf` |
| Renommer une fonction | impossible | `afn real_check` |
| Renommer une variable locale | impossible | `afvn idx var_8h` |
| Vue graphe des branches | impossible | `agf`, `VV` |
| Détecter du code caché / non atteint | non | analyse récursive (`aaa`) |

Le point décisif est le **balayage récursif** : r2 part des points d'entrée, suit les `call` et
les sauts, et distingue le code des données. `objdump` désassemble tout, y compris les tables de
sauts — d'où ces fonctions fantômes que l'on voit parfois dans sa sortie.

```text
objdump  : « voici les octets de .text, dans l'ordre »
radare2  : « voici les fonctions, qui appelle qui, et qui utilise quelle donnée »
```

## 2. `radare2` et `rizin` : les mêmes commandes

`rizin` est un fork de `radare2` ; les deux partagent la syntaxe et environ 90 % des commandes.
Tout ce qui suit fonctionne avec `r2` **et** avec `rizin`, en remplaçant le nom du binaire :

```bash
r2 -q -c "aaa; afl" ./crackme
rizin -q -c "aaa; afl" ./crackme
```

| Option | Effet |
| --- | --- |
| `-q` | pas de bannière ni de prompt décoré |
| `-c "cmd; cmd"` | exécuter des commandes puis quitter |
| `-A` | lancer `aaa` au chargement |
| `-B 0x…` | fixer l'adresse de base (utile pour le PIE) |
| `-w` | ouvrir en écriture (patch, chapitre 4.6) |

Le mode `-q -c` est **la** façon de documenter une session : les commandes sont dans le writeup,
la sortie est reproductible, et rien ne dépend d'un état interactif.

> Les sorties de cette fiche ont été produites avec **radare2 6.2.7** sur Debian. Les versions
> antérieures peuvent différer sur des détails de format (`afl` avec ou sans taille), jamais sur
> les commandes.

## 3. Syntaxe modulaire, aide et déplacement

Une commande r2 est `[action][cible]`. La cible peut être une adresse, un nom de fonction, ou
`@ expr` pour « appliquer à ».

| Commande | Lecture |
| --- | --- |
| `afl` | **a**nalyse **f**onction **l**ist |
| `pdf @ main` | **p**rint **d**isassembly **f**unction, sur `main` |
| `iz` / `izz` | **i**nfo **z**eichen (chaînes de `.rodata` / de tout le fichier) |
| `ii` | **i**nfo **i**mports |
| `axt @ 0x2021` | **a**nalyse **x**refs **t**o |
| `axf @ 0x11c8` | **a**nalyse **x**refs **f**rom |

### L'aide intégrée

`?` est le point d'entrée de toute la documentation, hors ligne :

```text
[0x0000122e]> ?
Usage: [.][times][cmd][~grep][@[@iter]addr!size][|>pipe] ; ...
```

`?` suivi d'un préfixe donne l'aide de la famille (`a?`, `p?`, `i?`, `af?`), et `commande?` donne
l'aide précise (`pdf?`, `afvn?`). C'est plus rapide que n'importe quelle recherche web, et ça
fonctionne sans réseau.

### Le calculateur

`?` seul, suivi d'une expression, calcule :

```text
$ r2 -q -c '? 0x401140 + 0x18' ./crackme
int32   4198744
uint32  4198744
hex     0x401158
octal   020010530
unit    4.0M
segment 40000:1158
string  "X\x11@"
fvalue  4198744.0
float   0.000000000000000f
double  0.000000000000000
binary  0b010000000001000101011000
base36  0_2hzrs
ternary 0t21220022121001
```

Pratique pour calculer une cible de saut, un offset dans une section, ou convertir une constante
lue en hexadécimal dans un `cmp`.

### Se déplacer

| Commande | Effet |
| --- | --- |
| `s main` | se placer sur `main` |
| `s 0x2021` | se placer à l'adresse `0x2021` |
| `s+ 4` / `s- 4` | avancer / reculer de 4 octets |
| `s` | afficher la position courante |
| `sf main` | se placer au début de la fonction `main` |

### Filtrer

`~` filtre les lignes par expression régulière, `~!` inverse, `|` envoie vers un shell :

```bash
r2 -q -c 'aaa; pdf @ main~call' ./crackme     # seulement les appels
r2 -q -c 'izz~bravo' ./crackme                # chercher une chaîne
r2 -q -c 'afl~main' ./crackme                 # filtrer la liste des fonctions
```

### `aa` contre `aaa`

| Commande | Ce qu'elle fait | Coût |
| --- | --- | --- |
| `aa` | analyse de base : fonctions depuis les entrées et les symboles | rapide |
| `aaa` | + références, appels, variables locales, types | plus lent, indispensable |

Sur un binaire de quelques kilo-octets, `aaa` prend une fraction de seconde. Sur un binaire
statique de 700 Ko (chapitre 4.2), comptez plusieurs secondes : lancez `aa` d'abord pour explorer,
`aaa` quand vous avez besoin des xrefs et des variables. `aaaa` ajoute l'analyse expérimentale —
rarement nécessaire.

## 4. Cartographier un binaire en cinq commandes

### `afl` — les fonctions

```text
$ r2 -q -c 'aaa; afl' ./crackme
0x00001030    1      6 sym.imp.puts
0x00001040    1      6 sym.imp.strlen
0x00001050    1      6 sym.imp.printf
0x00001060    1      6 sym.imp.strcspn
0x00001070    1      6 sym.imp.fgets
0x00001080    1      6 sym.imp.strcmp
0x00001090    1      6 sym.imp.__cxa_finalize
0x000010a0    1     33 entry0
0x0000122e    9    184 main
0x00001180    5     60 entry.init0
0x00001140    5     54 entry.fini0
0x000010d0    4     34 fcn.000010d0
0x00001189    1     44 fcn.00001189
0x000011b5    9    121 fcn.000011b5
```

Colonnes : adresse, nombre de blocs de base, taille en octets, nom. Sur un binaire **strippé**,
les fonctions internes n'ont pas de nom (`fcn.00001189`) — c'est normal, et c'est là que
l'analyse commence. r2 a quand même trouvé `main` : il remonte depuis `entry0` jusqu'à l'argument
passé à `__libc_start_main`.

### `iz` / `izz` — les chaînes

```text
$ r2 -q -c 'iz' ./crackme
nth paddr      vaddr      len size section type  string
―――――――――――――――――――――――――――――――――――――――――――――――――――――――
0   0x00002004 0x00002004 11  12   .rodata ascii not-the-key
1   0x00002010 0x00002010 13  15   .rodata ascii mot de passe:
2   0x00002021 0x00002021 10  11   .rodata ascii presque...
3   0x0000202c 0x0000202c 5   6    .rodata ascii bravo
4   0x00002036 0x00002036 4   5    .rodata ascii \bi,{
```

`iz` lit les sections de données (`.rodata`, `.data`), `izz` scanne **tout** le fichier. La
dernière ligne est intéressante : `\bi,{` à `0x2036` n'est pas une chaîne, c'est une **table
d'octets** que r2 affiche comme une chaîne parce que les octets sont imprimables. C'est un rappel
du chapitre 4.1 : ce que `iz` montre n'est pas forcément du texte.

### `ii` — les imports

```text
$ r2 -q -c 'ii' ./crackme
nth vaddr      bind   type   lib name
―――――――――――――――――――――――――――――――――――――
1   ---------- GLOBAL FUNC       __libc_start_main
2   ---------- WEAK   NOTYPE     _ITM_deregisterTMCloneTable
3   0x00001030 GLOBAL FUNC       puts
4   0x00001040 GLOBAL FUNC       strlen
5   0x00001050 GLOBAL FUNC       printf
6   0x00001060 GLOBAL FUNC       strcspn
7   0x00001070 GLOBAL FUNC       fgets
8   0x00001080 GLOBAL FUNC       strcmp
9   ---------- WEAK   NOTYPE     __gmon_start__
10  ---------- WEAK   NOTYPE     _ITM_registerTMCloneTable
11  0x00001090 WEAK   FUNC       __cxa_finalize
```

La liste des imports est un profil comportemental : ici `fgets` + `strlen` + `strcmp` annoncent
une saisie comparée à quelque chose, et `printf`/`puts` les messages. Pas besoin de désassembler
pour deviner l'architecture.

### `pdf @ main` — une fonction, annotée

```text
$ r2 -q -c 'aaa; pdf @ main' ./crackme
; DATA XREF from entry0 @ 0x10b4(r)
┌ 184: int main (int argc, char **argv, char **envp);
│ afv: vars(1:sp[0x48..0x48])
│           0x0000122e      55             push rbp
│           0x0000122f      4889e5         mov rbp, rsp
│           0x00001232      4883ec40       sub rsp, 0x40
│           0x00001236      488d05d30d..   lea rax, str.mot_de_passe:  ; 0x2010 ; "mot de passe:"
│           0x0000123d      4889c7         mov rdi, rax                ; const char *format
│           0x00001245      e806feffff     call sym.imp.printf         ; int printf(const char *format, ...)
│           0x00001251      488d45c0       lea rax, [s1]
│           0x00001255      be40000000     mov esi, segment.PHDR       ; 0x40 ; int size
│           0x0000125d      e80efeffff     call sym.imp.fgets          ; char *fgets(char *s, int size, FILE *stream)
│           0x00001262      4885c0         test rax, rax
│       ┌─< 0x00001265      7507           jne 0x126e
│       │   0x00001267      b801000000     mov eax, 1
│      ┌──< 0x0000126c      eb76           jmp 0x12e4
│      │└─> 0x0000126e      488d45c0       lea rax, [s1]
│      │    0x0000127f      e8dcfdffff     call sym.imp.strcspn        ; size_t strcspn(const char *s1, const char *s2)
│      │    0x00001284      c64405c000     mov byte [rbp + rax - 0x40], 0
│      │    0x00001290      e8f4feffff     call fcn.00001189
│      │    0x00001295      85c0           test eax, eax
│      │┌─< 0x00001297      7416           je 0x12af
│      ││   0x00001299      488d05810d..   lea rax, str.presque...     ; 0x2021 ; "presque..."
│      ││   0x000012a3      e888fdffff     call sym.imp.puts           ; int puts(const char *s)
│      ││   0x000012a8      b801000000     mov eax, 1
│     ┌───< 0x000012ad      eb35           jmp 0x12e4
│     ││└─> 0x000012af      488d45c0       lea rax, [s1]
│     ││    0x000012b6      e8fafeffff     call fcn.000011b5
│     ││    0x000012bb      85c0           test eax, eax
│     ││┌─< 0x000012bd      7411           je 0x12d0
│     │││   0x000012bf      488d05660d..   lea rax, str.bravo          ; 0x202c ; "bravo"
│     │││   0x000012c9      e862fdffff     call sym.imp.puts           ; int puts(const char *s)
│    ┌────< 0x000012ce      eb0f           jmp 0x12df
│    │││└─> 0x000012d0      488d055b0d..   lea rax, [0x00002032]       ; "non"
│    │││    0x000012da      e851fdffff     call sym.imp.puts           ; int puts(const char *s)
│    └────> 0x000012df      b800000000     mov eax, 0
│     └└──> 0x000012e4      c9             leave
└           0x000012e5      c3             ret
```

(sortie abrégée : les commentaires de prototype redondants et quelques lignes de prologue sont
omis.)

r2 fait trois choses qu'`objdump` ne fait pas :

1. il **nomme** les chaînes (`str.presque...`) et affiche leur contenu ;
2. il **annote les appels** avec le prototype (`const char *s`, `int size`) ;
3. il **dessine les branches** avec des traits (`┌─<`, `│└─>`), ce qui rend le flot lisible sans
   graphe.

## 5. Références croisées : remonter d'une chaîne à la fonction

C'est le gain de temps décisif. Deux commandes, deux directions :

| Commande | Question | Réponse |
| --- | --- | --- |
| `axt @ <addr>` | qui **utilise** cette adresse ? | liste des instructions qui la référencent |
| `axf @ <addr>` | cette instruction **appelle quoi** ? | cible de l'appel |

### Qui affiche « presque... » ?

```text
$ r2 -q -c 'aaa; axt @ 0x2021' ./crackme
main 0x1299 [STRN:r--] lea rax, str.presque...
```

Une ligne, et on sait que `main` référence la chaîne à `0x1299`. Même chose pour `bravo` :

```text
$ r2 -q -c 'aaa; axt @ 0x202c' ./crackme
main 0x12bf [STRN:r--] lea rax, str.bravo
```

### Qui utilise la fausse piste ?

```text
$ r2 -q -c 'aaa; axt @ 0x2004' ./crackme
fcn.00001189 0x1199 [STRN:r--] lea rdx, str.not_the_key
```

La chaîne `not-the-key` n'est référencée que par `fcn.00001189`, pas par `main` directement. C'est
le signal d'une fonction dédiée : elle sera appelée depuis `main` (`call fcn.00001189` visible
plus haut), et c'est un **leurre**.

### Que fait une instruction `call` ?

```text
$ r2 -q -c 'aaa; axf @ 0x11c8' ./crackme
CALL 0x1040 sym.imp.strlen
```

`axf` s'applique à l'**adresse de l'instruction**, pas au nom de la fonction : `axf @ main` ne
renvoie rien, `axf @ 0x11c8` renvoie la cible du `call` situé à cette adresse. Pour lister tous
les appelants d'un import, on prend le problème par l'autre bout :

```text
$ r2 -q -c 'aaa; axt @ sym.imp.strlen' ./crackme
fcn.000011b5 0x11c8 [CALL:--x] call sym.imp.strlen
```

### Le parcours complet, en quatre commandes

```bash
r2 -q -c 'aaa; afl' ./crackme                  # 1. quelles fonctions ?
r2 -q -c 'aaa; izz~bravo' ./crackme            # 2. où est le message de succès ?
r2 -q -c 'aaa; axt @ 0x202c' ./crackme         # 3. qui l'affiche ? → main
r2 -q -c 'aaa; pdf @ main' ./crackme           # 4. quelle fonction décide ? → fcn.000011b5
```

Quatre commandes, et la fonction de vérification est identifiée sans lire une seule ligne
d'assembleur en entier.

## 6. Graphe de flot : `VV` et `agf`

### En mode visuel (interactif)

`VV` ouvre le graphe de la fonction courante en plein écran (curses, donc **dans le terminal**,
sans X11 — ça marche en SSH). Les raccourcis qui suffisent :

| Touche | Effet |
| --- | --- |
| `p` / `P` | changer de mode d'affichage (assembleur, pseudo-code, hexdump) |
| `hjkl` | se déplacer entre les blocs |
| `g` | aller à une adresse (saisir `main`, `0x1299`…) |
| `/` | chercher du texte dans le graphe |
| `c` | curseur / mode commentaire |
| `q` | revenir en arrière (deux fois pour quitter) |

`V` (une seule fois) ouvre le mode visuel classique : hexdump à gauche, désassemblage à droite,
`p`/`P` pour changer de panneau, `:` pour une commande r2.

> Ces modes sont interactifs : ils ne produisent pas de sortie copiable dans un writeup. C'est
> pourquoi la version **reproductible** du graphe est `agf`.

### En mode non interactif : `agf`

```text
$ r2 -q -c 'aaa; agf @ main' ./crackme
     ┌─────────────────────────────────────────────────────┐
     │  0x122e                                             │
     │ 184: int main (int argc, char **argv, char **envp); │
     │ push rbp                                            │
     │ mov rbp, rsp                                        │
     │ sub rsp, 0x40                                       │
     │ ; "mot de passe:"                                   │
     │ call sym.imp.printf;[oa]                            │
     │ call sym.imp.fgets;[ob]                             │
     │ test rax, rax                                       │
     │ jne 0x126e                                          │
     └─────────────────────────────────────────────────────┘
             f t
             │ │
             │ └───────────────┐
     ┌───────┘                 │
 ┌────────────────────┐    ┌──────────────────────────────────────────────────┐
 │  0x1267            │    │  0x126e                                          │
 │ mov eax, 1         │    │ call sym.imp.strcspn;[oc]                        │
 │ jmp 0x12e4         │    │ mov byte [rbp + rax - 0x40], 0                   │
 └────────────────────┘    │ call fcn.00001189;[od]                           │
     v                     │ test eax, eax                                    │
     │                     │ je 0x12af                                        │
     │                     └──────────────────────────────────────────────────┘
     │                             f t
     │                             │ │
     └──────┐                      │ └─────────────────┐
            │        ┌─────────────┘                   │
            │    ┌────────────────────────────┐    ┌──────────────────────────────────────┐
            │    │  0x1299                    │    │  0x12af                              │
            │    │ ; "presque..."             │    │ call fcn.000011b5;[of]               │
            │    │ call sym.imp.puts;[oe]     │    │ test eax, eax                        │
            │    │ mov eax, 1                 │    │ je 0x12d0                            │
            │    │ jmp 0x12e4                 │    └──────────────────────────────────────┘
            │    └────────────────────────────┘            f t
            │        v                                     │ │
            │    ┌───┘                                     │ │
            │    │                                         │─┘
            │    │        ┌────────────────────────────────┘
            │    │    ┌───────────────────────────┐    ┌──────────────────────────────────────┐
            │    │    │  0x12bf                   │    │  0x12d0                              │
            │    │    │ ; "bravo"                 │    │ ; "non"                              │
            │    │    │ jmp 0x12df                │    └──────────────────────────────────────┘
            │    │    └───────────────────────────┘        v
            │    │        v                                │
            │    │        └───────────┐                    │
            │    │              ┌──────────────────────────────────────┐
            │    │              │  0x12df  mov eax, 0                  │
            │    │              └──────────────────────────────────────┘
            │    │                  v
      ┌─────│────│──────────────────┘
      │ ┌───┘    │
      │ │ ┌──────┘
┌──────────────────────────────────────────────────┐
│  0x12e4  leave / ret                             │
└──────────────────────────────────────────────────┘
```

(extrait : les blocs sont abrégés à leurs instructions significatives ; les lignes de commentaire
et les annotations de prototype sont omises.)

Lecture : sous chaque bloc conditionnel, **`f` et `t`** marquent la branche fausse (*false*) et
vraie (*true*). Ici, `je 0x12af` (saut si zéro) : la branche `t` part vers `0x12af` quand le test
renvoie 0, la branche `f` continue vers `0x1299` (« presque... »). C'est l'inverse de l'intuition
« vrai = on saute » : `je` saute quand la condition est vraie, donc `t` suit le saut.

Le graphe rend visible en un coup d'œil ce que le listing cache : trois issues (`presque...`,
`bravo`, `non`) et **deux fonctions de vérification** appelées successivement (`0x1189` puis
`0x11b5`).

## 7. Annoter : renommer et commenter

Un binaire strippé se lit comme un brouillon : `fcn.000011b5`, `var_8h`, `str._bi_`. Trois
commandes suffisent à le rendre lisible, et **elles n'altèrent pas le fichier** tant que vous ne
sauvegardez pas.

| Commande | Effet |
| --- | --- |
| `afn <nouveau>` | renommer la fonction courante |
| `afvn <nouveau> <ancien>` | renommer une variable locale (**nouveau nom en premier**) |
| `afvt <nom> <type>` | changer le type d'une variable |
| `CC <texte>` | ajouter un commentaire à l'adresse courante |
| `afv` | lister arguments et variables de la fonction |

Session réelle sur le crackme :

```text
$ r2 -q -c 'aaa; s 0x11b5; afv' ./crackme
arg char * arg1 @ rdi
var int64_t var_8h @ rbp-0x8
var size_t var_10h @ rbp-0x10
var char * s @ rbp-0x18
```

```text
$ r2 -q -c 'aaa; s 0x11b5; afn real_check; afvn idx var_8h; afvn n var_10h; \
             s 0x11f9; CC table XOR 0x5a; pdf @ real_check~idx,n,table' ./crackme
; CALL XREF from main @ 0x12b6(x)
│           0x000011c8      e873feffff     call sym.imp.strlen         ; size_t strlen(const char *s)
│           0x000011cd      488945f0       mov qword [n], rax
│           0x000011d1      48837df007     cmp qword [n], 7
│      │└─> 0x000011df      48c745f800..   mov qword [idx], 0
│     ╎││   0x000011ed      488b45f8       mov rax, qword [idx]
│     ╎││   0x000011f9      488d15360e..   lea rdx, str._bi_           ; 0x2036 ; table XOR 0x5a
│     ╎││   0x00001200      488b45f8       mov rax, qword [idx]
│   │└────> 0x00001218      488345f801     add qword [idx], 1
│   │ ╎│└─> 0x0000121d      488b45f8       mov rax, qword [idx]
│   │ ╎│    0x00001221      483b45f0       cmp rax, qword [n]
```

En une commande, le brouillon est devenu un listing lisible : `real_check`, `idx`, `n`, et un
commentaire sur la table. C'est exactement ce qu'on veut avant d'écrire un writeup — et si vous
voulez garder le travail, `Ps <nom>` crée un projet r2 réutilisable (`Po` pour l'ouvrir).

> **Piège de syntaxe.** `afvn` prend le **nouveau** nom en premier : `afvn idx var_8h` renomme
> `var_8h` en `idx`. L'ordre inverse renvoie `ERROR: Cant find var by name` — erreur fréquente
> quand on a l'habitude de `mv ancien nouveau`.

## 8. Le décalage PIE : `0x122e` contre `0x55555555522e`

Un exécutable **PIE** (chapitre 4.2) est chargé à une adresse aléatoire. r2, par défaut, le
présente à sa **base 0** : `main` est à `0x122e`. À l'exécution, la même instruction peut être à
`0x55555555522e` ou ailleurs.

```text
$ r2 -q -c 'aaa; s main; pd 2' ./crackme
│           0x0000122e      55             push rbp
│           0x0000122f      4889e5         mov rbp, rsp
```

Adresse réelle pendant une exécution (lue dans `/proc/<pid>/maps` alors que le programme attend
sur `fgets`) :

```text
$ grep crackme /proc/$(pgrep -n crackme)/maps | head -2
5e3eefb77000-5e3eefb78000 r--p 00000000 00:138 2663263   /tmp/rev43/crackme
5e3eefb78000-5e3eefb79000 r-xp 00001000 00:138 2663263   /tmp/rev43/crackme
```

La base est `0x5e3eefb77000`, donc `main` s'exécute à `0x5e3eefb77000 + 0x122e =
0x5e3eefb7822e`. Sous `gdb`, la base est presque toujours `0x555555554000`, d'où l'adresse
`0x55555555522e` que l'on voit dans la majorité des writeups.

Trois façons de travailler avec ce décalage :

| Besoin | Solution |
| --- | --- |
| comparer avec un writeup qui utilise `0x555555554000` | `r2 -B 0x555555554000 -q -c 'aaa; s main; pd 2'` |
| calculer une adresse d'exécution | `? 0x122e + 0x555555554000` (calculateur r2) |
| désactiver le PIE pour simplifier | `gcc -no-pie` à la compilation (adresses fixes) |

```text
$ r2 -B 0x555555554000 -q -c 'aaa; s main; pd 2' ./crackme
│           0x55555555522e      55             push rbp
│           0x55555555522f      4889e5         mov rbp, rsp
```

> **Règle de writeup.** Donnez toujours les adresses **relatives au fichier** (celles de r2 par
> défaut) et précisez la base si vous montrez une adresse d'exécution. Un lecteur qui n'a pas la
> même base croira à une erreur.

## 9. Exercice pratique : un crackme strippé avec une fausse piste

### Le programme

Créer `crackme.c` :

```c
#include <stdio.h>
#include <string.h>

static int decoy_check(const char *s) {
    return strcmp(s, "not-the-key") == 0;
}

static int real_check(const char *s) {
    static const unsigned char t[] = {0x08, 0x69, 0x2c, 0x7b, 0x05, 0x1b, 0x20};
    size_t n = strlen(s);
    if (n != 7)
        return 0;
    for (size_t i = 0; i < n; i++)
        if ((unsigned char)s[i] != (t[i] ^ 0x5a))
            return 0;
    return 1;
}

int main(void) {
    char buf[64];

    printf("mot de passe: ");
    if (!fgets(buf, sizeof buf, stdin))
        return 1;
    buf[strcspn(buf, "\n")] = 0;

    if (decoy_check(buf)) {
        puts("presque...");
        return 1;
    }
    if (real_check(buf))
        puts("bravo");
    else
        puts("non");

    return 0;
}
```

```bash
gcc -O0 -s -o crackme crackme.c
file crackme
```

```text
crackme: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=c01ed298ca92341f5af650c27e4cebfedeb1659c, for GNU/Linux 3.2.0, stripped
```

Le binaire est **strippé** et contient une **fausse piste** : `not-the-key` mène à « presque... »
et à un code de retour d'échec. La vraie clé n'apparaît pas en clair (elle est masquée par un
XOR).

> Le `BuildID` et les adresses exactes (`0x1189`, `0x11b5`, `0x2036`) dépendent de votre version
> de gcc : recompilez avec la même commande et vos propres adresses feront l'affaire. Les
> **noms de commandes**, les **relations** (`main` appelle deux fonctions, la seconde fait un
> XOR avec `0x5a`) et la clé, eux, ne changent pas.

### Questions

1. Combien de fonctions internes reste-t-il ? Comment les distinguer des imports ?
2. Quelles chaînes sont visibles, et laquelle est un piège ? Comment le prouver ?
3. Quelle fonction `main` appelle-t-elle en premier, et quelle est sa condition de succès ?
4. Dans la seconde fonction, quelles sont les deux contraintes sur l'entrée ?
5. Retrouver la clé. Que se passe-t-il si on saisit `not-the-key` ?

<details>
<summary>Correction</summary>

**1. Les fonctions**

```text
$ r2 -q -c 'aaa; afl' ./crackme
0x00001030    1      6 sym.imp.puts
…
0x000010a0    1     33 entry0
0x0000122e    9    184 main
0x00001189    1     44 fcn.00001189
0x000011b5    9    121 fcn.000011b5
```

Trois fonctions internes utiles : `main` (r2 l'a nommée en remontant depuis `entry0`), et deux
`fcn.` anonymes. Les `sym.imp.*` sont les imports de la libc (adresses en `0x10xx`, dans la PLT).

**2. Les chaînes**

```text
$ r2 -q -c 'iz' ./crackme
0   0x00002004 0x00002004 11  12   .rodata ascii not-the-key
1   0x00002010 0x00002010 13  15   .rodata ascii mot de passe:
2   0x00002021 0x00002021 10  11   .rodata ascii presque...
3   0x0000202c 0x0000202c 5   6    .rodata ascii bravo
4   0x00002036 0x00002036 4   5    .rodata ascii \bi,{
```

`not-the-key` est la fausse piste. La preuve est la référence croisée :

```text
$ r2 -q -c 'aaa; axt @ 0x2004' ./crackme
fcn.00001189 0x1199 [STRN:r--] lea rdx, str.not_the_key
```

Cette chaîne n'est utilisée que par `fcn.00001189`, jamais par `main` directement. Et le message
associé n'est pas « bravo » mais « presque... », suivi de `return 1` : c'est un échec déguisé.

**3. La première fonction appelée**

```text
$ r2 -q -c 'aaa; pdf @ main~call' ./crackme
│           0x00001245      e806feffff     call sym.imp.printf         ; int printf(const char *format, ...)
│           0x0000125d      e80efeffff     call sym.imp.fgets          ; char *fgets(char *s, int size, FILE *stream)
│           0x0000127f      e8dcfdffff     call sym.imp.strcspn        ; size_t strcspn(const char *s1, const char *s2)
│           0x00001290      e8f4feffff     call fcn.00001189
│           0x000012b6      e8fafeffff     call fcn.000011b5
```

`fcn.00001189` (leurre) est appelée en premier. Si elle renvoie vrai, `main` affiche
« presque... » et sort en `1`. Sinon, `fcn.000011b5` est appelée : c'est la vraie vérification.

Sa condition de succès : `test eax, eax` puis `je 0x12d0` (« non »). Donc **non-zéro = succès**,
c'est-à-dire `return 1`.

**4. Les contraintes**

```text
$ r2 -q -c 'aaa; pdf @ 0x11b5' ./crackme
│           0x000011c8      e873feffff     call sym.imp.strlen         ; size_t strlen(const char *s)
│           0x000011cd      488945f0       mov qword [var_10h], rax
│           0x000011d1      48837df007     cmp qword [var_10h], 7
│       ┌─< 0x000011d6      7407           je 0x11df
│       │   0x000011d8      b800000000     mov eax, 0
│      ┌──< 0x000011dd      eb4d           jmp 0x122c
│      │└─> 0x000011df      48c745f800..   mov qword [var_8h], 0
│      │┌─< 0x000011e7      eb34           jmp 0x121d
│     ┌───> 0x000011e9      488b55e8       mov rdx, qword [s]
│     ╎││   0x000011ed      488b45f8       mov rax, qword [var_8h]
│     ╎││   0x000011f1      4801d0         add rax, rdx
│     ╎││   0x000011f4      0fb600         movzx eax, byte [rax]
│     ╎││   0x000011f7      89c1           mov ecx, eax
│     ╎││   0x000011f9      488d15360e..   lea rdx, str._bi_           ; 0x2036
│     ╎││   0x00001200      488b45f8       mov rax, qword [var_8h]
│     ╎││   0x00001204      4801d0         add rax, rdx
│     ╎││   0x00001207      0fb600         movzx eax, byte [rax]
│     ╎││   0x0000120a      83f05a         xor eax, 0x5a
│     ╎││   0x0000120d      38c1           cmp cl, al
│    ┌────< 0x0000120f      7407           je 0x1218
│    │╎││   0x00001211      b800000000     mov eax, 0
│   ┌─────< 0x00001216      eb14           jmp 0x122c
│   │└────> 0x00001218      488345f801     add qword [var_8h], 1
│   │ ╎│└─> 0x0000121d      488b45f8       mov rax, qword [var_8h]
│   │ ╎│    0x00001221      483b45f0       cmp rax, qword [var_10h]
│   │ └───< 0x00001225      72c2           jb 0x11e9
│   │  │    0x00001227      b801000000     mov eax, 1
│   └──└──> 0x0000122c      c9             leave
```

Deux contraintes :

- `cmp qword [var_10h], 7` + `je` : `strlen(s) == 7` ;
- boucle sur `i` : `s[i] == table[i] ^ 0x5a`, sinon `return 0`. Le `jb` (non signé) borne la
  boucle.

**5. La clé**

La table est à `0x2036` (la pseudo-chaîne `\bi,{` vue par `iz`). On la lit en octets :

```text
$ r2 -q -c 'px 16 @ 0x2036' ./crackme
- offset -  3637 3839 3A3B 3C3D 3E3F 4041 4243 4445  6789ABCDEF012345
0x00002036  0869 2c7b 051b 2000 0000 011b 033b 3c00  .i,{.. ......;<.
```

Les 7 premiers octets sont `08 69 2c 7b 05 1b 20`. Chacun XORé avec `0x5a` :

```bash
python3 -c "t=[0x08,0x69,0x2c,0x7b,0x05,0x1b,0x20]; print(''.join(chr(b^0x5a) for b in t))"
```

```text
R3v!_Az
```

```text
$ echo 'R3v!_Az' | ./crackme
mot de passe: bravo
```

Et la fausse piste :

```text
$ echo 'not-the-key' | ./crackme
mot de passe: presque...
$ echo $?
1
```

« presque... » puis code de retour `1` : le piège confirme l'échec. Un solveur pressé qui patch
`decoy_check` pour renvoyer 0 (afin d'éviter « presque... ») n'a toujours pas la clé : il faut
lire la **seconde** fonction.

**Leçon** : la chaîne visible n'est pas toujours la vérification. `axt` répond à la question en
une ligne, et `iz` montre parfois des « chaînes » qui sont en réalité des tables d'octets.

</details>

## 10. Ce que je retiens

- `objdump` fait un balayage **linéaire** : il ne sait pas ce qu'est une fonction, ni qui
  référence une donnée. r2/rizin font une analyse **récursive** et construisent le graphe d'appels.
- `r2 -q -c "cmd; cmd"` rend toute session reproductible : c'est le format à utiliser dans un
  writeup. `rizin -q -c` accepte les mêmes commandes.
- La syntaxe est `[action][cible]` : `afl`, `pdf @ main`, `iz`, `ii`, `axt @ 0x2021`.
- `?` est la documentation, `? expr` est le calculateur, `~motif` filtre.
- `axt @ <addr>` répond à « qui utilise cette chaîne ? » — c'est **la** commande qui fait gagner du
  temps sur un binaire strippé.
- `agf` produit un graphe ASCII copiable ; `VV` ouvre le même graphe en interactif, avec `f`/`t`
  sous chaque saut pour lire la branche prise ou non.
- `afn` / `afvn` / `CC` rendent un listing anonyme lisible — sans modifier le fichier.
- Un binaire PIE est vu à la base 0 par r2 : `0x122e` dans le listing, `base + 0x122e` à
  l'exécution. `-B 0x555555554000` aligne r2 sur les adresses des writeups.
- `iz` peut afficher comme « chaîne » une table d'octets : ne jamais conclure sans regarder les
  octets (`px`).

## Références

- [radare2 book](https://book.rada.re/) — référence officielle, chapitre « Visual mode »
- [rizin book](https://rizin.re/pages/manual/rizin/) — équivalent pour rizin
- [Cheat sheet r2](https://github.com/radareorg/radare2/blob/master/doc/intro.md) — commandes de
  base
- `r2 -q -c 'a?'` et `pdf?` — l'aide intégrée, toujours à jour avec votre version
