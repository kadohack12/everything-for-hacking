# 05 — Cyclic et offsets

[← Module](README.md)

## Objectif

Trouver l'offset exact entre le début du tampon et l'adresse de retour, sans essais successifs, et
le prouver dans `gdb`.

## Le principe du motif

Un motif `cyclic` est une suite dont chaque sous-suite de 4 ou 8 octets est unique. On envoie le
motif, le programme plante, on lit l'adresse de retour écrasée, et on demande à pwntools à quel
décalage ce motif apparaît.

```bash
pwn cyclic 200
```

```text
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaa...
```

## Lab

```c
/* ret2win.c — compilation :
   gcc -fno-stack-protector -no-pie -o ret2win ret2win.c */
#include <stdio.h>
#include <unistd.h>

void win(void) {
    puts("Bravo, tu as detourne l'execution !");
    execl("/bin/sh", "sh", NULL);
}

void vuln(void) {
    char buf[64];
    read(0, buf, 200);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("Entree :");
    vuln();
    puts("Retour propre, rien ne s'est passe.");
    return 0;
}
```

Le tampon fait 64 octets, mais `read` en accepte 200. L'offset cherché n'est pas 64 : entre le
tampon et l'adresse de retour s'ajoute le `rbp` sauvegardé.

## Étape 1 : envoyer le motif et planter

```bash
python3 -c "
from pwn import *
context.arch = 'amd64'
open('/tmp/cyc.bin','wb').write(cyclic(200))
"
gdb -q -batch -ex 'run < /tmp/cyc.bin' \
    -ex 'info registers rsp rbp rip' -ex 'x/3gx $rsp' ./ret2win
```

```text
Program received signal SIGSEGV, Segmentation fault.
rsp            0x7fffffffd668      0x7fffffffd668
rbp            0x6161617261616171  0x6161617261616171
rip            0x4011af            0x4011af <vuln+32>
0x7fffffffd668: 0x6161617461616173      0x6161617661616175
0x7fffffffd678: 0x6161617861616177
```

Lecture : `rbp` contient déjà du motif (`qaaaaara`), et la valeur en haut de pile au moment du
`ret` est `0x6161617461616173` — c'est l'adresse de retour écrasée. `rip` pointe encore sur le
`ret` : le processeur n'a pas encore sauté.

## Étape 2 : convertir la valeur en offset

```python
from pwn import *

context.arch = "amd64"
print("offset =", cyclic_find(0x6161617461616173))
```

```text
offset = 72
```

72 = 64 octets de tampon + 8 octets de `rbp` sauvegardé. Le calcul se vérifie à la main : le
`ret` lit les 8 octets qui suivent le `rbp` sauvegardé, donc `64 + 8`.

## Étape 3 : vérifier la structure dans gdb

```bash
gdb -q -batch -ex 'b vuln' -ex 'run < /dev/null' \
    -ex 'info registers rsp rbp' -ex 'x/6gx $rsp' ./ret2win
```

```text
Breakpoint 1, 0x0000000000401193 in vuln ()
rsp            0x7fffffffd660      0x7fffffffd660
rbp            0x7fffffffd660      0x7fffffffd660
0x7fffffffd660: 0x00007fffffffd670      0x00000000004011e6
0x7fffffffd670: 0x0000000000000001      0x00007ffff7df4ca8
0x7fffffffd680: 0x00007fffffffd770      0x00000000004011b0
```

À l'entrée de `vuln`, `rbp` pointe sur le `rbp` de `main` sauvegardé (`0x7fffffffd670`) et
l'adresse de retour vers `main` est juste au-dessus (`0x4011e6`). Le tampon, lui, est à
`rbp - 0x40`, soit 64 octets plus bas : la cohérence est confirmée.

## Les cas où l'offset n'est pas la taille du tampon

| Situation | Offset |
| --- | --- |
| `char buf[64]` + `read` | 64 + 8 = 72 |
| `char buf[64]` + `gets` | 64 + 8 = 72 |
| variable locale déclarée avant le tampon | la taille de cette variable s'ajoute |
| compilation avec `-O2` | le tampon peut être placé ailleurs : mesurer, ne pas supposer |
| `-fstack-protector` | un canary s'intercale : offset plus grand et valeur à préserver |

D'où la règle : **on mesure toujours**. La taille déclarée dans le source donne une intuition, pas
une réponse.

## Automatiser la mesure

Sans `gdb`, on peut aussi chercher l'offset par bissection : envoyer des payloads de longueurs
croissantes et repérer celle où le programme cesse de revenir proprement. C'est plus lent, plus
bruité, et cela ne dit pas *où* on a écrasé. La méthode `cyclic` + `gdb` reste la plus fiable.

## Pièges

| Symptôme | Cause |
| --- | --- |
| `cyclic_find` renvoie `-1` | la valeur lue n'appartient pas au motif (alignement, ou canary) |
| Offset 72 mais le payload ne marche pas | l'offset est bon, c'est la cible du saut qui est fausse |
| Plantage avant le `ret` | le canary a été écrasé : offset mal mesuré ou protection active |
| Offset différent entre deux compilations | optimisation : mesurer sur le binaire final |

## À retenir

- `cyclic` donne un motif unique ; `cyclic_find` traduit la valeur écrasée en offset.
- L'offset vaut taille du tampon + variables intercalées + 8 (rbp sauvegardé).
- On le prouve dans `gdb` en regardant `rsp`, `rbp` et les mots en haut de pile.
- Un offset juste ne suffit pas : c'est la cible du saut qui décide du succès.
