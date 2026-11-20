# 4.6 — Décompilation, patching et solveurs en CLI

> Fiche du chapitre 4.6 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- décompiler une fonction **dans le terminal** avec `pdc` (natif) et `pdg` (`r2ghidra`), et dire
  honnêtement ce que chacun apporte et ce qu'il invente ;
- **patcher** un binaire avec `radare2 -w` (`wa`, `wao nop`, `wx`) sur une **copie**, en respectant
  la **taille des instructions** ;
- vérifier un patch par l'exécution, pas par la lecture ;
- utiliser `patchelf` pour l'interpréteur et le `rpath`, et patcher quelques octets en Python ;
- automatiser l'extraction de constantes avec `r2pipe` ;
- modéliser des contraintes arithmétiques, XOR et bit-à-bit avec **`z3`**, et retrouver une clé ;
- expliquer ce qu'apporte **`angr`** (exécution symbolique) par rapport à `z3`, et quand choisir
  l'un ou l'autre.

## 1. Décompiler dans le terminal

Le désassembleur donne des instructions. Le décompilateur donne du **pseudo-C** : plus vite à lire,
mais jamais la vérité — c'est une reconstruction. Deux commandes dans `radare2` :

| Commande | Plugin | Ce qu'elle produit |
| --- | --- | --- |
| `pdc` | aucun, natif | pseudo-C de bas niveau, proche de l'assembleur |
| `pdg` | `r2ghidra` | vrai décompilateur (moteur Ghidra), types et structures inférés |

### Le binaire d'étude

```c
#include <stdio.h>
#include <string.h>

static int verifie(const char *s) {
    if (strlen(s) != 8) return 0;
    if ((unsigned char)(s[0] ^ 0x37) != 0x64) return 0;
    if ((unsigned char)(s[1] + s[2]) != 0x9c) return 0;
    if ((unsigned char)(s[2] ^ s[3]) != 0x1a) return 0;
    if ((unsigned char)(s[4] * 3) != 0x99) return 0;
    if ((unsigned char)(s[5] - s[6]) != 0x43) return 0;
    if ((unsigned char)s[7] != (unsigned char)(s[0] ^ 0x6c)) return 0;
    return 1;
}

int main(void) {
    char buf[64];

    printf("cle : ");
    if (!fgets(buf, sizeof buf, stdin))
        return 1;
    buf[strcspn(buf, "\n")] = 0;

    if (verifie(buf))
        puts("bravo");
    else
        puts("non");

    return 0;
}
```

```bash
gcc -O0 -o crackme46 crackme46.c
echo 'S0lv3d!?' | ./crackme46
echo 'abcdefgh' | ./crackme46
```

```text
cle : bravo
cle : non
```

Ce binaire sert aux deux parties de l'exercice : on va d'abord le **patcher**, puis retrouver une
clé valide **sans** le patcher.

### `pdc` : le pseudo-décompilateur natif

```bash
r2 -2 -q -c 'aaa; s sym.verifie; pdc' ./crackme46
```

```text
// callconv: rax amd64 (rdi, rsi, rdx, rcx, r8, r9, stack);
void sym.verifie (char *arg1) {
    // CALL XREF from main @ 0x12c9(x)
    push (rbp)
    rbp = rsp
    rsp -= 0x10
    qword [s] = rdi // arg1
    rax = qword [s]
    rdi = rax     // const char *s
    rax = strlen (rdi)
    v = rax - 8
    if (rax != 8) {
        eax = 0
    } else {
        // CODE XREF from sym.verifie @ 0x1195(x)
        rax = qword [s]
        eax = byte [rax]
        v = al - 0x53 // 'S'
        if (al != 0x53) {
            eax = 0
        } else {
            // ... (meme structure pour les six tests)
```

`pdc` est une **traduction ligne à ligne** : les registres restent (`rax`, `al`, `rdi`), les accès
mémoire restent (`qword [s]`, `byte [rax]`), les commentaires de r2 sont conservés. Il ne devine
ni les types ni les structures. Son avantage : il est **toujours disponible**, sans plugin, et il
ne ment jamais sur ce que fait le code — parce qu'il ne réécrit presque rien.

`-2` ferme `stderr`, où r2 écrit ses lignes `INFO:` et `HINT:` : la sortie reste propre pour un
writeup.

### `pdg` : le décompilateur Ghidra

`pdg` vient du plugin `r2ghidra`, qui embarque le décompilateur de Ghidra. Il faut l'installer
une fois :

