# 4.8 — Méthodologie complète et autres formats

> Fiche du chapitre 4.8 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- dérouler une analyse en **cinq phases** (triage, cartographie, dynamique, résolution, rédaction)
  et savoir ce que chaque phase doit produire ;
- choisir le **premier outil** à lancer selon ce que je vois (`file`, `strings`, un arrêt sous
  `gdb`, un `.exe`, un `.jar`, un binaire Go…) ;
- analyser en CLI un **`.pyc`** Python, un **PE** Windows, un **`.class` / `.jar`** Java, un binaire
  **Go**, et savoir où commencer sur un **APK** ;
- résoudre un crackme **`-O2 -s`** de bout en bout : constantes repliées, boucle vectorisée,
  contraintes extraites et vérifiées avec `z3` ;
- écrire un writeup **reproductible** : commandes exactes, sorties réelles, échecs documentés.

Les sections 3.1 à 3.4 ont été exécutées sur Debian 13 (`python3.13`, `mingw-w64`, `openjdk 21`,
`go 1.24`, `radare2`, `z3`). La section 3.5 (APK) est une présentation : `apktool` et `jadx` ne sont
pas installés ici, et je le dis plutôt que d'inventer des sorties.

## 1. Les cinq phases

Un reverse ne commence pas par `r2` et ne finit pas par la clé trouvée. Il commence par une fiche
d'identité et finit par un texte qu'un autre peut rejouer.

| Phase | Question | Outils | Livrable |
| --- | --- | --- | --- |
| 1. Triage | Qu'est-ce que c'est ? Est-ce que ça tourne ? Que dit-il ? | `file`, `sha256sum`, `strings`, `readelf -h/-l`, exécution | fiche d'identité + messages visibles |
| 2. Cartographie | Où est la logique ? | `r2` : `aaa`, `afl`, `iz`, `axt`, `pdf`, `pdc`/`pdg` | fonctions candidates, chaînes utiles |
| 3. Dynamique | Que se passe-t-il vraiment à l'exécution ? | `strace`, `ltrace`, `gdb` (`break`, `x/s`, `watch`) | valeurs observées, chemin réel |
| 4. Résolution | Comment obtenir la clé, ou contourner le test ? | `z3`, script Python, `r2 -w`, `angr` | clé ou patch + preuve d'exécution |
| 5. Rédaction | Comment un autre refait-il tout ? | Markdown, captures, hash, versions | writeup reproductible |

### Phase 1 — le triage élimine les faux chemins

```bash
cible=/bin/true          # n'importe quel binaire ; ici un exemple du système
sha256sum "$cible"
file "$cible"
strings -a -n 6 "$cible" | head -6
readelf -h "$cible" | grep -E 'Type|Entry|Machine'
readelf -l "$cible" | grep -E 'INTERP|GNU_STACK|GNU_RELRO'
"$cible"; echo "rc=$?"   # et si ça ne tourne pas ? (mauvaise archi, lib manquante)
```

```text
b381cc8c55ec524b9fa92897f0882e855357468b4a763519cec47e05994d61ff  /bin/true
/bin/true: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=97b6cb54883633ece766a29e7c3ecd37adfe567b, for GNU/Linux 3.2.0, stripped
V{/lib64/ld-linux-x86-64.so.2
nl_langinfo
error_message_count
program_invocation_short_name
fputc_unlocked
dcgettext
  Type:                              DYN (Position-Independent Executable file)
  Machine:                           Advanced Micro Devices X86-64
  Entry point address:               0x27e0
  INTERP         0x0000000000000394 0x0000000000000394 0x0000000000000394
  GNU_STACK      0x0000000000000000 0x0000000000000000 0x0000000000000000
  GNU_RELRO      0x0000000000009bb0 0x0000000000009bb0 0x0000000000009bb0
rc=0
```

Trois informations décident de la suite :

- **architecture et linkage** : `x86-64` + `dynamically linked` ≠ `i386` + `statically linked` ;
- **strippé ou non** : `stripped` dans la sortie de `file` (voir [4.7](07-anti-analyse-et-obfuscation.md)) ;
- **ce que le programme affiche** : les messages visibles sont les meilleurs points d'ancrage pour
  la phase 2 (`iz~<message>` puis `axt`).

Le hash sert au writeup : il identifie le binaire exact dont on parle.

### Phase 2 — cartographier avant de cliquer

```bash
cible=/bin/true
r2 -2 -q -c 'aaa; afl' "$cible" | head -5     # fonctions reconnues
r2 -2 -q -c 'aaa; iz~error' "$cible"          # chaînes intéressantes + adresses
r2 -2 -q -c 'aaa; axt @ 0x70e1' "$cible"      # qui lit « write error »
r2 -2 -q -c 'aaa; s main; pdf' "$cible" | head -4
```

