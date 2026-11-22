# Autres plateformes et CTFs

Retour à l'[index des writeups](../README.md) · [Comment contribuer](../../CONTRIBUTING.md)

Writeups de challenges qui ne dépendent pas des trois plateformes principales
([Hack The Box](../hackthebox/), [TryHackMe](../tryhackme/), [Hackropole](../hackropole.fr/)) :
plateformes d'apprentissage, CTFs archivés, environnements vulnérables à installer soi-même.

Chaque writeup vit dans `autres/<plateforme-ou-ctf>/<nom-du-challenge>/`, avec son `README.md`
et ses captures dans `assets/`.

## ⚠️ Ce qui est accepté, ce qui est refusé

| Bienvenu | Refusé |
| --- | --- |
| PicoCTF | **Tout CTF encore en cours** |
| PortSwigger Web Security Academy | Toute plateforme qui **interdit la publication** de solutions |
| OverTheWire (Bandit, Natas, Leviathan…) | Root-Me (ses règles interdisent la publication de solutions) |
| VulnHub | Flags d'épreuves encore ouvertes |
| CTFs archivés : 404CTF, épreuves terminées de CTFtime… | Cibles réelles, contenu illégal |

Deux règles, et elles suffisent :

1. **L'épreuve doit être terminée.** Un CTF en cours, c'est du spoil pour les joueurs qui planchent
   encore — même si le challenge est public.
2. **Les règles de la plateforme priment.** Si elle interdit la publication de solutions
   (Root-Me), le writeup n'a pas sa place ici, même après la clôture de l'épreuve.

Un doute sur un cas limite ? Ouvre une issue **Suggérer un writeup ou un cours** avant de rédiger,
plutôt que de découvrir le refus en review.

## HackerLab Benin 2026

CTF terminé (novembre 2026), couvert par deux collections distinctes : deux équipes, deux dépôts,
deux rédactions. Les dossiers portent le nom du dépôt d'origine.

### Collection 1 — DazBot13-boopt (35 fiches)

Les 35 fiches viennent du dépôt
[DazBot13-boopt/hackerlab-benin-2026-wu](https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu),
écrites par **DazBot13-boopt** et **elielfresnel**, intégrées ici avec leur accord.

Le corps de chaque fiche est repris tel quel : seul le frontmatter de ce dépôt a été ajouté.
Les flags affichés sont ceux de l'épreuve, close à la date d'import.

| Épreuve | Questions couvertes | Préfixe de dossier |
| --- | --- | --- |
| The Fall of JANUS (forensics) | Q1–Q5, Q8, Q9 — Q6 et Q7 non résolues | `janus-*` |
| Last Departure / Northline (web) | Q4 | `northline-*` |
| Harmattan (OSINT) | Q1 | `harmattan-*` |
| The Fall of Memento (misc) | Q1–Q3 | `memento-*` |
| Sail Away (ICS) | Q2–Q4 | `sail-away-*` |
| Kiss of Death (misc) | Q6 | `kiss-of-death-*` |
| FBI Valdoria (AD) | Q11, Q12 | `fbi-valdoria-*`, `sealed-order-*`, `core-systems-*` |
| Épreuves isolées | crypto, pwn, web, forensics, misc | `vault-*`, `lockbox`, `cagliostro`… |

### Collection 2 — H4ckd4ne (33 fiches)

