# 4.1 — Triage et analyse statique de base

> Fiche du chapitre 4.1 du module [04 — Reverse Engineering en ligne de commande](README.md).
> Plan complet : [README.md#plan](README.md#plan).

## Objectifs d'apprentissage

À la fin de cette fiche, je dois savoir :

- appliquer un **ordre de triage reproductible** sur un fichier inconnu, sans jamais l'exécuter ;
- répondre en moins de deux minutes à : *quel type de fichier, quelle architecture, packé ou non,
  quelles chaînes lisibles, quelles dépendances ?* ;
- utiliser `file`, `sha256sum`, `strings`, `xxd`, `binwalk` et `upx` avec les options qui comptent,
  et savoir ce que chacune ne peut **pas** voir ;
- reconnaître un binaire UPX, y compris quand son en-tête a été maquillé ;
- documenter le triage dans un writeup de façon vérifiable (commandes + sorties).

## 1. La règle d'or : on ne lance pas un binaire inconnu

Un binaire inconnu est du **code arbitraire** que je m'apprête à exécuter avec mes droits. Ce n'est
pas une hypothèse théorique : c'est le métier de base d'un analyste malware, et un challenge CTF
peut très bien contenir un binaire qui, en plus de demander un mot de passe, écrit dans
`~/.bashrc` ou ouvre une connexion sortante.

| Risque | Ce qui se passe concrètement | Parade |
| --- | --- | --- |
| Destruction | `rm -rf ~`, chiffrement de fichiers | VM avec instantané, dossier jetable |
| Réseau | callback vers un serveur, exfiltration | réseau coupé ou simulé (VM host-only) |
| Persistance | `cron`, `systemd --user`, `~/.bashrc` | VM jetable, jetée après analyse |
| Élévation | exploitation d'un service local | jamais en `root` |
| Évasion | détection de VM/sandbox, comportement conditionnel | le savoir : un binaire sage en VM peut être méchant ailleurs |

Trois habitudes qui coûtent trente secondes :

1. **Travailler dans une VM ou un conteneur** dont on peut jeter l'état. `docker run --rm -it
   --network none -v ~/rev-lab:/lab debian:stable` suffit pour un crackme.
2. **Retirer le bit exécutable** sur les échantillons inconnus : `chmod -x echantillon`. Ce n'est
   pas une sécurité (on peut le remettre), c'est un garde-fou contre le `./` réflexe.
3. **Monter le dossier de lab en `noexec`** quand c'est possible :
   `sudo mount -o remount,noexec /home`. Les outils de triage lisent le fichier, ils n'ont pas
   besoin de l'exécuter.

> **Ordre de triage.** Empreinte → type réel → chaînes → octets → fichiers embarqués → packer.
> On ne descend d'un niveau qu'après avoir noté ce que le précédent a donné. Et on n'exécute
> qu'au chapitre 4.5, dans un environnement maîtrisé.

## 2. `file` — quel est ce fichier, vraiment ?

`file` lit les **magic bytes** et l'en-tête du fichier. Il ne l'exécute pas et ne se fie pas à
l'extension : c'est exactement ce qu'on veut en premier.

```bash
file exo
```

```text
exo: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=064f17e95f4dd1f4f82ade0a0cbb2cc5710982b4, for GNU/Linux 3.2.0, not stripped
```

Chaque mot de cette ligne est une information exploitable :

| Terme | Ce que ça m'apprend | Conséquence pour la suite |
| --- | --- | --- |
| `ELF` | format Linux (Executable and Linkable Format) | `readelf`, `objdump`, `nm` s'appliquent (4.2) |
| `64-bit` | architecture x86-64 | registres `rax`…`r15`, pointeurs de 8 octets (4.3) |
| `LSB` | little-endian | les entiers se lisent à l'envers dans un dump |
| `pie executable` | position-independent, chargé à une adresse aléatoire | les adresses absolues ne sont pas stables : préférer les offsets (4.4) |
| `dynamically linked` | dépend de `libc.so.6` | `strace`/`ltrace` verront les appels (4.5) |
| `interpreter /lib64/ld-linux…` | le loader qui démarre le programme | **c'est lui que `ldd` exécute** (4.2, section sécurité) |
| `not stripped` | la table de symboles est présente | `nm` donnera les noms de fonctions (4.2) |

Options utiles :

```bash
file -b exo        # sans le nom de fichier : pratique dans un pipeline
file -i exo        # type MIME
file -k exo        # ne s'arrête pas au premier motif : détecte les polyglottes
```

```text
$ file -i exo
exo: application/x-pie-executable; charset=binary
```

**Le piège de l'extension.** `file` ignore le nom : un fichier nommé `facture.pdf` qui commence
par `7f 45 4c 46` est un ELF. C'est la première chose à vérifier sur une pièce jointe suspecte.

## 3. `sha256sum` — l'identité de l'échantillon

```bash
sha256sum exo
```

```text
0a1e27582d2247de1c590ccf7e03488d47c749d59274c2ec280d330edd2d32a8  exo
```

À quoi ça sert :

- **reproductibilité** : un writeup qui donne le hash permet de vérifier qu'on analyse le même
  fichier, même si le challenge a été mis à jour ;
- **déduplication** : deux noms différents, un seul hash = un seul échantillon ;
- **réputation** : un hash se cherche sur VirusTotal sans uploader le fichier.

> **Attention à l'upload.** Envoyer un échantillon sur VirusTotal le rend **public** : d'autres
> personnes, et l'attaquant, peuvent le récupérer. Pour un binaire d'entreprise ou un challenge
> non terminé, on cherche **le hash**, on n'envoie pas le fichier.

`md5sum` existe encore (VirusTotal affiche le MD5), mais SHA-256 est la référence : MD5 et SHA-1
ont des collisions construites.

## 4. `strings` — la mémoire du binaire

`strings` extrait les séquences de caractères imprimables d'au moins **4 caractères** (par défaut),
suivies d'un octet non imprimable. C'est l'outil le plus rentable du triage : messages d'erreur,
chemins, URLs, noms de fonctions, et parfois le mot de passe en clair.

```bash
strings exo | head -12
```

```text
/lib64/ld-linux-x86-64.so.2
puts
__libc_start_main
__cxa_finalize
printf
libc.so.6
GLIBC_2.2.5
GLIBC_2.34
cours-rev 1.0 - binaire de demonstration
version %s
1.0.3
```

Les huit premières lignes sont du **bruit de linkage** (symboles de la libc) : elles apparaissent
dans *tous* les binaires dynamiques et n'apprennent rien sur le programme. Les trois dernières sont
intéressantes : un nom de version et un message applicatif.

### Options qui changent tout

| Option | Effet | Quand l'utiliser |
| --- | --- | --- |
| `-n 3` | longueur minimale de 3 | chercher des marqueurs courts (`key`, `ok`, `zz9`) |
| `-a` | scanner tout le fichier, pas seulement les sections chargeables | données hors sections classiques |
| `-t x` | préfixer par l'offset en hexadécimal | localiser la chaîne dans le fichier pour un patch |
| `-t d` | offset en décimal | recoupement avec `objdump -s` |
| `-e l` | chaînes 16 bits little-endian (UTF-16LE) | chaînes Windows, `char16_t` en C |
| `-e L` | chaînes 32 bits little-endian (UTF-32LE) | **`L"..."` en C sur Linux** |
| `-e b` / `-e B` | variantes big-endian | binaires réseau, PowerPC |

### Le détail Linux qui fait perdre une heure

En C, sur Linux, `L"secret"` est un `wchar_t` de **4 octets** : chaque lettre est suivie de trois
octets nuls. Ce n'est donc **pas** de l'UTF-16, et `strings -e l` ne le trouve pas.

```bash
strings -e l exo | grep REV     # UTF-16LE
strings -e L exo | grep REV     # UTF-32LE
```

```text
$ strings -e l exo | grep REV
REV{utf16_h1dd3n}

$ strings -e L -t x exo | grep REV
   2038 REV{utf32_h1dd3n}
```

Autrement dit : `u"..."` (`char16_t`) → `-e l`, `L"..."` (`wchar_t`) → `-e L`. Sur Windows,
`L"..."` est bien de l'UTF-16 : la même commande ne donne pas le même résultat selon la plateforme
de compilation. C'est une source classique de « le writeup dit que ça marche, chez moi non ».

### Filtrer le bruit

Sur un vrai binaire, `strings` sort des centaines de lignes. Quelques filtres :

```bash
strings -n 8 exo | grep -vE '^(GLIBC|\.|_|/)' | sort -u    # enlever le linkage
strings exo | grep -iE 'pass|flag|key|secret|token'        # chercher l'intéressant
strings -t x exo | grep -i 'version'                       # avec l'offset
```

## 5. `xxd` et `hexdump -C` — lire les octets

`strings` interprète ; `xxd` montre la vérité brute. C'est indispensable dès qu'une chaîne est
découpée, tronquée ou dans un encodage inattendu.

```bash
xxd -s 0x2030 -l 0x40 exo
```

```text
00002030: 0000 0000 0000 0000 5200 0000 4500 0000  ........R...E...
00002040: 5600 0000 7b00 0000 7500 0000 7400 0000  V...{...u...t...
00002050: 6600 0000 3300 0000 3200 0000 5f00 0000  f...3...2..._...
00002060: 6800 0000 3100 0000 6400 0000 6400 0000  h...1...d...d...
```

Lecture : l'offset à gauche (`0x2038` pour le `R`), 16 octets par ligne, puis la colonne ASCII.
Le motif `52 00 00 00 45 00 00 00` est bien `R`, `E` séparés par trois octets nuls : de l'UTF-32LE,
ce qui confirme l'analyse de `strings -e L`.

Options et équivalents :

```bash
xxd exo | head -3                  # début du fichier (magic ELF : 7f 45 4c 46)
xxd -p exo | head -c 64            # dump sans colonne ASCII (pour les pipes)
xxd -r dump.hex > binaire          # reconstruire un binaire depuis un dump (4.6)
hexdump -C exo | head -3           # même chose, autre outil (util-linux)
hexdump -C -n 64 exo               # seulement 64 octets
```

> `xxd` et `hexdump -C` produisent le même contenu avec une mise en forme légèrement différente.
> Choisir un des deux et s'y tenir évite les erreurs de recopie dans les writeups.

## 6. `binwalk` — ce qui est planqué dans le fichier

`binwalk` cherche des **signatures de fichiers** (archives, images, firmwares, exécutables) à
l'intérieur d'un autre fichier.

```bash
binwalk exo
```

```text
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             ELF, 64-bit LSB shared object, AMD x86-64, version 1 (SYSV)
```

Sur un binaire simple, il n'apprend rien de plus que `file`. Il devient indispensable quand :

- le fichier est un **firmware** ou une image disque (plusieurs systèmes de fichiers empilés) ;
- une **archive** est concaténée à un exécutable (self-extracting) ;
- un packer laisse une signature connue.

```bash
binwalk -e fichier          # extraire (crée un dossier _fichier.extracted/)
binwalk -E fichier          # entropie : repère les zones compressées ou chiffrées
```

> **Attention à `-e`** : l'extraction écrit des fichiers, et certains formats extraits peuvent
> eux-mêmes être exécutables. On extrait dans le dossier de lab, jamais dans son `$HOME`.
> Selon la version, les options diffèrent (binwalk 3, réécrit en Rust, a changé plusieurs
> drapeaux) : `binwalk --help` avant d'automatiser.

## 7. `upx` — détecter et défaire un packer

UPX compresse un exécutable et le préfixe d'un décompresseur. Résultat : le binaire est plus petit,
les chaînes disparaissent, les sections aussi. C'est la première chose à tester quand `strings`
ne donne rien d'utile.

```bash
cp exo exo.packed
upx -q exo.packed
file exo.packed
```

```text
exo.packed: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), statically linked, no section header
```

Trois signaux dans cette seule ligne :

- `statically linked` alors que l'original était dynamique : le décompresseur UPX est lié en dur ;
- **`no section header`** : UPX supprime la table des sections — signature typique ;
- la taille chute (ici 16 120 → 6 036 octets, soit ~37 %).

```bash
upx -t exo.packed        # tester l'intégrité
upx -d exo.packed        # décompresser (écrase le fichier)
```

```text
$ upx -t exo.packed

Tested 1 file.
```

### Quand l'en-tête UPX a été maquillé

Certains challenges modifient la signature `UPX!` pour casser les outils automatiques. `upx` refuse
alors le fichier, mais les autres indices restent :

```text
$ upx -t casse
upx: casse: NotPackedException: not packed by UPX

Tested 0 files.
```

```bash
binwalk casse
```

```text
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             ELF, 64-bit LSB shared object, AMD x86-64, version 1 (SYSV)
2237          0x8BD           Copyright string: "Copyright (C) 1996-2024 the UPX Team. All Rights Reserved. $"
```

La chaîne de copyright UPX trahit le packer même quand le magic est faux. Pour aller plus loin :
chercher la version d'UPX dans les octets, puis réparer le magic (`UPX?` → `UPX!`) avec `xxd -r`
ou un éditeur hexadécimal, et relancer `upx -d`. Détail traité au chapitre 4.7.

## 8. Tableau de synthèse : indice observé → action suivante

C'est le tableau à garder sous les yeux. Il transforme une sortie d'outil en décision.

| Indice observé | Interprétation | Action suivante |
| --- | --- | --- |
| `ELF 64-bit … not stripped` | symboles disponibles | `nm`, `objdump -d` → chapitre 4.2 |
| `… stripped` | pas de table de symboles | analyse dynamique, `r2` → chapitres 4.4 et 4.5 |
| `no section header` + taille réduite | packer (souvent UPX) | `upx -t`, `upx -d` → section 7 |
| Entropie élevée sur tout le fichier | compressé ou chiffré | `binwalk -E`, chercher le packer → 4.7 |
| `statically linked` | pas d'appels libc visibles par `ltrace` | privilégier `strace` et `gdb` → 4.5 |
| `strings` : URL, IP, `/etc/passwd` | activité réseau ou fichiers | `strace -e trace=network,openat` → 4.5 |
| `strings` : `pass`, `flag`, `REV{` | donnée en clair | vérifier, c'est peut-être fini |
| `strings` : rien d'utile, binaire petit | chaînes construites ou chiffrées | désassembler → 4.3, 4.4 |
| `file` : `PE32+ executable (console) x86-64` | binaire Windows | outils PE → 4.8 |
| `file` : `Python script, ASCII text` | pas un binaire | lire le source |
| `file` : `Python bytecode` | `.pyc` | décompiler → 4.8 |
| `file` : `Mach-O` | binaire macOS | outils Mach-O → 4.8 |
| `file` : `data` | format inconnu ou chiffré | `xxd`, `binwalk`, entropie |

## 9. Pièges classiques

### 9.1 Les faux positifs de `strings`

Une chaîne trouvée n'est pas une chaîne **du programme**. `GLIBC_2.2.5`, `libc.so.6`, des chemins
de la bibliothèque standard apparaissent dans presque tous les binaires dynamiques. Filtrer le
linkage avant de conclure :

```bash
strings -n 8 exo | grep -vE '^(GLIBC|\.|_|/lib|/usr)' | sort -u
```

### 9.2 `strings` sur un binaire packé : des fragments, pas des chaînes

Sur un binaire UPX, les données compressées contiennent parfois des bribes lisibles. Elles
ressemblent à des chaînes, mais sont tronquées :

```text
$ strings exo.packed | grep -i cours-rev
cours-rev 1.0 - binai
```

La vraie chaîne est `cours-rev 1.0 - binaire de demonstration`. Ce fragment est un **artefact de
compression** : conclure à partir de lui, c'est écrire un writeup faux. Règle : sur un binaire
packé, `strings` ne prouve rien tant que le binaire n'est pas décompressé.

### 9.3 Chaînes construites à l'exécution

Un programme peut assembler son mot de passe octet par octet, ou par `movabs` d'un immédiat de
64 bits. `strings` en montre alors un fragment incohérent :

```text
$ strings pile | grep REV
REV{pileH
```

Le `H` final n'existe pas : il vient de l'instruction suivante. Le vrai contenu est reconstruit par
le code (`movabs $0x656c69707b564552` charge `REV{pile` dans un registre). Seul le désassemblage
(chapitre 4.3) ou l'exécution sous `gdb` (4.5) donnera la valeur exacte.

### 9.4 Les chaînes trop courtes

Le minimum par défaut est de 4 caractères. Un marqueur de 3 caractères est invisible :

```text
$ strings court | grep -c zz9
0
$ strings -n 3 court | grep zz9
zz9
```

### 9.5 L'encodage

Trois pièges qui se cumulent :

- **UTF-16 vs UTF-32** : `L"..."` sur Linux = 4 octets par caractère (voir section 4) ;
- **big-endian** : un binaire réseau ou PowerPC stocke `R` en `00 52` ;
- **encodages mixtes** : un programme peut utiliser les deux selon la plateforme cible.

Toujours essayer `-e l` **et** `-e L` avant de conclure qu'une chaîne n'existe pas.

### 9.6 « Not stripped » ne veut pas dire « tout est nommé »

Un binaire peut garder ses symboles **dynamiques** (ceux de la libc) et avoir perdu ses symboles
internes. `nm` sans option ne montre alors que des `U` et des `w`. Vérifier avec
`nm -D` (dynamique) et `nm` (complet) : le chapitre 4.2 détaille la différence.

### 9.7 Se fier à l'extension ou au nom

`file` lit le contenu, pas le nom. Un `README.txt` peut être un exécutable, une `image.png` peut
contenir une archive ZIP concaténée. C'est le principe même d'un polyglotte, et `file -k` aide à
les repérer.

## 10. Exercice pratique

### Le programme

Créer `exo.c` dans `~/rev-lab` :

```c
#include <stdio.h>
#include <uchar.h>
#include <wchar.h>

static const char *banner = "cours-rev 1.0 - binaire de demonstration";
static const wchar_t *secret32 = L"REV{utf32_h1dd3n}";
static const char16_t *secret16 = u"REV{utf16_h1dd3n}";

int main(void) {
    puts(banner);
    printf("version %s\n", "1.0.3");
    return 0;
}
```

Compiler **sans optimisation** (les chaînes restent alors en clair dans `.rodata`), puis fabriquer
la version packée :

```bash
gcc -O0 -o exo exo.c
cp exo exo.packed
upx -q exo.packed
```

### Questions

1. Que dit `file exo` ? Quels mots indiquent qu'il s'agit d'un binaire 64 bits non strippé ?
2. Combien de chaînes contenant `REV` `strings exo` trouve-t-il par défaut ? Pourquoi ?
3. Donne les deux commandes qui extraient les deux secrets.
4. Quel est l'offset du secret UTF-32 ? Pourquoi y a-t-il trois octets nuls entre chaque lettre ?
5. Sur `exo.packed` : que dit `file` ? Que devient la bannière dans `strings` ? Comment revenir à
   l'original ?

<details>
<summary>Correction</summary>

**1. `file exo`**

```text
exo: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, BuildID[sha1]=…, for GNU/Linux 3.2.0, not stripped
```

`64-bit` et `x86-64` donnent l'architecture ; `not stripped` indique que la table de symboles est
présente (`nm` fonctionnera) ; `dynamically linked` annonce des appels libc visibles par `ltrace`.

**2. Aucune.**

```text
$ strings exo | grep -c REV
0
```

`strings` par défaut ne lit que des séquences d'octets ASCII imprimables. Les deux secrets sont
stockés en caractères larges : chaque lettre est suivie d'octets nuls, donc la séquence
« imprimable, imprimable, imprimable » n'existe pas. Il faut demander l'encodage.

**3. Extraction**

```text
$ strings -e l exo | grep REV
REV{utf16_h1dd3n}

$ strings -e L exo | grep REV
REV{utf32_h1dd3n}
```

`u"..."` (`char16_t`) → 2 octets par caractère → `-e l`.
`L"..."` (`wchar_t`) → 4 octets par caractère sur Linux → `-e L`.

**4. Offset et structure**

```text
$ strings -e L -t x exo | grep REV
   2038 REV{utf32_h1dd3n}
```

```text
$ xxd -s 0x2038 -l 0x10 exo
00002038: 5200 0000 4500 0000 5600 0000 7b00 0000  R...E...V...{...
```

`R` = `0x52`, puis trois octets nuls : `wchar_t` fait 4 octets, et la valeur d'un caractère ASCII
tient dans le premier octet (little-endian). Vérification directe de la taille :

```bash
python3 -c 'import ctypes; print(ctypes.sizeof(ctypes.c_wchar))'   # 4 sur Linux
```

**5. Version packée**

```text
$ file exo.packed
exo.packed: ELF 64-bit LSB pie executable, x86-64, version 1 (SYSV), statically linked, no section header
```

`no section header` et `statically linked` sont les deux signatures d'UPX. La bannière devient un
fragment :

```text
$ strings exo.packed | grep -i cours-rev
cours-rev 1.0 - binai
```

Pour revenir à l'original : `upx -d exo.packed` (le fichier est écrasé) puis re-vérifier avec
`file` et `strings`. Si `upx -d` répond `NotPackedException`, l'en-tête a été maquillé : voir
section 7 et chapitre 4.7.

</details>

## 11. Ce que je retiens

- **Triage avant exécution**, toujours. Un binaire inconnu est du code arbitraire ; la VM jetable
  et le `chmod -x` coûtent moins cher qu'un `rm -rf`.
- `file` répond à « qu'est-ce que c'est », `sha256sum` à « est-ce bien le même », `strings` à
  « qu'est-ce que ça raconte », `xxd` à « qu'est-ce qu'il y a vraiment », `binwalk` à « qu'est-ce
  qui est caché dedans », `upx` à « est-ce que c'est compressé ».
- **`no section header` = packer** dans la grande majorité des cas rencontrés en CTF.
- Les chaînes larges se cherchent avec `-e l` **et** `-e L` : Linux et Windows ne stockent pas
  `L"..."` de la même façon.
- `strings` sur un binaire packé produit des fragments trompeurs : ne jamais conclure sans
  décompresser.
- Ce chapitre ne fait que **lire**. Le suivant lit la structure interne (ELF), puis on apprendra à
  désassembler et à exécuter sous contrôle.

## Références

- `man file`, `man strings`, `man xxd`, `man binwalk`, `man upx`
- [ELF — format de fichier](https://refspecs.linuxfoundation.org/elf/elf.pdf) (spécification)
- [UPX — documentation](https://upx.github.io/)
- [Liste des signatures de fichiers](https://en.wikipedia.org/wiki/List_of_file_signatures)