```text
0x00002030    1      6 sym.imp.free
0x00002040    1      6 sym.imp.__vfprintf_chk
0x00002050    1      6 sym.imp.abort
0x00002060    1      6 sym.imp.__errno_location
0x00002070    1      6 sym.imp.strncmp
16  0x000070e1 0x000070e1 11  12   .rodata ascii write error
19  0x000070fb 0x000070fb 20  21   .rodata ascii Unknown system error
(nofunc) 0x2c6e [STRN:r--] lea rsi, str.write_error
            ; DATA XREF from entry0 @ 0x27f4(r)
┌ 198: int main (int argc, char **argv, char **envp);
│ `- args(rdi, rsi, rcx)
│           0x00002710      f30f1efa       endbr64
```

Notez le `(nofunc)` : la référence existe, mais `r2` n'a pas identifié de fonction à cet endroit.
C'est exactement pourquoi la phase 2 produit une **liste de candidats**, pas une vérité.

Objectif : une liste courte de **fonctions candidates**. Sur un binaire de 20 ko, c'est `main` plus
deux ou trois fonctions. Sur un binaire Go de 2 Mo, il faut filtrer (section 3.4).

### Phase 3 — la dynamique confirme, elle ne devine pas

La phase 2 propose une hypothèse (« la comparaison est ici ») ; la phase 3 la **vérifie** : quel
`strcmp`, avec quels arguments, dans quel ordre. C'est aussi la phase qui révèle ce que le statique
cache : chaînes déchiffrées, anti-debug, valeur réelle d'un calcul.

### Phase 4 — une seule preuve compte : l'exécution

Une clé trouvée n'est pas une clé gagnée. On la passe au binaire — `echo 'LA_CLE' | ./cible` — et
on garde la sortie : c'est la seule preuve qui compte dans le writeup.

Et si on a patché, on vérifie **les deux** : le patch tourne hors debugger, et il tourne sous
debugger (voir [4.7](07-anti-analyse-et-obfuscation.md#34-contournement-3--patcher-le-binaire)).
La section 4 le fait pour de vrai, avec un binaire et deux clés différentes.

### Phase 5 — le carnet de bord devient le writeup

Pendant l'analyse, on note les commandes **et** leurs sorties, y compris les essais ratés. Un
writeup qui ne montre que le chemin gagnant n'apprend rien. La structure attendue dans ce dépôt est
décrite dans [`writeups/README.md`](../../writeups/README.md).

## 2. Choisir le premier outil

| Ce que j'observe | Premier réflexe | Chapitre |
| --- | --- | --- |
| `file` : `stripped` | point d'entrée → `rdi` de `__libc_start_main` | [4.7](07-anti-analyse-et-obfuscation.md) |
| `strings` ne montre aucun message | chaînes XORées / stack strings → dynamique | [4.7](07-anti-analyse-et-obfuscation.md) |
| arrêt immédiat sous `gdb` | anti-debug `ptrace` / `TracerPid` | [4.7](07-anti-analyse-et-obfuscation.md) |
| `strings` contient `UPX!` | `upx -d` (ou réparer la signature) | [4.7](07-anti-analyse-et-obfuscation.md) |
| `ltrace` muet | binaire statique : `strace`, `iz` + `axt` | [4.7](07-anti-analyse-et-obfuscation.md) |
| comparaisons avec des constantes | extraire et modéliser avec `z3` | [4.6](06-decompilation-cli-patching-z3.md) |
| chemin qui dépend de la libc | `angr` (exécution symbolique) | [4.6](06-decompilation-cli-patching-z3.md) |
| fichier `.pyc` | `dis` + `marshal` | §3.1 |
| `.exe`, `.dll` | `objdump -p`, `strings -e l`, `pefile` | §3.2 |
| `.jar`, `.class` | `unzip -l`, `javap -c -p` | §3.3 |
| binaire de plusieurs Mo, `runtime.` partout | Go : `afl~main.` | §3.4 |
| `.apk` | `unzip -l`, `apktool`, `jadx` | §3.5 |

Et trois impasses à reconnaître tout de suite :

- `ltrace` sur un binaire statique : « Couldn't find .dynsym » ;
- `upx -d` sur un stub réécrit : il n'y a rien à décompresser avec l'outil standard ;
- `nm` sur un binaire `-s` : il n'y a plus de table de symboles, ce n'est pas une erreur de commande.

## 3. Autres formats

Le raisonnement ne change pas : trouver la comparaison, lire les valeurs. Ce qui change, c'est
l'outil et le conteneur.

### 3.1 Python : `.pyc`

Un `.pyc` est du **bytecode CPython** : un en-tête de 16 octets, puis un objet `code` sérialisé
avec `marshal`. Pas besoin de décompiler pour lire les constantes.

```bash
mkdir -p ~/rev-lab/48 && cd ~/rev-lab/48

cat > verif.py <<'EOF'
import sys

CIBLE = [0x59, 0x19, 0x49, 0x58, 0x4F, 0x5E]


def controle(cle):
    if len(cle) != len(CIBLE):
        return False
    return all(ord(c) ^ 0x2a == v for c, v in zip(cle, CIBLE))