```bash
r2pm -U
r2pm -ci r2ghidra
```

> **Ce que l'installation m'a coûté.** Le premier essai a échoué trois fois de suite, chaque fois
> sur un outil manquant — les messages sont explicites :
>
> ```text
> ERROR: R2PM_NEEDS: Cannot find unzip in PATH
> checking for pkg-config... Cannot find pkg-config or pkgconf in PATH
> ```
>
> ```bash
> sudo apt install unzip pkg-config cmake g++
> ```
>
> La compilation du moteur Ghidra prend ensuite plusieurs minutes. C'est le prix d'un vrai
> décompilateur : `pdc` est instantané, `pdg` se mérite.

```bash
r2 -2 -q -c 'aaa; s sym.verifie; pdg' ./crackme46
```

```text
ulong sym.verifie(char *arg1)

{
    int64_t iVar1;
    ulong uVar2;
    char *s;

    iVar1 = sym.imp.strlen(arg1);
    if (iVar1 == 8) {
        if (*arg1 == 'S') {
            if (arg1[2] + arg1[1] == -100) {
                if ((arg1[3] ^ arg1[2]) == 0x1a) {
                    if (arg1[4] == '3') {
                        if (arg1[5] - arg1[6] == 'C') {
                            if (arg1[7] == (*arg1 ^ 0x6cU)) {
                                uVar2 = 1;
                            }
                            else {
                                uVar2 = 0;
                            }
                        }
                        // ... (meme imbrication pour les tests suivants)
```

Le contraste est net. `pdg` a **résolu des calculs** que le code ne fait pas explicitement :

- `s[0] ^ 0x37 == 0x64` est devenu `*arg1 == 'S'` (le XOR et la constante ont été repliés) ;
- `s[4] * 3 == 0x99` est devenu `arg1[4] == '3'` (il a divisé par 3) ;
- `s[1] + s[2] == 0x9c` est affiché `== -100`, parce que `0x9c` en `int8_t` vaut `-100` — piège
  classique du **caractère signé**.

Ces simplifications sont exactes **ici**, mais elles reposent sur des hypothèses de types. Sur un
binaire moins propre, `pdg` se trompe : types inventés, variables fusionnées, boucles mal
reconstruites.

### Ce que `pdg` invente aussi

Le même `pdg` sur `main` du même binaire :

```text
ulong main(int argc,char **argv,char **envp)

{
    int iVar1;
    int64_t iVar2;
    ulong uVar3;
    char *s1;

    sym.imp.printf("cle : ");
    iVar2 = sym.imp.fgets(&s1,0x40,_reloc.stdin);
```

`buf` est déclaré `char buf[64]` dans le source, mais `pdg` en fait un `char *s1` et écrit
`&s1` : le pointeur est passé à `fgets`, donc le décompilateur en déduit un `char **`. Le code
fonctionne ; la déclaration est fausse. Plus loin, `sym.imp.puts(0x2013)` n'a pas la chaîne
résolue, alors que `puts("bravo")` juste à côté l'est.

> **Règle.** Le pseudo-C sert à **comprendre vite**. L'assembleur (`pdf`) fait toujours foi.
> Quand `pdg` et `pdf` se contredisent, c'est `pdf` qui a raison — et la contradiction elle-même
> est une information : elle indique une astuce de compilateur ou une hypothèse de type fausse.

### Choisir

| Situation | Commande |
| --- | --- |
| Pas de plugin, il faut aller vite | `pdc` |
| Fonction longue, logique à comprendre | `pdg` |
| Vérifier un détail (type, offset, saut) | `pdf` / `pd` |
| Comparer deux versions d'une fonction | `pdg` sur les deux, puis diff |

## 2. Patcher le binaire

Patcher, c'est modifier les **octets** du fichier pour changer son comportement : neutraliser un
saut, inverser une condition, remplacer un appel par une constante.

> **Règle d'or.** On patche une **copie**. Jamais l'original : une erreur d'un octet transforme un
> binaire en épave, et sans copie il n'y a plus rien à comparer. `cp crackme46 p1` avant chaque
> essai, et un nom différent par tentative.

### Repérer la cible

La cible est l'instruction qui décide. Sur `crackme46`, `objdump` la donne directement :

```text
    12c9:       e8 ab fe ff ff          call   1179 <verifie>
    12ce:       85 c0                   test   eax,eax
    12d0:       74 11                   je     12e3 <main+0x7c>
    12d2:       48 8d 05 34 0d 00 00    lea    rax,[rip+0xd34]        # 200d <_IO_stdin_used+0xd>
```

