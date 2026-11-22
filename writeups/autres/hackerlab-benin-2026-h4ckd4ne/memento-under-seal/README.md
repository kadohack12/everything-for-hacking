---
title: "Memento · Under Seal"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "misc-forensics"
difficulty: "—"
points: 200
os: "—"
date: 2026-11-20
author: "Johans585"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/memento/under-seal/memento.md"
license: "CC BY-SA 4.0"
status: published
---

# memento — Writeup

**Catégorie :** misc (forensic / OSINT)
**Mission :** The Fall of Memento — dossier BV-2026-0518, « L'affaire Mertens »
**Flag** : `HLB2026{cc12c83247a308c80746d4c79ce76d16}`

## Énoncé
> On a forcé la planque d'Henri Mertens quelques heures après son départ. Trop tard pour lui, trop tôt pour ses traces : il n'a pas eu le temps de tout faire disparaître. Ce qu'il a tenté de détruire est sous scellés. Ce qui a survécu suffit peut-être à le retrouver. Reprenez le dossier.
>
> Chall 1 : Soumets le flag trouvé dans le dossier. — `172.28.42.2:9040` (Dossier d'instruction, web)

## Fichiers fournis
Application web statique (`SimpleHTTP`), copiée dans `workspace/memento/work/` : `home.html`, `data.js`, `app.js`, `assets/` (hero, 9 photos de pièces `exhibit-A…I`, `scelle-P7.enc`). Je n'ai touché que ce port.

## Étape 1 — Lire le dossier
`data.js` décrit 9 scellés (P-1 à P-9). La pièce déterminante est **P-7** : « Clé USB chiffrée », avec une copie forensique `assets/scelle-P7.enc` et la remarque « sans de quoi l'ouvrir, c'est un presse-papier ».

`scelle-P7.enc` fait 64 octets et commence par `Salted__` : c'est un fichier OpenSSL (`openssl enc`) protégé par mot de passe. Il faut donc trouver la clé dans les autres pièces.

## Étape 2 — Les pièces visibles (pas de clé)
- P-1 carte ValAir : `MERTENS/HENRI`, VA0117 VLD→KTY 09:40, VA0231 KTY→KVX 13:25, **jour 137**, PNR `QR4T9Z`, et un code-barres.
- P-3 note : « Vexholm : laisser filer / charter KA0.. (pas la ligne) ».
- P-2 (EXIF : Aedra Veil 7, 17/05/2026 07:12:44), P-4 virement 1,2 M USD vers Belize, P-5 hôtel de Vexholm (M. Laurent), P-6 change gare de Valdoria, P-8 carte, P-9 « Résidence du Phare, Kaltyr-Durn, unité 7 » : contexte, pas de clé.
- Aucune donnée après la fin des JPEG/PNG, aucun `HLB2026{` en clair dans les fichiers ou les scripts.

## Étape 3 — Le code-barres PDF417 de la carte d'embarquement (P-1)
Le code-barres de `exhibit-A.png` est un PDF417 (format BCBP IATA). `zbar` ne le lit pas ; `zxing-cpp` le décode (recadrage sur la zone du code-barres) :

```
M3MERTENS/HENRI       EQR4T9Z VLDKTYVA 0117 137J003A0042 01A>6 UPG WL PAX REF VARGA
  QR4T9Z KTYKVXVA 0231 137J011C0043 01A>6 BAG 1PC/23 SEQ ACCEPTED
  QR4T9Z KVXKDRKA 0088 137Y014C0044 043>6 RBK KVX>KDR KA088/137 OPR KALAIR // KEY b6f383eb6a9a4dbcea04308f
```

Deux informations que l'image ne montre pas :
- un **troisième segment** : Mertens a été reprogrammé sur **KA088 KVX→KDR** (Vexholm → Kaltyr-Durn) le jour 137. Cela correspond au « charter KA0.. » de la note P-3 et à la « Résidence du Phare, Kaltyr-Durn » de P-9 ;
- une **clé** : `b6f383eb6a9a4dbcea04308f`.

Le champ `REF VARGA` est à noter : c'est le nom d'alias de Lindberg dans la mission BATMAN (probable lien entre dossiers).

## Étape 4 — Ouvrir le scellé P-7
La clé est un mot de passe OpenSSL. Combinaison qui donne un padding valide :

```bash
openssl enc -d -aes-256-cbc -md sha256 -pbkdf2 \
  -pass pass:b6f383eb6a9a4dbcea04308f -in scelle-P7.enc
# HLB2026{cc12c83247a308c80746d4c79ce76d16}
```

Script de test des combinaisons (chiffre × digest × pbkdf2) : `work/trykey.sh`.

## Pistes écartées / erreurs
- Fichiers images : pas de stéganographie évidente ni de données après EOF.
- Mes premiers essais OpenSSL étaient invalides : la variable du mot de passe était interprétée par Git Bash avant d'atteindre WSL (mot de passe vide). Corrigé en passant par un script fichier.

## Challenge 2 — Destination réelle et heure locale d'arrivée

> Pour l'attendre à l'arrivée, il te faut deux choses : où il pose le pied, et quand. Donne la destination réelle et l'heure locale. Format : `HLB2026{Ville-HH:MM}`

**Flag proposé : `HLB2026{Durn-17:25}`** (non vérifiable localement : l'application est statique, sans API de validation ; non soumis).

Raisonnement :
1. La carte d'embarquement affiche VLD→KTY→KVX (Vexholm) : c'est la destination **apparente**, confirmée par la carte annotée (P-8) et l'hôtel de Vexholm (P-5, leurre).
2. Le BCBP décodé à l'étape 3 contient un troisième segment `RBK KVX>KDR KA088/137 OPR KALAIR` (RBK = rebooked) : la destination **réelle** est **KDR, Kaltyr-Durn**, en accord avec la note P-3 (« charter KA0.. pas la ligne ») et la carte de visite P-9 (Résidence du Phare, Kaltyr-Durn).
3. Le « jour 137 » est le 17/05/2026 (jour julien) : même date que le reçu de change (06:40) et le cliché du téléphone.
4. Grille KalAir (heures locales, `data.js` et tableau de la photo) : KA088 KVX→KDR **jour 137 : départ 15:40, arrivée 17:25**. Les autres jours sont des leurres (jour 136 : 17:05, jour 138 : 16:10 → 17:55). KA120 KVX→KTY est la « ligne », écartée par la note.

Réserve sur le format : « Ville » est pris comme **Durn** (le nom de la localité, `KDR = Kaltyr-Durn` étant l'aéroport) ; `Kaltyr-Durn` contiendrait un second tiret et collerait mal au format `Ville-HH:MM`.

## Challenge 3 — Le refuge

> Il lui faut un toit, loin des regards indiscrets. Où comptait-il trouver refuge une fois arrivé ? Format : `HLB2026{Reponse}`

**Flag proposé : `HLB2026{Residence du Phare}`** (formulation exacte non vérifiable localement ; non soumis).

Raisonnement : la destination réelle est Kaltyr-Durn (challenge 2). La seule pièce qui décrit un hébergement à cet endroit est **P-9**, la carte de visite « Résidence du Phare, locations meublées, courte durée, Kaltyr-Durn, unité 7 », que le dossier décrit comme « un pied-à-terre que personne n'était censé connaître ». L'hôtel de Vexholm (P-5, réservé au nom de M. Laurent pour la nuit du 16 au 17) est le leurre : il n'a jamais été sa destination.

Observations :
- le numéro de la carte de visite (03 71 42 90) est **le même** que celui de l'en-tête de ValExchange, la banque du virement P-4 : un lien possible entre le logement et le montage financier, sans effet sur la réponse ;
- le fichier d'origine du cliché du téléphone (P-2) ne contient pas de GPS ni de commentaire (EXIF : Aedra Veil 7, 17/05/2026 07:12:44) ;
- le listing de `/assets/` est désactivé (404) : aucune autre pièce accessible sans deviner des noms de fichiers.

## Éléments conservés pour la suite de la mission
- Itinéraire : Valdoria (VLD) → Kaltyr (KTY) → Vexholm (KVX) → **Kaltyr-Durn (KDR)** par le charter **KA088 / jour 137** (17/05/2026), puis Résidence du Phare, unité 7.
- Grille KalAir dans `data.js` : KA088 KVX→KDR jour 137 départ 15:40, arrivée 17:25 ; KA120 KVX→KTY jour 137 18:00 (la « ligne », écartée par la note).
- Alias `VARGA` lu dans le BCBP (`REF VARGA`).