if __name__ == "__main__":
    entree = sys.argv[1] if len(sys.argv) > 1 else ""
    print("bravo" if controle(entree) else "non")
EOF

/usr/bin/python3 verif.py 's3cret'
/usr/bin/python3 -m py_compile verif.py
file __pycache__/verif.cpython-313.pyc
```

```text
bravo
__pycache__/verif.cpython-313.pyc: Byte-compiled Python module for CPython 3.13 (magic: 3571), timestamp-based, .py timestamp: Fri Nov 20 22:35:17 2026 UTC, .py size: 326 bytes
```

`magic: 3571` = `0x0df3` : c'est la version du bytecode. Un `.pyc` compilé pour 3.13 ne se charge
pas dans 3.11 — c'est le premier piège des challenges Python.

```python
import dis, marshal

with open("__pycache__/verif.cpython-313.pyc", "rb") as f:
    entete = f.read(16)            # magic (4) + flags (4) + mtime (4) + taille source (4)
    code = marshal.load(f)

print("magic :", entete[:4].hex())
print("constantes du module :", code.co_consts[:3])
print()
dis.dis(code)
```

```text
magic : f30d0d0a
constantes du module : (0, None, (89, 25, 73, 88, 79, 94))

  3           BUILD_LIST               0
              LOAD_CONST               2 ((89, 25, 73, 88, 79, 94))
              LIST_EXTEND              1
              STORE_NAME               1 (CIBLE)
...
Disassembly of <code object controle at 0x76747b1278a0, file "verif.py", line 6>:
  9   L1:     LOAD_GLOBAL              5 (all + NULL)
              LOAD_CONST               2 (<code object <genexpr> ...>)
...
Disassembly of <code object <genexpr> at 0x76747afedce0, file "verif.py", line 9>:
   9           RETURN_GENERATOR
...
               LOAD_GLOBAL              1 (ord + NULL)
               LOAD_FAST                1 (c)
               CALL                     1
               LOAD_CONST               0 (42)
               BINARY_OP               12 (^)
               LOAD_FAST                2 (v)
               COMPARE_OP              72 (==)
               YIELD_VALUE              0
```

Le bytecode dit tout : table `(89, 25, 73, 88, 79, 94)`, `ord(c) ^ 42`, comparaison. Il ne reste
qu'à inverser :

```python
import marshal

with open("__pycache__/verif.cpython-313.pyc", "rb") as f:
    f.read(16)
    code = marshal.load(f)

cible = next(c for c in code.co_consts if isinstance(c, tuple))
print("cible :", cible)
print("clair :", bytes(v ^ 0x2A for v in cible).decode())
```

```text
cible : (89, 25, 73, 88, 79, 94)
clair : s3cret
```

> **Piège vécu.** `marshal.load(f)` sans `f.read(16)` d'abord donne
> `EOFError: EOF read where not expected` : `marshal` commence à lire l'en-tête comme si c'était un
> objet. Les 16 octets doivent être sautés.

`uncompyle6` / `decompyle3` ne suivent pas toujours les nouvelles versions ; `dis` et `marshal`
sont dans la bibliothèque standard, donc toujours alignés sur l'interpréteur qui a produit le
fichier. C'est l'outil fiable, même s'il demande de lire du bytecode.

### 3.2 Windows : un PE analysé depuis Linux

Pas besoin de Windows : `objdump`, `strings` et `pefile` lisent un PE, et `mingw-w64` en fabrique
un pour s'entraîner.

```bash
cat > demo.c <<'EOF'
#include <stdio.h>
#include <string.h>
#include <wchar.h>

int main(void) {
    char nom[32];
    const wchar_t *msg = L"indice UTF-16 : P3-S3cret";

    wprintf(L"%ls\n", msg);
    printf("nom : ");
    if (!fgets(nom, sizeof nom, stdin))
        return 1;
    nom[strcspn(nom, "\n")] = 0;
    puts(strcmp(nom, "P3-S3cret") == 0 ? "bravo" : "non");
    return 0;
}
EOF

x86_64-w64-mingw32-gcc -O0 -o demo.exe demo.c
```

```text
$ file demo.exe
demo.exe: PE32+ executable for MS Windows 5.02 (console), x86-64, 18 sections
```

**Les chaînes UTF-16 sont invisibles pour `strings` par défaut.** C'est le piège numéro un du PE :

```text
$ strings -a demo.exe | head -5
!This program cannot be run in DOS mode.
.text
`.data
.rdata
@.pdata

$ strings -a -e l demo.exe | head -5
indice UTF-16 : P3-S3cret
(null)
%*.*S
%-*.*S
%.*S
```

`-e l` = little-endian 16 bits. Sans lui, `L"..."` (donc `wchar_t` sur Windows) reste illisible.

**Les en-têtes et les imports** :

