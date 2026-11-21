---
title: "JANUS Q5 · No Witnesses"
platform: "HackerLab Benin 2026"
category: "forensics"
difficulty: "—"
points: 100
os: "Windows"
date: 2026-11-20
author: "DazBot13-boopt, elielfresnel"
author_github: "DazBot13-boopt"
source: "https://github.com/DazBot13-boopt/hackerlab-benin-2026-wu/blob/main/janus/05-no-witnesses.md"
tags: [hackerlab-benin-2026, forensics]
status: published
---

# The Fall of JANUS : Q5 · No Witnesses (100 pts)

> *« Après l'exfiltration, l'attaquant a supprimé le fichier contenant l'export de la base. Retrouvez la date et l'heure de suppression. »*

Format : `HLB2026{JJ-MM-AAAA_HH:MM}`

## TL;DR

L'USN Journal (`$Extend\$J`) garde l'historique des modifications sur chaque fichier.

**Flag** : `HLB2026{08-11-2026_18:29}`

## Parse USN

```python
import re, struct
from datetime import datetime, timezone

d = open("$J","rb").read()
pat = b"v\x00e\x00r\x00d\x00i\x00c\x00t\x00s\x00_\x00d\x00u\x00m\x00p"

def ft(x):
    return datetime.fromtimestamp(x/1e7 - 11644473600, tz=timezone.utc)

for m in re.finditer(re.escape(pat), d):
    pos = m.start()
    for back in range(16, 512, 4):
        s = pos - back
        if s < 0: break
        rl = struct.unpack("<I", d[s:s+4])[0]
        if 60 <= rl <= 1024 and struct.unpack("<H", d[s+4:s+6])[0] in (2,3):
            fnlen = struct.unpack("<H", d[s+56:s+58])[0]
            fnoff = struct.unpack("<H", d[s+58:s+60])[0]
            fname = d[s+fnoff:s+fnoff+fnlen].decode("utf-16-le","replace")
            if "verdicts_dump.sql" in fname and fname.endswith(".sql"):
                ts = struct.unpack("<Q", d[s+32:s+40])[0]
                reason = struct.unpack("<I", d[s+40:s+44])[0]
                if reason & 0x200:     # FILE_DELETE
                    print(ft(ts), hex(reason), fname)
            break
```

Sortie :

```
2026-11-08 18:28:59.834606 UTC   FILE_DELETE|CLOSE   verdicts_dump.sql
2026-11-08 18:59:35.599018 UTC   FILE_DELETE|CLOSE   verdicts_dump.sql   # ransomware
```

La première suppression (`18:28:59`) est la trace de l'attaquant qui nettoie avant que le ransomware n'arrive 30 min plus tard. Arrondi à la minute supérieure (seconds > 30) → `18:29`.

## Flag

```
HLB2026{08-11-2026_18:29}
```

> **Timezone** : convention UTC pour ce chall (aligné avec Q4).
