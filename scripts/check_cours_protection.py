#!/usr/bin/env python3
"""Refuse toute modification de `cours/` par un contributeur non mainteneur.

`cours/` est un espace éditorial : les propositions passent par une issue, la
rédaction reste au mainteneur. Les logins autorisés sont listés dans
`.github/MAINTAINERS` (un par ligne).

Usage :
    python3 scripts/check_cours_protection.py --actor <login> --base origin/main
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROTECTED_PREFIX = "cours/"
MAINTAINERS_FILE = Path(".github") / "MAINTAINERS"


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def read_maintainers(root: Path) -> set[str]:
    path = root / MAINTAINERS_FILE
    if not path.is_file():
        return set()
    logins = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().lstrip("@")
        if line:
            logins.add(line.lower())
    return logins


def changed_files(root: Path, base: str) -> list[str] | None:
    for revspec in (f"{base}...HEAD", f"{base}..HEAD"):
        result = git(root, "diff", "--name-only", revspec)
        if result.returncode == 0:
            return [line for line in result.stdout.splitlines() if line.strip()]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--actor", default=os.environ.get("GITHUB_ACTOR", ""), help="login GitHub de l'auteur")
    parser.add_argument("--base", default="origin/main", help="référence de base (défaut : origin/main)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    maintainers = read_maintainers(root)
    actor = (args.actor or "").strip().lstrip("@").lower()

    files = changed_files(root, args.base)
    if files is None:
        print(f"⚠️  Vérification ignorée : impossible de comparer avec « {args.base} ».")
        print("   (en CI, récupérer la branche de base avant d'appeler ce script)")
        return 0

    touched = [f for f in files if f.startswith(PROTECTED_PREFIX)]
    if not touched:
        print(f"✅ Aucun fichier de {PROTECTED_PREFIX} modifié ({len(files)} fichier(s) comparé(s))")
        return 0

    if actor and actor in maintainers:
        print(f"✅ {actor} est mainteneur : {len(touched)} fichier(s) de cours/ autorisé(s)")
        return 0

    print(f"❌ Modification de {PROTECTED_PREFIX} par « {actor or 'inconnu'} » :", file=sys.stderr)
    for path in touched[:15]:
        print(f"   {path}", file=sys.stderr)
    if len(touched) > 15:
        print(f"   … et {len(touched) - 15} autre(s)", file=sys.stderr)
    print(
        "\n   Le dossier cours/ est réservé aux mainteneurs (voir CONTRIBUTING.md).\n"
        "   Ouvre une issue « Améliorer un cours » plutôt qu'une PR directe :\n"
        "   la proposition sera relue et intégrée par un mainteneur.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