```text
$ objdump -p demo.exe | sed -n '1,12p'
demo.exe:     file format pei-x86-64

Characteristics 0x26
        executable
        line numbers stripped
        large address aware

Time/Date               Fri Nov 20 22:35:33 2026
Magic                   020b    (PE32+)
MajorLinkerVersion      2
MinorLinkerVersion      44

$ objdump -p demo.exe | grep -A3 'DLL Name' | head -4
        DLL Name: KERNEL32.dll
        vma:     Ordinal  Hint  Member-Name  Bound-To
        000111f8  <none>  0124  DeleteCriticalSection
        00011200  <none>  014a  EnterCriticalSection
```

`Magic 020b` = PE32+ (64 bits) ; `010b` serait PE32 (32 bits). Les DLL importées disent le style du
programme : `KERNEL32` + `msvcrt` = programme console MinGW classique.

**Le code**, avec ses adresses typiques (`0x140000000` = base par défaut d'un exe 64 bits) :

```text
$ objdump -d -M intel demo.exe | sed -n '/<main>:/,+5p'
00000001400014f8 <main>:
   1400014f8:   55                      push   rbp
   1400014f9:   48 89 e5                mov    rbp,rsp
   1400014fc:   48 83 ec 50             sub    rsp,0x50
   140001500:   e8 6b 01 00 00          call   140001670 <__main>
   140001505:   48 8d 05 f4 aa 00 00    lea    rax,[rip+0xaaf4]        # 14000c000 <.rdata>
```

`objdump` retrouve les symboles MinGW (`<main>`, `<__main>`) : un PE compilé par MinGW **n'est pas
strippé** par défaut. `radare2` les voit aussi :

```text
$ r2 -2 -q -c 'aaa; afl~main' demo.exe
0x1400013f0    1     29 dbg.mainCRTStartup
0x140001180   26    554 dbg.__tmainCRTStartup
0x14000a2d0    1      6 sym.__getmainargs
0x1400014f8    7    192 sym.main
0x140001670    3     26 dbg.__main
```

**Et avec `pefile`**, pour les en-têtes et les imports en Python :

```python
import pefile

pe = pefile.PE("demo.exe", fast_load=True)
pe.parse_data_directories(
    directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
)
print("machine :", hex(pe.FILE_HEADER.Machine), "| sous-systeme :", pe.OPTIONAL_HEADER.Subsystem)
print("imagebase :", hex(pe.OPTIONAL_HEADER.ImageBase))
for dll in pe.DIRECTORY_ENTRY_IMPORT:
    print(dll.dll.decode(), "->", ", ".join(i.name.decode() for i in dll.imports[:6]))
```

```text
machine : 0x8664 | sous-systeme : 3
imagebase : 0x140000000
KERNEL32.dll -> DeleteCriticalSection, EnterCriticalSection, GetLastError, InitializeCriticalSection, IsDBCSLeadByteEx, LeaveCriticalSection
msvcrt.dll -> fwprintf, __C_specific_handler, ___lc_codepage_func, ___mb_cur_max_func, __getmainargs, __initenv
```

`0x8664` = AMD64, sous-système `3` = console (`2` = GUI). Une comparaison de clé apparaîtrait dans
les imports sous forme de `strcmp` ou dans le code sous forme de `cmp`.

> Pour aller plus loin côté Windows, `speakeasy` émule un PE et journalise les API appelées ; c'est
> du Python en CLI, comme tout le reste de ce module. Les bases d'assembleur nécessaires sont au
> chapitre [4.3](03-assembleur-x86-64.md).

### 3.3 Java : `.class` et `.jar`

Un `.class` contient du bytecode **JVM** avec les noms de classes, de méthodes et de champs. Un
`.jar` est un zip de `.class` plus un manifeste.

```bash
cat > Verif.java <<'EOF'
public class Verif {
    static final int[] CIBLE = {89, 25, 73, 88, 79, 94};

    static boolean controle(String cle) {
        if (cle.length() != CIBLE.length)
            return false;
        for (int i = 0; i < CIBLE.length; i++)
            if ((cle.charAt(i) ^ 0x2a) != CIBLE[i])
                return false;
        return true;
    }

    public static void main(String[] args) {
        String entree = args.length > 0 ? args[0] : "";
        System.out.println(controle(entree) ? "bravo" : "non");
    }
}
EOF

javac Verif.java
java Verif s3cret
jar cf verif.jar Verif.class
unzip -l verif.jar
```

```text
bravo
Archive:  verif.jar
  Length      Date    Time    Name
---------  ---------- -----   ----
       55  2026-11-20 22:35   META-INF/MANIFEST.MF
      907  2026-11-20 22:35   Verif.class
---------                     -------
      962                     3 files
```

`unzip -l` suffit à lister ; `unzip -o verif.jar -d out/` extrait. Puis `javap`, livré avec le JDK :

```text
$ javap -c -p -cp . Verif | sed -n '/controle/,/^$/p'
  static boolean controle(java.lang.String);
    Code:
       0: aload_0
       1: invokevirtual #7                  // Method java/lang/String.length:()I
       4: getstatic     #13                 // Field CIBLE:[I
       7: arraylength
       8: if_icmpeq     13
      11: iconst_0
      12: ireturn
      13: iconst_0
      14: istore_1
      ...
      25: invokevirtual #19                 // Method java/lang/String.charAt:(I)C
      28: bipush        42
      30: ixor
      31: getstatic     #13                 // Field CIBLE:[I
```

`bipush 42` puis `ixor` : c'est le `^ 0x2a`. Reste à trouver la table, dans l'initialiseur statique :

```text
$ javap -c -p -cp . Verif | sed -n '/static {};/,/^$/p'
static {};
    Code:
       0: bipush        6
       2: newarray       int
       4: dup
       5: iconst_0
       6: bipush        89
       8: iastore
       9: dup
      10: iconst_1
      11: bipush        25
      13: iastore
      ...
      31: bipush        94
      33: iastore
      34: putstatic     #13                 // Field CIBLE:[I
```

Les six valeurs sont là, en clair : `89 25 73 88 79 94`, XOR `42` → `s3cret`. Sur un vrai `.jar`
obfusqué (ProGuard), les noms deviennent `a`, `b`, `c` — mais `javap -c -p` continue de montrer les
constantes et le flot.

### 3.4 Go : des binaires énormes, mais bavards

Un binaire Go embarque le runtime complet : garbage collector, ordonnanceur, réflexion. Résultat :
plusieurs mégaoctets et des milliers de fonctions qui n'ont rien à voir avec le programme.

```bash
mkdir -p gocheck && cd gocheck

cat > main.go <<'EOF'
package main

import (
	"fmt"
	"os"
)

var cible = []byte{89, 25, 73, 88, 79, 94}

func controle(cle string) bool {
	if len(cle) != len(cible) {
		return false
	}
	for i := 0; i < len(cible); i++ {
		if cle[i]^0x2a != cible[i] {
			return false
		}
	}
	return true
}

func main() {
	entree := ""
	if len(os.Args) > 1 {
		entree = os.Args[1]
	}
	if controle(entree) {
		fmt.Println("bravo")
	} else {
		fmt.Println("non")
	}
}
EOF

go mod init gocheck
go build -o ../gocheck.bin .
cd ..

./gocheck.bin s3cret
file gocheck.bin
```

```text
bravo
gocheck.bin: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, BuildID[sha1]=ed5f18861599471c37d5f334276c47c57446bebc, with debug_info, not stripped
```

2,2 Mo pour un `if` : c'est le runtime. Et l'analyse coûte cher :

```text
$ time r2 -2 -q -c 'aa; afl' gocheck.bin | wc -l
1792

real    0m39.601s
```

**1792 fonctions et 40 secondes** pour `aa` seul. D'où la règle : sur un binaire Go, on **filtre
avant d'analyser**.

```text
$ r2 -2 -q -c 'aa; afl~main.' gocheck.bin
0x00439460    5     34 sym.runtime.main.func2
0x004640a0    3     50 sym.runtime.main.func1
0x00491ac0   14    241 sym.main.main
```

Le paquet et la fonction sont dans le nom (`sym.main.main`) : c'est le gros avantage de Go. Mieux,
`pdf` retrouve les **lignes de source** dans la table `pclntab` :

```text
$ r2 -2 -q -c 'aa; s sym.main.main; pdf' gocheck.bin | grep -E 'main.go|xor r10d'
│       ┌─> 0x00491ac0      493b6610       cmp rsp, qword [r14 + 0x10] ; main.go:22func main() {
│      │╎   0x00491ad2      48833dcec7..   cmp qword [0x0055e2a8], 1   ; main.go:24if len(os.Args) > 1 { ; [0x55e2a8:8]=0
│     ││╎   0x00491ae3      4c8b4218       mov r8, qword [rdx + 0x18]  ; main.go:25entree = os.Args[1]
│    └────> 0x00491af2      4c8b0d2f78..   mov r9, qword [0x00559328]  ; main.go:11if len(cle) != len(cible) { ; [0x559328:8]=6
...
│  ╎╎│╎│╎   0x00491b58      4183f22a       xor r10d, 0x2a              ; 42
```

`xor r10d, 0x2a` annoté `main.go:15if cle[i]^0x2a != cible[i] {` : on lit presque le source. Avec
`aa`, la boucle de comparaison se trouve en quelques secondes.

**Les chaînes sont un piège.** Go ne termine pas ses chaînes par un NUL : elles sont regroupées dans
un gros bloc, et `strings` découpe au hasard dedans.

```text
$ r2 -2 -q -c 'iz' gocheck.bin | wc -l
2481
$ strings -a gocheck.bin | wc -l
24809
$ strings -a -n 20 gocheck.bin | grep -m3 'runtime\.'
*runtime.errorString
*[]runtime.ptabEntry
*[]*runtime.initTask
```

Dix fois plus de lignes avec `strings`, et des fragments qui n'ont pas de sens isolément : les noms
de types Go (`*runtime.errorString`) sont collés les uns aux autres. `iz` reste préférable pour
chercher un message applicatif.

**Go « strippé ».** `go build -ldflags="-s -w"` retire la table de symboles ELF :

```text
$ (cd gocheck && go build -ldflags="-s -w" -o ../gocheck_strip .)
$ file gocheck_strip
gocheck_strip: ELF 64-bit LSB executable, x86-64, version 1 (SYSV), statically linked, BuildID[sha1]=cdd484e7f0c749919571dfc17e64870befc00105, stripped
$ nm gocheck_strip
nm: gocheck_strip: no symbols
```

Mais les **noms de fonctions sont toujours là**, dans la `pclntab` (le runtime en a besoin pour les
traces) :

```text
$ strings -a gocheck_strip | grep -E 'main\.(main|controle)'
main.main
main.controle
```

Seulement `r2` ne les associe plus aux adresses avec `aa` : `afl~main` ne renvoie rien. Pour ce cas,
il faut un outil qui relit la `pclntab` (`redress`, `GoReSym`) ou chercher la chaîne et remonter par
`axt`.

> **Note d'outil.** `aaa` sur un binaire Go affiche parfois `Usage: a:autoname [subcmd]` : une
> commande d'analyse interne bute sur le format Go. `aa` suffit et va deux fois plus vite.

### 3.5 Android : `.apk` (présentation)

Un APK est un zip avec une structure fixe. Je n'ai pas `apktool` ni `jadx` sur cette machine :
voici le parcours standard, à exécuter chez vous.

| Élément | Contenu | Outil |
| --- | --- | --- |
| `classes.dex` | bytecode Dalvik | `jadx`, `apktool` (smali), `d2j-dex2jar` |
| `AndroidManifest.xml` | XML **binaire** | `apktool d` (le décode), `aapt2 dump` |
| `resources.arsc` | table de ressources compilée | `apktool`, `aapt2` |
| `lib/<abi>/*.so` | bibliothèques natives | tout ce module (ELF) |
| `META-INF/` | signature | `apksigner verify`, `keytool` |

```text
unzip -l app.apk                       # inventaire, sans rien installer
apktool d app.apk -o app_dec           # smali + manifeste lisible + ressources
jadx -d app_src app.apk                # pseudo-Java lisible
jadx-gui app.apk                       # navigation graphique
```

Ordre de travail : `unzip -l` pour voir s'il y a des `.so` (alors une partie du travail est du
reverse ELF, comme dans ce module), `jadx` pour le code Java/Kotlin, `apktool` quand il faut
**modifier** puis reconstruire (`apktool b`). Un APK protégé (DexGuard, packing) demandera de
dumper le dex en mémoire — même logique que le dump d'un binaire UPX, mais côté Android.