Trois cibles possibles, du plus grossier au plus fin :

| Cible | Octets | Effet du patch |
| --- | --- | --- |
| `call verifie` | `e8 ab fe ff ff` (5) | remplacer par `mov eax,1` |
| `test eax,eax` + `je` | `85 c0 74 11` (4) | supprimer le saut (NOP) |
| `je 12e3` | `74 11` (2) | inverser en `jne` (`75 11`) |

Dans `radare2`, la même information : `r2 -2 -q -c 'aaa; s main; pdf' ./crackme46`.

### Les trois commandes d'écriture

| Commande | Sens | Exemple |
| --- | --- | --- |
| `wx <hex>` | écrire des octets bruts | `wx 9090` |
| `wa <asm>` | assembler **une** instruction et l'écrire | `wa nop` |
| `wao <asm>` | idem, mais **complète** avec des `nop` jusqu'à la taille de l'ancienne | `wao nop` |

Toutes s'utilisent avec `-w` (écriture) et `s <adresse>` pour se placer.

### La règle critique : la taille des instructions

Un processeur ne connaît pas les instructions, seulement les octets. Écrire deux octets là où il y
en avait cinq ne « supprime » pas trois octets : les trois restants sont **exécutés** et, presque
toujours, ne veulent rien dire.

**Cas correct — même taille.** `je` fait 2 octets (`74 11`), deux `nop` en font 2 :

```bash
cp crackme46 p1
r2 -2 -w -q -c 's 0x12d0; wx 9090' p1
r2 -2 -q -c 's 0x12c9; pd 5' p1
```

```text
            0x000012c9      e8abfeffff     call sym.verifie
            0x000012ce      85c0           test eax, eax
            0x000012d0      90             nop
            0x000012d1      90             nop
            0x000012d2      488d05340d..   lea rax, str.bravo          ; 0x200d ; "bravo"
```

Le `test` s'exécute, les deux `nop` ne font rien, et l'exécution **tombe** sur le bloc « bravo »
quel que soit le résultat :

```bash
$ echo 'abcdefgh' | ./p1
cle : bravo
```

**Cas piégeux — `wa` n'écrit qu'une instruction.** Même cible, mais avec `wa nop` :

```bash
cp crackme46 p6
r2 -2 -w -q -c 's 0x12d0; wa nop' p6
r2 -2 -q -c 's 0x12d0; pd 2' p6
```

```text
            0x000012d0      90             nop
            0x000012d1      11488d         adc dword [rax - 0x73], ecx
```

`wa nop` a écrit **un** octet `90` et laissé le second octet du `je` (`0x11`). Résultat : une
instruction inventée `adc dword [rax-0x73], ecx`, qui lit une adresse quelconque.

```text
$ echo 'abcdefgh' | ./p6
Segmentation fault
```

**Cas correct — `wao` s'adapte.** `wao nop` remplace l'instruction entière par autant de `nop`
qu'il faut :

```bash
cp crackme46 p7
r2 -2 -w -q -c 's 0x12d0; wao nop' p7
r2 -2 -q -c 's 0x12d0; pd 3' p7
```

```text
            0x000012d0      90             nop
            0x000012d1      90             nop
            0x000012d2      488d05340d..   lea rax, str.bravo          ; 0x200d ; "bravo"
```

```text
$ echo 'abcdefgh' | ./p7
cle : bravo
```

**Cas piégeux — deux octets sur un `call` de cinq.** La même erreur, en plus visible :

```bash
cp crackme46 p4
r2 -2 -w -q -c 's 0x12c9; wx 9090' p4
r2 -2 -q -c 's 0x12c9; pd 4' p4
```

```text
            0x000012c9      90             nop
            0x000012ca      90             nop
            0x000012cb      fe             invalid
            0x000012cc      ff             invalid
```

Les trois octets restants du `call` (`ff ff ff`) forment deux instructions invalides. Le noyau
refuse de les exécuter :

```text
$ echo 'abcdefgh' | ./p4
Illegal instruction
```

Le code de retour est **132** (`128 + 4`, `SIGILL`). C'est le symptôme typique d'un patch de
mauvaise taille : `Illegal instruction` ou `Segmentation fault`, jamais un message du programme.

**Cas correct — remplacer un `call` par une constante.** `mov eax,1` fait exactement 5 octets
(`b8 01 00 00 00`), comme le `call` :