Les 33 fiches viennent du dépôt
[H4ckd4ne/hackerlab2026-writeups](https://github.com/H4ckd4ne/hackerlab2026-writeups), publié sous
**CC BY-SA 4.0**, la licence de ce dépôt : reprise autorisée avec attribution. Les writeups sont
signés par les membres de l'équipe **7H3_D4RK_R007**, 3ᵉ de la finale avec 14 934 points.

| Mission | Fiches | Points documentés | Préfixe de dossier |
| --- | --- | --- | --- |
| Janus | 6 | 500 | `janus-*` |
| Operation Tervalis | 5 | 550 | `tervalis-*` |
| AIZEN | 4 | 800 | `aizen-*` |
| Northline Interception | 4 | 220 | `northline-*` |
| Sail Away | 3 | 350 | `sail-away-*` |
| Ghost Authority | 2 | — | `ghost-authority-*` |
| Kiss | 2 | 400 | `kiss-*` |
| Contingency Protocol | 1 | 200 | `contingency-protocol-*` |
| Operation BATMAN | 1 | 500 | `harmattan-*` |
| Human After All | 1 | 100 | `human-after-all-*` |
| Inside Job | 1 | 150 | `inside-job-*` |
| Memento | 1 | 200 | `memento-*` |
| The Fugitive | 1 | 200 | `the-fugitive` |
| Toguro Tempest | 1 | 500 | `toguro-tempest` |
| **Total** | **33** | **4 670** | |

**Modifications apportées**, comme l'exige la CC BY-SA : ajout du frontmatter de ce dépôt,
images déplacées dans `assets/` de chaque fiche, et réécriture des seuls chemins de ces images.
Aucun texte technique n'a été modifié.

### Rangement

Les fiches sont rangées à plat (`autres/hackerlab-benin-2026*/<slug>/`) : le regroupement par
épreuve passe par le préfixe du dossier et le champ `category` du frontmatter.

**Crédits.** Collection 1 : © DazBot13-boopt et elielfresnel. Collection 2 : © H4ckd4ne et les
auteurs signés, sous CC BY-SA 4.0. En cas de réutilisation, citer les auteurs et le dépôt d'origine.

## Challenges publiés

<!-- INDEX:START -->

| Plateforme / CTF | Challenge | Catégorie | Difficulté | Auteur | Date | Writeup |
| --- | --- | --- | --- | --- | --- | --- |
| HackerLab Benin 2026 (H4ckd4ne) | AIZEN · Fujiko Mine | web-crypto | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/aizen-fujiko-mine/) |
| HackerLab Benin 2026 (H4ckd4ne) | AIZEN · Ishikawa Goemon | web-hsm | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/aizen-ishikawa-goemon/) |
| HackerLab Benin 2026 (H4ckd4ne) | AIZEN · Vantage Hosting | web | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/aizen-vantage-hosting/) |
| HackerLab Benin 2026 (H4ckd4ne) | AIZEN · Zenigata | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/aizen-zenigata/) |
| HackerLab Benin 2026 | Broken Relay · AD1 + relay.db | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/broken-relay/) |
| HackerLab Benin 2026 | Cagliostro · LFI + JWT + WeasyPrint | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/cagliostro/) |
| HackerLab Benin 2026 | CashCache · ATO WordPress → JWT → PJL | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/cashcache/) |
| HackerLab Benin 2026 (H4ckd4ne) | Contingency Protocol · Dossier Varga | web3 | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/contingency-protocol-dossier-varga/) |
| HackerLab Benin 2026 | Core Systems Q12 · RBCD via LDAP | ad | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/core-systems-q12-rbcd/) |
| HackerLab Benin 2026 | Death Match · Battle 01 · SSTI Jinja2 | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/deathmatch-battle-01/) |
| HackerLab Benin 2026 | FBI Valdoria Q11 · Deep Archive | ad | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/fbi-valdoria-q11-deep-archive/) |
| HackerLab Benin 2026 | FBI Valdoria Q12 · Core Systems | ad | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/fbi-valdoria-q12-core-systems/) |
| HackerLab Benin 2026 | Forensic Recovery · Git + GPG | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/forensic-recovery/) |
| HackerLab Benin 2026 (H4ckd4ne) | Ghost Authority · Ghost Authority (partie 1) | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/ghost-authority-partie-1/) |
| HackerLab Benin 2026 (H4ckd4ne) | Ghost Authority · Ghost Authority (partie 2) | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/ghost-authority-partie-2/) |
| HackerLab Benin 2026 | Harmattan Q1 · Operation BATMAN | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/harmattan-q1-operation-batman/) |
| HackerLab Benin 2026 (H4ckd4ne) | Human After All · Human After All 1 | misc-web | — | [0xS0ra](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/human-after-all-1/) |
| HackerLab Benin 2026 | Human After All · Phishing SMTP | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/human-after-all/) |
| HackerLab Benin 2026 | Inside Job Q1 · Reset Password Poisoning | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/inside-job-q1-reset-poisoning/) |
| HackerLab Benin 2026 | Inside Job Q2 · AES-256-CBC | crypto | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/inside-job-q2-aes-256-cbc/) |
| HackerLab Benin 2026 | Inside Job Q3 · Table convoy_route | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/inside-job-q3-table-base64/) |
| HackerLab Benin 2026 (H4ckd4ne) | Inside Job · LockBox | misc | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/inside-job-lockbox/) |
| HackerLab Benin 2026 | JANUS Q1 · Ransomless | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q1-ransomless/) |
| HackerLab Benin 2026 | JANUS Q2 · The Trojan Horse | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q2-trojan-horse/) |
| HackerLab Benin 2026 | JANUS Q3 · New Blood | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q3-new-blood/) |
| HackerLab Benin 2026 | JANUS Q4 · Royal Heist | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q4-royal-heist/) |
| HackerLab Benin 2026 | JANUS Q5 · No Witnesses | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q5-no-witnesses/) |
| HackerLab Benin 2026 | JANUS Q8 · True Identity | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q8-true-identity/) |
| HackerLab Benin 2026 | JANUS Q9 · Hidden Treasure | forensics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/janus-q9-hidden-treasure/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · Broken Channel | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-broken-channel/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · Canary | misc | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-canary/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · Conspiracy (note) | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-conspiracy/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · Final Trigger | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-final-trigger/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · Ghost Ratchet | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-ghost-ratchet/) |
| HackerLab Benin 2026 (H4ckd4ne) | Janus · The Hunt | forensics | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/janus-the-hunt/) |
| HackerLab Benin 2026 | Kiss of Death Q6 · Papyrus | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/kiss-of-death-q6-papyrus/) |
| HackerLab Benin 2026 (H4ckd4ne) | Kiss · Jericho | forensics | — | [W1z4rd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/kiss-jericho/) |
| HackerLab Benin 2026 (H4ckd4ne) | Kiss · Papyrus | forensics | — | [W1z4rd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/kiss-papyrus/) |
| HackerLab Benin 2026 | Lockbox · OTP addition digit-wise | crypto | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/lockbox/) |
| HackerLab Benin 2026 | Memento Q1 · Under Seal | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/memento-q1-under-seal/) |
| HackerLab Benin 2026 | Memento Q2 · Shooting Window | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/memento-q2-shooting-window/) |
| HackerLab Benin 2026 | Memento Q3 · The Hideout | misc | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/memento-q3-the-hideout/) |
| HackerLab Benin 2026 (H4ckd4ne) | Memento · Under Seal | misc-forensics | — | [Johans585](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/memento-under-seal/) |
| HackerLab Benin 2026 (H4ckd4ne) | Northline Interception · Last Departure | web | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/northline-last-departure/) |
| HackerLab Benin 2026 (H4ckd4ne) | Northline Interception · THE GATE | web | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/northline-the-gate/) |
| HackerLab Benin 2026 (H4ckd4ne) | Northline Interception · The Passenger | web | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/northline-the-passenger/) |
| HackerLab Benin 2026 (H4ckd4ne) | Northline Interception · WINDOW | web | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/northline-window/) |
| HackerLab Benin 2026 | Northline Q4 · WINDOW | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/northline-q4-window/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation BATMAN · Operation BATMAN | web-osint | — | [5c0r7](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/harmattan-operation-batman/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation Tervalis · Dead Drop (AIZEN Package 01) | forensics-crypto | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/tervalis-dead-drop/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation Tervalis · File Vault | web-ad | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/tervalis-file-vault/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation Tervalis · Invisible Relay | network-forensics | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/tervalis-invisible-relay/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation Tervalis · Silent Broker | web | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/tervalis-silent-broker/) |
| HackerLab Benin 2026 (H4ckd4ne) | Operation Tervalis · Subject File | web-ad | — | [Unpasswd](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/tervalis-subject-file/) |
| HackerLab Benin 2026 | Sail Away Q2 · Flow In | ics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/sail-away-q2-flow-in/) |
| HackerLab Benin 2026 | Sail Away Q3 · Welcome to the Machine | ics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/sail-away-q3-welcome-to-the-machine/) |
| HackerLab Benin 2026 | Sail Away Q4 · Renegade | ics | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/sail-away-q4-renegade/) |
| HackerLab Benin 2026 (H4ckd4ne) | Sail Away · Catch Me | osint | — | [Sh1n](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/sail-away-catch-me/) |
| HackerLab Benin 2026 (H4ckd4ne) | Sail Away · Flow In | web | — | [Sh1n](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/sail-away-flow-in/) |
| HackerLab Benin 2026 (H4ckd4ne) | Sail Away · Welcome to the Machine | crypto-web | — | [Sh1n](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/sail-away-welcome-to-the-machine/) |
| HackerLab Benin 2026 | Sealed Order Q11 · Délégation contrainte S4U | ad | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/sealed-order-q11-constrained-delegation/) |
| HackerLab Benin 2026 | Silent Broker · CVE-2023-46604 ActiveMQ | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/silent-broker/) |
| HackerLab Benin 2026 | Stay Behind · AWS IAM persistence | web | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/stay-behind/) |
| HackerLab Benin 2026 | Subject File · SMB share caché Recon-Data | ad | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/subject-file/) |
| HackerLab Benin 2026 (H4ckd4ne) | The Fugitive · The Fugitive | misc | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/the-fugitive/) |
| HackerLab Benin 2026 (H4ckd4ne) | Toguro Tempest · Toguro Tempest | misc | — | [H4ckd4ne](https://github.com/H4ckd4ne) | 2026-11-20 | [Writeup](hackerlab-benin-2026-h4ckd4ne/toguro-tempest/) |
| HackerLab Benin 2026 | Vault 0037 · Feistel8 + AES-KW | crypto | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/vault-0037/) |
| HackerLab Benin 2026 | Vault KeyCtl · Truncation entière + OOB | pwn | — | [DazBot13-boopt, elielfresnel](https://github.com/DazBot13-boopt) | 2026-11-20 | [Writeup](hackerlab-benin-2026/vault-keyctl/) |

<!-- INDEX:END -->

## Ajouter un writeup

Depuis la **racine du dépôt** :

```bash
python3 scripts/new_writeup.py     # choisir « autres », puis le nom de la plateforme
```

Ou à la main :

```bash
cp -r writeups/_template writeups/autres/picoctf/nom-du-challenge
$EDITOR writeups/autres/picoctf/nom-du-challenge/README.md
python3 scripts/update_index.py
```

Le dossier de plateforme est en kebab-case minuscule (`picoctf`, `portswigger`, `404ctf-2025`),
mais le champ `platform` du frontmatter porte le **vrai nom** (`PicoCTF`, `PortSwigger`,
`404CTF 2025`) : c'est lui qui s'affiche dans la colonne « Plateforme / CTF ».

Renseigne aussi `category` (`web`, `crypto`, `reverse`, `pwn`, `forensics`, `misc`…) et
`difficulty` : ce sont les colonnes qui permettent de retrouver un writeup dans l'index.
