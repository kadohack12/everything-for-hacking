#!/usr/bin/env python3
"""Liste les writeups encore en brouillon (`status: draft`).

Mode par défaut : simple avertissement (code retour 0). `--strict` échoue si un
brouillon existe — utile juste avant de merger sur `main`, puisqu'un brouillon
public peut spoiler une machine encore active.

Usage :
    python3 scripts/check_drafts.py             # avertit, code retour 0
    python3 scripts/check_drafts.py --strict    # échoue si brouillon
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, iter_writeups  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", help="échouer si un brouillon existe")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    drafts = [w for w in iter_writeups(root) if not w.is_published]
    total = sum(1 for _ in iter_writeups(root))

    if not drafts:
        print(f"✅ {total} writeup(s) publié(s), aucun brouillon")
        return 0

    details = []
    for writeup in drafts:
        rel = writeup.path.relative_to(root)
        state = f"status: {writeup.status}" if writeup.status else "status absent"
        details.append(f"   {rel}  ({state})")

    if not args.strict:
        print(f"⚠️  {len(drafts)} brouillon(s) présent(s) :")
        print("\n".join(details))
        print("\n   Non bloquant. Un brouillon n'apparaît pas dans l'index ; ne pas merger")
        print("   un writeup de machine encore active sur main (`--strict` pour bloquer).")
        return 0

    print(f"❌ {len(drafts)} writeup(s) encore en brouillon :", file=sys.stderr)
    print("\n".join(details), file=sys.stderr)
    print(
        "\n   Sur main, un writeup doit être finalisé : passer `status: draft` à `status: published`,\n"
        "   ou retirer le dossier. Un brouillon public = spoiler d'une machine encore active.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