## 4. Exercice final : le boss, en cinq phases

Dernier programme du module : `-O2 -s`, trois contrôles successifs, aucune chaîne secrète. La clé
intuitive est `R3v3rs3!` — mais ce n'est pas la seule. On va le prouver.

```bash
mkdir -p ~/rev-lab/boss && cd ~/rev-lab/boss

cat > boss.c <<'EOF'
#include <stdio.h>
#include <string.h>

static int etape1(const char *s) {
    if (strlen(s) != 8) return 0;
    if ((s[0] ^ 0x13) != 0x41) return 0;
    if (s[1] + s[2] != 0xa9) return 0;
    if ((unsigned char)s[3] * 3 != 0x99) return 0;
    return 1;
}

static int etape2(const char *s) {
    if ((s[4] & 0x0f) != 0x02) return 0;
    if (s[5] != s[4] + 1) return 0;
    if ((s[6] | 0x20) != 0x33) return 0;
    if (s[7] != 0x21) return 0;
    return 1;
}

static int somme(const char *s) {
    int t = 0;
    for (int i = 0; i < 8; i++)
        t += (unsigned char)s[i];
    return t;
}

int main(void) {
    char buf[64];

    printf("cle : ");
    if (!fgets(buf, sizeof buf, stdin))
        return 1;
    buf[strcspn(buf, "\n")] = 0;

    if (!etape1(buf)) { puts("etape 1: non"); return 1; }
    puts("etape 1: ok");
    if (!etape2(buf)) { puts("etape 2: non"); return 1; }
    puts("etape 2: ok");
    if (somme(buf) != 0x267) { puts("somme: non"); return 1; }
    puts("bravo");
    return 0;
}
EOF

gcc -O2 -s -o boss boss.c
printf 'R3v3rs3!\n' > key.txt
printf 'AAAAAAAA\n' > bad.txt
```