```bash
cp crackme46 p3
r2 -2 -w -q -c 's 0x12c9; wx b801000000' p3
r2 -2 -q -c 's 0x12c9; pd 5' p3
```

```text
            0x000012c9      b801000000     mov eax, 1
            0x000012ce      85c0           test eax, eax
            0x000012d0      7411           je 0x12e3
```

```text
$ echo 'abcdefgh' | ./p3
cle : bravo
```

`verifie` n'est plus appelée du tout : `eax` vaut 1, le `test` met `ZF` à 0, le `je` n'est pas
pris, on tombe sur « bravo ». Patch propre, aucune instruction décalée.

**Inverser une condition.** Pour retourner la logique au lieu de la neutraliser, un seul octet
change : `74` (`je`) devient `75` (`jne`).

```bash
cp crackme46 p2
r2 -2 -w -q -c 's 0x12d0; wx 75' p2
echo 'abcdefgh' | ./p2
```

```text
cle : bravo
```

Ici c'est une **clé fausse** qui est acceptée, et la vraie qui est refusée : la condition est
inversée, pas contournée. Utile pour comprendre, dangereux à confondre.

### Vérifier un patch

Un patch se vérifie par l'**exécution**, dans les deux sens :

```bash
echo 'abcdefgh' | ./p1     # entrée fausse -> doit afficher bravo
echo 'S0lv3d!?' | ./p1     # entrée vraie  -> doit toujours afficher bravo
```

Et par les octets, pour être sûr de ce qu'on a écrit :

```bash
r2 -2 -q -c 'px 8 @ 0x12c9' crackme46
r2 -2 -q -c 'px 8 @ 0x12c9' p5
```

```text
- offset -  C9CA CBCC CDCE CFD0 D1D2 D3D4 D5D6 D7D8  9ABCDEF012345678
0x000012c9  e8ab feff ff85 c074                      .......t
- offset -  C9CA CBCC CDCE CFD0 D1D2 D3D4 D5D6 D7D8  9ABCDEF012345678
0x000012c9  9090 9090 9085 c074                      .......t
```

À gauche l'original (`e8 ab fe ff ff` = `call`), à droite le `call` remplacé par cinq `nop`
(`90 90 90 90 90`) : le `85 c0` du `test` est intact. C'est ce qu'on veut voir.

### `patchelf` : l'éditeur d'en-têtes

Tous les patchs ne sont pas du code. `patchelf` modifie les métadonnées ELF sans désassembler :

```bash
patchelf --print-interpreter crackme46
patchelf --set-rpath '$ORIGIN/lib' demo_patch
patchelf --print-rpath demo_patch
readelf -d demo_patch | grep -E 'RPATH|RUNPATH|NEEDED'
```

```text
/lib64/ld-linux-x86-64.so.2
$ORIGIN/lib
 0x000000000000001d (RUNPATH)            Library runpath: [$ORIGIN/lib]
 0x0000000000000001 (NEEDED)             Shared library: [libc.so.6]
```

| Option | Usage |
| --- | --- |
| `--set-interpreter <chemin>` | changer le loader (utile pour un `ld.so` fourni à côté) |
| `--set-rpath <chemins>` | chercher les bibliothèques ailleurs (`$ORIGIN` = dossier du binaire) |
| `--set-soname <nom>` | renommer la bibliothèque elle-même |
| `--print-interpreter`, `--print-rpath` | vérifier |

Un interpréteur invalide rend le binaire **inexécutable** — la démonstration est immédiate :

```bash
cp crackme46 bad_interp
patchelf --set-interpreter /nonexistent/ld.so bad_interp
./bad_interp
```

```text
bash: ./bad_interp: cannot execute: required file not found
```

C'est le premier réflexe quand un binaire refuse de démarrer alors que `file` le dit valide :
`readelf -l ./binaire | grep interpreter`.

### Patcher en Python

Pour quelques octets, un script suffit et se relit :

```python
from pathlib import Path

d = bytearray(Path("crackme46").read_bytes())

# .text : offset fichier == adresse virtuelle (0x1090 == 0x1090)
assert d[0x12d0:0x12d2] == b"\x74\x11"
d[0x12d0:0x12d2] = b"\x90\x90"

Path("patched_py").write_bytes(d)
```

```bash
/usr/bin/python3 patch.py && chmod +x patched_py
echo 'abcdefgh' | ./patched_py
```

```text
cle : bravo
```

