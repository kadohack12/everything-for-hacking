#!/usr/bin/env python3
"""Refuse les flags en clair et les secrets dans les fichiers versionnés.

Détecte :
  - les flags des plateformes (préfixes HTB, THM, FCSC, CTF) ;
  - les clés privées (bloc PEM « PRIVATE KEY ») ;
  - les jetons d'API courants (AWS, GitHub, Slack, OpenAI) ;
  - les fichiers de credentials (`.ovpn`, `.p12`, `.pfx`, `.kdbx`, clés SSH).

Les valeurs sont masquées dans la sortie : les logs de CI sont publics.
Un faux positif se neutralise avec un commentaire `secret-scan:ignore` sur la
ligne concernée, ou `secret-scan:ignore-file` n'importe où dans le fichier.

Usage : python3 scripts/check_secrets.py [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, is_ignored_dir  # noqa: E402

TEMPLATE_DIRNAME = "_template"
MAX_SIZE = 2 * 1024 * 1024
IGNORE_LINE = "secret-scan:ignore"
IGNORE_FILE = "secret-scan:ignore-file"

# Construits par concaténation pour que ce fichier ne se détecte pas lui-même.
FLAG_PREFIXES = ("HTB", "THM", "FCSC", "CTF")
FLAG_RE = re.compile(r"\b(" + "|".join(FLAG_PREFIXES) + r")\{([^}\n]{0,200})\}")
PLACEHOLDER_RE = re.compile(r"^[\s.*_…<>/\\-]*$", re.IGNORECASE)
PRIVATE_KEY_RE = re.compile("-----BEGIN " + r"(?:[A-Z0-9 ]+ )?PRIVATE KEY-----")

TOKEN_PATTERNS = (
    ("clé d'accès AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jeton GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("jeton Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b")),
    ("clé OpenAI", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
)

SENSITIVE_SUFFIXES = {".ovpn": "profil VPN (credentials)", ".p12": "trousseau PKCS#12", ".pfx": "trousseau PKCS#12", ".kdbx": "base KeePass"}
SENSITIVE_NAMES = {"id_rsa": "clé privée SSH", "id_ed25519": "clé privée SSH", "id_ecdsa": "clé privée SSH"}


def candidate_files(root: Path) -> list[Path]:
    """Fichiers versionnés + non ignorés (ce qui partirait dans un commit)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=True,
        )
        names = [n for n in result.stdout.decode("utf-8", "replace").split("\0") if n]
        return [root / name for name in names]
    except (OSError, subprocess.CalledProcessError):
        return [
            path
            for path in sorted(root.rglob("*"))
            if path.is_file() and not any(is_ignored_dir(part) for part in path.relative_to(root).parts[:-1])
        ]


def mask(value: str, keep: int = 4) -> str:
    return value[:keep] + "…" if len(value) > keep else "…"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    problems: list[str] = []
    scanned = 0
    for path in candidate_files(root):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if TEMPLATE_DIRNAME in rel.parts or any(is_ignored_dir(p) for p in rel.parts[:-1]):
            continue

        suffix = path.suffix.lower()
        if suffix in SENSITIVE_SUFFIXES or path.name in SENSITIVE_NAMES:
            problems.append(f"{rel}  fichier de credentials ({SENSITIVE_SUFFIXES.get(suffix, SENSITIVE_NAMES.get(path.name, ''))})")
            continue

        if path.stat().st_size > MAX_SIZE:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue  # binaire
        text = data.decode("utf-8", "replace")
        if IGNORE_FILE in text:
            continue
        scanned += 1

        for number, line in enumerate(text.splitlines(), 1):
            if IGNORE_LINE in line:
                continue
            for match in FLAG_RE.finditer(line):
                if PLACEHOLDER_RE.match(match.group(2)):
                    continue  # FCSC{...} : exemple de documentation
                problems.append(f"{rel}:{number}  flag en clair ({match.group(1)}) → {match.group(1)}{{{mask(match.group(2), 0)}}}")
            if PRIVATE_KEY_RE.search(line):
                problems.append(f"{rel}:{number}  clé privée (bloc PEM PRIVATE KEY)")
            for label, pattern in TOKEN_PATTERNS:
                if pattern.search(line):
                    problems.append(f"{rel}:{number}  {label} en clair")

    print(f"{scanned} fichier(s) texte analysé(s) dans {root}")
    if problems:
        print(f"\n❌ {len(problems)} secret(s) ou flag(s) détecté(s) :", file=sys.stderr)
        for problem in problems:
            print(f"   {problem}", file=sys.stderr)
        print("\n   Retirer la valeur (la tronquer : `FCSC{...}`), ou ajouter", file=sys.stderr)
        print("   `secret-scan:ignore` sur la ligne s'il s'agit d'un faux positif.", file=sys.stderr)
        return 1
    print("✅ Aucun flag en clair, clé privée ni fichier de credentials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