### Phase 1 — triage

```text
$ file boss
boss: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=462d09300f4de4e2e927453ba1e7646c232f22cf, for GNU/Linux 3.2.0, stripped
$ strings -a boss | grep -E '^(cle|etape|bravo|somme)'
cle :
etape 1: ok
etape 1: non
etape 2: ok
etape 2: non
somme: non
bravo
$ ./boss < bad.txt
cle : etape 1: non
```

Fiche : PIE, dynamique, strippé, `-O2`. Trois contrôles nommés dans les messages. Aucune chaîne
candidate pour une clé : elle n'est nulle part, il faudra la **calculer**.

### Phase 2 — cartographie

```text
$ r2 -2 -q -c 'aaa; afl' boss | wc -l
11
$ r2 -2 -q -c 'aaa; afl~main' boss
0x00001090   16    360 main
```

Onze fonctions, dont `main` (360 octets). Le `-O2` a tout inliné dans `main` : `etape1`, `etape2` et
`somme` n'existent plus comme fonctions séparées.

### Phase 3 — dynamique

`puts` est appelé une fois par message : c'est un journal d'exécution gratuit.

```text
$ gdb -q -batch -ex 'break puts' -ex 'run < key.txt' \
    -ex 'x/s $rdi' -ex 'continue' -ex 'x/s $rdi' -ex 'continue' -ex 'x/s $rdi' ./boss
0x55555555600d: "etape 1: ok"
0x555555556026: "etape 2: ok"
0x55555555604a: "bravo"
```