L'`assert` est la partie importante : il vérifie qu'on écrit **au bon endroit** avant d'écrire.
Sans lui, un décalage de quelques octets produit un binaire corrompu sans message d'erreur.

La correspondance entre adresse virtuelle et offset fichier se lit dans `readelf -SW` (le `W`
empêche le retour à la ligne sur un terminal étroit) :

```text
[14] .text             PROGBITS        0000000000001090 001090 000269 00  AX  0   0 16
```

La colonne 4 est l'adresse (`.text` commence à `0x1090`), la colonne 5 l'offset dans le fichier
(`0x1090`) : les deux coïncident.

Les deux colonnes sont identiques ici, donc `adresse == offset`. Ce n'est pas toujours vrai : pour
un segment dont `p_vaddr != p_offset`, il faut soustraire la base du segment.

## 3. Automatiser : `r2pipe`, `z3`, `angr`

Patcher à la main ne passe pas l'échelle. Trois briques permettent d'automatiser : un **pont**
vers radare2 (`r2pipe`), un **solveur de contraintes** (`z3`), et un **exécuteur symbolique**
(`angr`).

### `r2pipe` : piloter radare2 depuis Python

`r2pipe` lance un `radare2` en sous-processus et lui envoie des commandes. La variante `cmdj`
renvoie du **JSON déjà parsé** — plus de `grep` fragile sur une sortie texte.

```bash
pip install r2pipe
```

```python
import r2pipe

r2 = r2pipe.open("./crackme46", flags=["-2"])
r2.cmd("aaa")

for op in r2.cmdj("pdfj @ sym.verifie")["ops"]:
    if op["type"] == "cmp":
        print(f'{op["addr"]:#06x}  {op["disasm"]}')
```

```text
0x1191  cmp rax, 8
0x11a8  cmp al, 0x53
0x11d0  cmp al, 0x9c
0x11f6  cmp al, 0x1a
0x120c  cmp al, 0x33
0x1235  cmp al, 0x43
0x1255  cmp dl, al
```

En sept lignes, toutes les constantes de la vérification sont extraites, avec leur adresse. Sur un
binaire à cent fonctions, le même script liste les comparaisons de chacune — c'est la base d'un
tri automatique : les `cmp` avec un immédiat sont des candidats, les `cmp` entre deux registres
demandent une analyse plus fine.

| Commande | Retour |
| --- | --- |
| `r2.cmd("pdf @ main")` | texte brut |
| `r2.cmdj("pdfj @ main")` | dict Python (`{"ops": [...]}`) |
| `r2.cmd("s 0x1191; px 8")` | lecture d'octets |
| `r2.cmd("wx 9090 @ 0x12d0")` | écriture (avec `r2pipe.open(..., flags=["-w"])`) |

Le drapeau `-2` transmis par `flags` ferme `stderr` : sans lui, les lignes `INFO:` de `aaa`
viennent polluer la sortie du script.

### `z3` : résoudre les contraintes

`z3` est un solveur SMT : on lui décrit des contraintes, il cherche des valeurs qui les
satisfont. C'est exactement le problème d'un `verifie` comme celui-ci — huit inconnues, sept
relations.

```bash
pip install z3-solver
```

```python
from z3 import BitVec, Solver

s = [BitVec(f"s{i}", 8) for i in range(8)]
sol = Solver()

sol.add(s[0] ^ 0x37 == 0x64)
sol.add(s[1] + s[2] == 0x9c)
sol.add(s[2] ^ s[3] == 0x1a)
sol.add(s[4] * 3 == 0x99)
sol.add(s[5] - s[6] == 0x43)
sol.add(s[7] == (s[0] ^ 0x6c))

for c in s:
    sol.add(c >= 0x20, c <= 0x7e)

print("statut :", sol.check())
m = sol.model()
print("cle    :", "".join(chr(m.eval(c).as_long()) for c in s))
```

```text
statut : sat
cle    : S^>$3p-?
```

`solve()` a trouvé une clé — mais **pas** celle que j'avais en tête en écrivant le programme :

```bash
$ echo 'S^>$3p-?' | ./crackme46
cle : bravo
```

Elle fonctionne pourtant. C'est le point le plus important de cette section : **les contraintes
admettent plusieurs solutions**. `s[1] + s[2] == 0x9c` laisse 93 combinaisons de caractères
imprimables ; `s[2] ^ s[3]` en déduit une seule pour `s[3]` ; `s[5] - s[6] == 0x43` en laisse 28.
Le solveur renvoie le premier modèle, pas le « vrai » mot de passe.

