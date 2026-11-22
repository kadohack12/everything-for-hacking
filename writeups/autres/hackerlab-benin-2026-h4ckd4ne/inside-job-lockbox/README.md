---
title: "Inside Job · LockBox"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc"
difficulty: "—"
points: 150
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/inside-job/lockbox/writeup-lockbox.md"
license: "CC BY-SA 4.0"
status: published
---

# LockBox — Coffre VS-400E (write-up du run)

## Objectif

- **Catégorie** : Misc / 150 pts (série Inside Job, partie 05)
- **Cible** : `172.28.17.2:80` — `vault.vdcbank.vld` (Coffre VS-400E)
- **Énoncé** : le fourgon intercepté contient un coffre électronique VS-400E. Deux
  sources ont vu des couples défi → code différents :
  - défi `314159` → code `732222`
  - défi `271828` → code `699991`
  - « Deux codes valides ? Le code change-t-il régulièrement ? »

## Analyse

Le coffre affiche un **défi à 6 chiffres** et attend un **code à 6 chiffres** : c'est
un OTP défi-réponse déterministe. En comparant les deux couples connus chiffre à
chiffre :

```
défi 3 1 4 1 5 9   -> code 7 3 2 2 2 2
offset (7-3, 3-1, 2-4, 2-1, 2-5, 2-9) mod 10 = 4 2 8 1 7 3

défi 2 7 1 8 2 8   -> code 6 9 9 9 9 1
offset (6-2, 9-7, 9-1, 9-8, 9-2, 1-8) mod 10 = 4 2 8 1 7 3
```

Les deux couples donnent **exactement le même offset** `[4,2,8,1,7,3]` : le code est
le défi additionné chiffre à chiffre modulo 10 (le « code qui change régulièrement »
suit simplement le défi courant).

## Exploitation

```bash
curl -s http://172.28.17.2/api/info
# {"attempts_left":8,"challenge":"323871","digits":6,"locked_out":false,"opened":false}

python3 - <<'EOF'
ch = "323871"; key = [4,2,8,1,7,3]
print("".join(str((int(ch[i]) + key[i]) % 10) for i in range(6)))
EOF
# 741944

curl -s -X POST http://172.28.17.2/api/unlock \
  -H "Content-Type: application/json" -d '{"code":"741944"}'
# {"flag":"...","status":"open"}
```

Calcul pour le défi `323871` : `(3+4, 2+2, 3+8, 8+1, 7+7, 1+3) mod 10`
= `7 4 1 9 4 4` → **741944**. Le coffre s'ouvre (`status: open`) et renvoie le flag,
soumis à la plateforme (valeur non reproduite ici).

## Pistes écartées

- Code fixe : les deux couples diffèrent, ce n'est pas un code statique.
- Force brute : `attempts_left` limité à 8 et lockout temporisé.
- Les défis ressemblent à π (314159) et e (271828) : coïncidence de couverture,
  la vraie relation est l'offset chiffre-à-chiffre identique sur les deux couples.

## Validation reproductible

1. `GET /api/info` → `challenge` courant.
2. Calculer `code[i] = (challenge[i] + offset[i]) % 10` avec `offset = [4,2,8,1,7,3]`
   (offset prouvé par les deux couples connus).
3. `POST /api/unlock {"code": "<code>"}` → `status: open` + flag.