Les trois contrôles passent avec `R3v3rs3!`. Avec `bad.txt`, le premier `puts` affiche
`etape 1: non`. La dynamique confirme l'ordre des tests, pas les contraintes.

### Phase 4 — résolution : lire les contrôles, puis `z3`

Les tests apparaissent en constantes repliées : `(s[0] ^ 0x13) != 0x41` devient
`cmp byte [rsp], 0x52` (0x41 ^ 0x13 = 0x52), et `s[3] * 3 != 0x99` devient `cmp byte [var_3h], 0x33`.

```text
$ r2 -2 -q -c 'aaa; s main; pdf' boss | sed -n '30,34p'
│     │││   0x000010ef      3da9000000     cmp eax, 0xa9
│    ┌────< 0x000010f4      7539           jne 0x112f
│    ││││   0x000010f6      807c240333     cmp byte [var_3h], 0x33     ; '3'
│   ┌─────< 0x000010fb      7532           jne 0x112f
│   │││││   0x000010fd      488d3d090f..   lea rdi, str.etape_1:_ok    ; 0x200d ; "etape 1: ok" ; const char *s
```

`cmp eax, 0xa9` : c'est `s[1] + s[2]`. Puis, plus bas, la somme des huit octets — **vectorisée** :

```text
│       ╎   0x000011ab      660ffec4       paddd xmm0, xmm4
│       ╎   0x000011b4      660ffec1       paddd xmm0, xmm1
│       ╎   0x000011b8      660ffec2       paddd xmm0, xmm2
│       ╎   0x000011bc      660f6fc8       movdqa xmm1, xmm0
│       ╎   0x000011c0      660f73d120     psrlq xmm1, 0x20
│       ╎   0x000011c5      660ffec1       paddd xmm0, xmm1
│       ╎   0x000011c9      660f7ec0       movd eax, xmm0
│       ╎   0x000011cd      3d67020000     cmp eax, 0x267
```

Le compilateur a transformé la boucle `t += s[i]` en additions SIMD. Le résultat est comparé à
`0x267` (615). On ne va pas réécrire le SIMD : on transcrit les contraintes dans `z3`.

```bash
cat > solve.py <<'EOF'
from z3 import BitVec, Solver, sat

s = [BitVec(f"s{i}", 8) for i in range(8)]
z = Solver()

z.add([0x20 <= c for c in s])                  # caractères imprimables
z.add([c <= 0x7e for c in s])
z.add(s[0] == 0x52)                            # etape 1 (constante repliée)
z.add(s[1] + s[2] == 0xa9)
z.add(s[3] == 0x33)
z.add(s[4] & 0x0f == 2)                        # etape 2
z.add(s[5] == s[4] + 1)
z.add(s[6] | 0x20 == 0x33)
z.add(s[7] == 0x21)
z.add(sum(s) == 0x267)                         # somme vectorisée

print("statut :", z.check())
m = z.model()
print("cle    :", bytes([m[c].as_long() for c in s]).decode())
EOF

/usr/bin/python3 solve.py
```

```text
statut : sat
cle    : RAh3rs3!
```

**`RAh3rs3!` n'est pas `R3v3rs3!`** — et pourtant il passe :

```text
$ echo 'RAh3rs3!' | ./boss
cle : etape 1: ok
etape 2: ok
bravo
```

Vérification des octets et de la somme, pour les deux clés :

```text
$ /usr/bin/python3 -c "
for k in ('R3v3rs3!','RAh3rs3!'):
    print(k, [hex(ord(c)) for c in k], 'somme =', hex(sum(map(ord,k))))"
R3v3rs3! ['0x52', '0x33', '0x76', '0x33', '0x72', '0x73', '0x33', '0x21'] somme = 0x267
RAh3rs3! ['0x52', '0x41', '0x68', '0x33', '0x72', '0x73', '0x33', '0x21'] somme = 0x267
```

`s[1] + s[2] == 0xa9` admet plusieurs couples (`0x33+0x76`, `0x41+0x68`, …) et la somme globale ne
les distingue pas : **plusieurs solutions valides**. C'est la leçon de la phase 4 : un solveur donne
*une* solution, pas *la* solution de l'auteur.