Pour retrouver la clé d'origine, on **ajoute des contraintes** :

```python
sol.add(s[1] == ord("0"), s[5] == ord("d"))
```

```text
statut : sat
cle    : S0lv3d!?
```

| Élément | Pourquoi |
| --- | --- |
| `BitVec("s0", 8)` | entier 8 bits, arithmétique **modulo 256** comme en C |
| `^`, `+`, `*`, `-` | opèrent sur le bit-vecteur, avec les mêmes débordements |
| `c >= 0x20, c <= 0x7e` | restreint aux caractères imprimables |
| `sol.check()` | `sat` (solution), `unsat` (aucune), `unknown` |
| `m.eval(c)` | la valeur concrète dans le modèle trouvé |

Si on modélisait avec des entiers Python (`Int`) au lieu de `BitVec`, `s[4] * 3 == 0x99`
n'aurait pas la même signification : en 8 bits, la multiplication déborde et boucle. Le type
`BitVec` reproduit le comportement du C, c'est pour cela qu'il est indispensable ici.

### `angr` : exécution symbolique

`z3` demande de **traduire soi-même** le code en contraintes. `angr` fait ce travail : il charge
le binaire, exécute les instructions symboliquement (l'entrée est une variable, pas une valeur) et
cherche un chemin qui atteint une adresse ou une sortie donnée.

```bash
pip install angr
```

```python
import angr

proj = angr.Project("./crackme46", auto_load_libs=False)
etat = proj.factory.entry_state()
sm = proj.factory.simulation_manager(etat)

sm.explore(find=lambda s: b"bravo" in s.posix.dumps(1),
           avoid=lambda s: b"non" in s.posix.dumps(1))

print("trouve :", len(sm.found))
if sm.found:
    print("entree :", sm.found[0].posix.dumps(0))
```

```text
trouve : 1
entree : b'SJRH3\xc4\x81?\x00\x00\x00...'
```

`angr` a trouvé une entrée valide — mais deux de ses octets ne sont pas imprimables. La
vérification confirme qu'elle passe :

```bash
$ /usr/bin/python3 -c "import sys; sys.stdout.buffer.write(b'SJRH3\xc4\x81?\n')" | ./crackme46
cle : bravo
```

Le programme n'impose pas de caractères imprimables : `angr` ne l'invente pas. Pour l'exiger, il
faut contraindre l'entrée :

```python
import angr

proj = angr.Project("./crackme46", auto_load_libs=False)
entree = angr.claripy.BVS("entree", 8 * 8)
etat = proj.factory.entry_state(
    stdin=angr.SimFileStream(name="stdin", content=entree, has_end=True))
for octet in entree.chop(8):
    etat.solver.add(octet >= 0x20, octet <= 0x7e)

sm = proj.factory.simulation_manager(etat)
sm.explore(find=lambda s: b"bravo" in s.posix.dumps(1),
           avoid=lambda s: b"non" in s.posix.dumps(1))
print("entree :", sm.found[0].posix.dumps(0))
```

```text
entree : b'S`<&3|9?'
```

```bash
$ echo 'S`<&3|9?' | ./crackme46
cle : bravo
```

`BVS` crée une entrée symbolique de 8 octets, `SimFileStream` la branche sur l'entrée standard,
et les contraintes par octet limitent la recherche aux caractères affichables.

> **Installation : un piège à connaître.** Sur Python 3.13, `pip install angr` échoue sur une
> dépendance dont le `setup.py` fait `from distutils.core import setup` :
>
> ```text
> ModuleNotFoundError: No module named 'distutils'
> ```
>
> `distutils` a été retiré de la bibliothèque standard en Python 3.12. La solution qui a
> fonctionné :
>
> ```bash
> pip install "setuptools<81"        # fournit le shim distutils
> pip install --no-build-isolation angr
> ```
>
> Compter plusieurs minutes et quelques centaines de mégaoctets.

### Lequel choisir ?

| Situation | Outil |
| --- | --- |
| Extraire des constantes, adresses, chaînes en masse | `r2pipe` |
| Contraintes déjà comprises (arithmétique, XOR, comparaisons) | `z3` |
| Le chemin dépend de la bibliothèque (allocations, parsing, `strlen`) | `angr` |
| Un seul mot de passe, sept équations | `z3` — plus rapide et plus lisible |
| Un binaire de 2 Mo avec validation complexe | `angr`, éventuellement avec `z3` pour les contraintes finales |

`z3` est **déterministe et rapide** quand on sait décrire le problème ; `angr` est **automatique
mais lourd** et se perd dans les bibliothèques (`auto_load_libs=False` est presque toujours
nécessaire). En pratique, on commence par `pdg` pour lire la logique, puis `z3` si elle est
arithmétique, puis `angr` si elle ne l'est pas.

## 4. Exercice : patcher, puis résoudre

Le binaire `crackme46` de la section 1 est le sujet. Son source est donné plus haut pour que tu
puisses le compiler ; essaie d'abord de répondre **sans le relire**, uniquement avec les outils.

### Partie A — le patch

1. À quelle adresse se trouve l'instruction qui décide entre « bravo » et « non » ? Comment
   l'as-tu trouvée (`objdump`, `pdf`, `pdg`) ?
2. Donne **deux** patchs différents qui font afficher « bravo » à une clé fausse, avec les octets
   exacts et la commande `r2 -w` correspondante.
3. Un troisième patch écrit `wa nop` sur le `je`. Le binaire plante. Explique pourquoi en une
   phrase, et donne la commande qui corrige le problème.
4. Vérifie chaque patch avec une entrée fausse **et** avec la vraie clé.

### Partie B — le solveur

5. Écris un script `z3` qui modélise les contraintes de `verifie` et affiche une clé.
6. La clé obtenue n'est pas `S0lv3d!?`. Est-elle valide ? Pourquoi le solveur ne renvoie-t-il pas
   celle du source ?
7. Combien de clés imprimables satisfont les contraintes ? (indice : compte les libertés laissées
   par chaque relation.)

<details>
<summary>Correction</summary>

**1. L'instruction de décision** est `je 0x12e3` à l'adresse `0x12d0`, précédée de
`test eax, eax` à `0x12ce`. On la trouve par `objdump -d -M intel crackme46` (les trois lignes
apparaissent ensemble), par `pdf @ main` dans `radare2`, ou par `pdg` qui montre le
`if (iVar1 == 0)` correspondant.

**2. Deux patchs qui marchent** — tous deux de taille correcte :

```bash
# a) neutraliser le saut : je (74 11) -> deux nop
cp crackme46 p1
r2 -2 -w -q -c 's 0x12d0; wx 9090' p1

# b) remplacer l'appel par une constante : call (5 octets) -> mov eax,1 (5 octets)
cp crackme46 p3
r2 -2 -w -q -c 's 0x12c9; wx b801000000' p3
```

```text
$ echo 'abcdefgh' | ./p1
cle : bravo
$ echo 'abcdefgh' | ./p3
cle : bravo
```

Un troisième patch valable : inverser le saut (`wx 75` à `0x12d0`), mais il accepte alors les
clés fausses **et refuse** les vraies — ce n'est pas la même chose qu'un contournement.

**3. `wa nop` sur le `je`** n'écrit qu'un octet `90` et laisse le second octet (`0x11`) en place.
La séquence devient `90 11`, qui se décode en `nop` puis `adc dword [rax-0x73], ecx` : une
instruction qui lit une adresse arbitraire, d'où le `Segmentation fault`. La commande correcte est
`wao nop`, qui complète avec des `nop` jusqu'à la taille de l'instruction remplacée.

**4. Vérification** :

```bash
echo 'abcdefgh' | ./p1   # entrée fausse
echo 'S0lv3d!?' | ./p1   # vraie clé
```

Les deux doivent afficher `bravo`. Si la seconde échoue, le patch a cassé quelque chose.

**5. Le script `z3`** est celui de la section 3, et il donne :

```text
statut : sat
cle    : S^>$3p-?
```

**6. La clé `S^>$3p-?` est valide** :

```bash
$ echo 'S^>$3p-?' | ./crackme46
cle : bravo
```

Vérification à la main : `'S' ^ 0x37 = 0x64` ✔, `0x5e + 0x3e = 0x9c` ✔, `0x3e ^ 0x24 = 0x1a` ✔,
`'3' * 3 = 0x99` ✔, `0x7c - 0x39 = 0x43` ✔, `'?' = 'S' ^ 0x6c` ✔.

Le solveur ne renvoie pas `S0lv3d!?` parce que **rien dans le binaire ne distingue les deux** : le
programme ne teste que ces six relations. `S0lv3d!?` est la chaîne que l'auteur avait en tête, pas
une propriété du code. C'est une leçon de fond : un crackme peut avoir plusieurs clés, et la
« bonne » n'est pas nécessairement celle du source.

**7. Nombre de solutions imprimables.** Chaque relation laisse des degrés de liberté :

| Relation | Liberté |
| --- | --- |
| `s[0]` fixé par `^ 0x37 == 0x64` | 1 valeur (`'S'`) |
| `s[1] + s[2] == 0x9c` | `s[1]` de `0x20` à `0x7c` → 93 couples |
| `s[2] ^ s[3] == 0x1a` | `s[3]` déterminé par `s[2]` → aucun |
| `s[4] * 3 == 0x99` | 1 valeur (`'3'`) |
| `s[5] - s[6] == 0x43` | `s[5]` de `0x63` à `0x7e` → 28 couples |
| `s[7] == s[0] ^ 0x6c` | 1 valeur (`'?'`) |

Soit `93 × 28 = 2604` clés imprimables. Toutes passent le `verifie`. Pour n'en garder qu'une, il
faut ajouter des contraintes — c'est ce que fait `sol.add(s[1] == ord("0"), s[5] == ord("d"))`.

</details>

## 5. Ce que je retiens

- `pdc` est **natif** et reste au niveau des registres : il ne se trompe pas, mais il ne simplifie
  rien. `pdg` (plugin `r2ghidra`) produit du pseudo-C lisible et **replie les calculs**
  (`s[0] ^ 0x37 == 0x64` devient `*arg1 == 'S'`).
- `pdg` **invente des types** : `char buf[64]` peut devenir `char *s1` avec `&s1`. Le pseudo-C
  sert à comprendre ; `pdf` fait foi.
- `r2pm -ci r2ghidra` exige `cmake`, `g++`, `pkg-config`, `unzip` et quelques minutes de
  compilation. Les messages d'erreur disent exactement ce qui manque.
- On patche **une copie**, et on vérifie par l'exécution **et** par `px`.
- **La taille compte.** `je` = 2 octets, `call` = 5, `mov eax,1` = 5, `nop` = 1. Un patch plus
  court laisse des octets exécutés en trop : `Illegal instruction` (`SIGILL`, code 132) ou
  `Segmentation fault` (code 139).
- `wa` écrit **une** instruction, `wao` **remplit** jusqu'à la taille de l'ancienne : c'est `wao`
  qu'il faut pour remplacer une instruction par des `nop`.
- `patchelf` modifie les en-têtes (interpréteur, `rpath`) ; un interpréteur invalide donne
  `cannot execute: required file not found`.
- En Python, `bytearray` + `assert` sur les octets attendus est un patch sûr et relisible ;
  `adresse virtuelle == offset` seulement si `.text` a `p_vaddr == p_offset` (`readelf -S`).
- `r2pipe` + `cmdj` transforme radare2 en bibliothèque : extraction de constantes, de chaînes, de
  références, sans `grep`.
- `z3` avec `BitVec(…, 8)` reproduit l'arithmétique modulo 256 du C. Un modèle `sat` est **une**
  solution : si le binaire admet plusieurs clés, il en renvoie une, pas celle du source.
- `angr` exécute symboliquement le binaire : ni traduction manuelle des contraintes, ni
  connaissance des offsets. Il faut contraindre l'entrée (`BVS` + `SimFileStream`) pour obtenir
  des caractères imprimables, et `auto_load_libs=False` pour éviter de s'enliser dans libc.
- L'ordre de travail qui marche : `pdg` pour comprendre → `z3` si c'est arithmétique → `angr` si
  le chemin dépend de la bibliothèque → patch `r2 -w` pour prouver le contournement.

## Références

- [radare2 book — Décompilation](https://book.rada.re/) et `pdc?`, `pdg?` dans r2
- [r2ghidra](https://github.com/radareorg/r2ghidra) — plugin `pdg`
- [patchelf](https://github.com/NixOS/patchelf) — documentation des options
- [z3 — guide officiel](https://microsoft.github.io/z3guide/) — `BitVec`, `Solver`, modèles
- [angr — documentation](https://docs.angr.io/) — `explore`, `SimFileStream`, `posix.dumps`
- [r2pipe](https://github.com/radareorg/radare2-r2pipe) — API Python, `cmd` / `cmdj`
- Chapitre [4.4 — Désassemblage](04-desassemblage-radare2-rizin.md) : `pdf`, `px`, `aaa`
- Chapitre [4.5 — Analyse dynamique](05-analyse-dynamique-gdb-strace.md) : `gdb` et `ltrace`