Et cette solution **dépend de la formulation**. Avec la contrainte supplémentaire
`sum([0x20 <= c for c in s]) == 8` au lieu de `z.add([0x20 <= c for c in s])`, le même problème
renvoie `Rj?3rs3!` — autre clé valide, autre modèle. Pour obtenir `R3v3rs3!`, il faudrait une
contrainte de plus (par exemple « les caractères forment un mot lisible »), ou le deviner.

### Phase 5 — le writeup

Ce que doit contenir la fiche :

- le hash du binaire et la version des outils (`gcc 14.2`, `radare2`, `z3`) ;
- les commandes exactes des cinq phases, avec leurs sorties (y compris `bad.txt`) ;
- la distinction entre la clé « attendue » et la clé trouvée par `z3`, avec la preuve que les deux
  passent ;
- ce qui n'a pas marché : `strings` (rien), le désassemblage de `somme` (vectorisé), la lecture
  directe des contraintes (repliées).

La structure de fichiers attendue est celle de [`writeups/README.md`](../../writeups/README.md) :
un `README.md` par machine et un dossier `assets/` pour les captures.

## 5. Fin du module

Le module a suivi un seul fil : **un binaire, des outils en ligne de commande, des sorties réelles**.
Du premier `file` au solveur `z3`, chaque étape a été exécutée sur une machine Debian 13, et chaque
sortie citée dans ces pages est une sortie réelle.

| Chapitre | Ce qu'il donne | L'outil qui fait le travail |
| --- | --- | --- |
| [4.1](01-triage-et-analyse-statique.md) | trier sans exécuter | `file`, `strings`, `xxd`, `binwalk` |
| [4.2](02-anatomie-elf-et-symboles.md) | comprendre un ELF | `readelf`, `xxd`, `nm` |
| [4.3](03-assembleur-x86-64.md) | lire du x86-64 | `objdump`, `gdb` |
| [4.4](04-desassemblage-radare2-rizin.md) | désassembler et naviguer | `radare2` |
| [4.5](05-analyse-dynamique-gdb-strace.md) | observer l'exécution | `gdb`, `strace`, `ltrace` |
| [4.6](06-decompilation-cli-patching-z3.md) | décompiler, patcher, résoudre | `r2 -w`, `angr`, `z3` |
| [4.7](07-anti-analyse-et-obfuscation.md) | vaincre les protections | `gdb`, `LD_PRELOAD`, patch, `upx` |
| 4.8 | méthodologie et autres formats | `javap`, `pefile`, `marshal`, `r2` |

### Trois habitudes à garder

1. **Toujours la même entrée en matière** : `sha256sum`, `file`, `strings`, `readelf -h`. C'est
   trente secondes qui évitent une heure de fausse piste.
2. **La dynamique tranche** : un désassemblage propose, `gdb`/`strace` confirment. Une clé trouvée
   n'existe que si le binaire l'accepte.
3. **Écrire en même temps** : les commandes, les sorties, les échecs. Un writeup se rédige pendant
   l'analyse, pas après.

### Et après ce module

- **ELF 32 bits et ARM** : même méthode, autres registres (`objdump -m i386`, `arm-linux-gnueabi`).
- **Windows** : `x64dbg` côté natif, `speakeasy` côté émulation, `pefile` côté Python.
- **Malware** : le même outillage, plus l'isolation (VM, réseau coupé) et l'analyse des comportements
  (`strace`, `inotifywait`, captures réseau).
- **CTF** : les épreuves `reverse` de ce dépôt sont un bon terrain ; les writeups publiés dans
  [`writeups/`](../../writeups/README.md) montrent la rédaction attendue.

## Références

- [System V ABI — x86-64](https://gitlab.com/x86-psABIs/x86-64-ABI) — conventions d'appel
- [ELF gABI](https://refspecs.linuxfoundation.org/elf/gabi4+/contents.html) — format des exécutables
- [radare2 book](https://book.rada.re/) — `aaa`, `afl`, `pdf`, `wx`, `axt`
- [gdb documentation](https://sourceware.org/gdb/documentation/) — `break`, `x/s`, `catch syscall`
- [strace / ltrace](https://strace.io/) — appels système et bibliothèque
- [Z3 guide](https://microsoft.github.io/z3guide/) — modéliser des contraintes
- [angr docs](https://docs.angr.io/) — exécution symbolique
- [UPX](https://upx.github.io/) — packer et `upx -d`
- [Python `dis`](https://docs.python.org/3/library/dis.html) et
  [`marshal`](https://docs.python.org/3/library/marshal.html)
- [pefile](https://github.com/erocarrera/pefile) — lecture de PE en Python
- [javap](https://docs.oracle.com/en/java/javase/21/docs/specs/man/javap.html) — bytecode JVM
- [Go `pclntab`](https://go.dev/src/debug/gosym/pclntab.go) — noms de fonctions Go
- [jadx](https://github.com/skylot/jadx) et [apktool](https://apktool.org/) — APK




