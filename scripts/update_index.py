#!/usr/bin/env python3
"""Régénère les tableaux d'index des writeups publiés.

Parcourt `writeups/<plateforme>/`, lit le frontmatter de chaque `README.md`,
ne conserve que `status: published` et réécrit le contenu situé entre
`<!-- INDEX:START -->` / `<!-- INDEX:END -->` (ou leurs variantes nommées
`<!-- INDEX:START:<plateforme> -->`).

Usage :
    python3 scripts/update_index.py           # réécrit les index
    python3 scripts/update_index.py --check   # code retour 1 si un index est périmé
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, Writeup, iter_platform_dirs, iter_writeups  # noqa: E402

DEFAULT_BLOCK = "default"
EMPTY_ROW = "_aucun writeup publié pour le moment_"

COLUMNS_BY_PLATFORM = {
    "hackthebox": [
        ("Machine", "title"),
        ("OS", "os"),
        ("Difficulté", "difficulty"),
        ("Date", "date"),
        ("Writeup", "link"),
    ],
    "tryhackme": [
        ("Room", "title"),
        ("Thème", "category"),
        ("Difficulté", "difficulty"),
        ("Date", "date"),
        ("Writeup", "link"),
    ],
    "hackropole.fr": [
        ("Challenge", "title"),
        ("Catégorie", "category"),
        ("Édition", "edition"),
        ("Date", "date"),
        ("Writeup", "link"),
    ],
}
DEFAULT_COLUMNS = [
    ("Nom", "title"),
    ("Catégorie", "category"),
    ("Difficulté", "difficulty"),
    ("Date", "date"),
    ("Writeup", "link"),
]

START_MARKER = "<!-- INDEX:START -->"
END_MARKER = "<!-- INDEX:END -->"


def escape_cell(value: str) -> str:
    return " ".join(str(value).split()).replace("|", r"\|")


def relative_link(readme: Path, target: Path) -> str:
    rel = os.path.relpath(target, readme.parent).replace(os.sep, "/")
    return quote(rel, safe="/._-~") + "/"


def cell(writeup: Writeup, key: str, readme: Path) -> str:
    if key == "link":
        return f"[Writeup]({relative_link(readme, writeup.directory)})"
    if key == "title":
        return escape_cell(writeup.title)
    if key == "category":
        return escape_cell(writeup.category or "—")
    if key == "edition":
        return escape_cell(writeup.field("edition"))
    if key == "date":
        return escape_cell(writeup.field("date"))
    return escape_cell(writeup.field(key))


def render_table(writeups: list[Writeup], columns, readme: Path) -> str:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    # Tri : date décroissante puis titre croissant (deux passes stables).
    ordered = sorted(writeups, key=lambda w: w.title.lower())
    ordered.sort(key=lambda w: str(w.meta.get("date") or ""), reverse=True)
    rows = [
        "| " + " | ".join(cell(w, key, readme) for _, key in columns) + " |"
        for w in ordered
    ]
    if not rows:
        rows = ["| " + " | ".join([EMPTY_ROW] + [""] * (len(columns) - 1)) + " |"]
    return "\n".join([header, separator, *rows])


def apply_blocks(text: str, blocks: dict[str, str], where: str) -> tuple[str, set[str]]:
    """Remplace le corps de chaque bloc délimité par les marqueurs INDEX."""
    out: list[str] = []
    used: set[str] = set()
    pos = 0
    while True:
        start = text.find(START_MARKER, pos)
        named = None
        if start == -1:
            named = _find_named_start(text, pos)
            if named is None:
                out.append(text[pos:])
                return "".join(out), used
            start, name = named
        else:
            name = DEFAULT_BLOCK
        if name not in blocks:
            known = ", ".join(sorted(blocks)) or "aucun"
            raise SystemExit(
                f"{where} : bloc INDEX « {name} » sans contenu à générer (blocs connus : {known})"
            )
        end_marker = END_MARKER if name == DEFAULT_BLOCK else f"<!-- INDEX:END:{name} -->"
        end = text.find(end_marker, start)
        if end == -1:
            raise SystemExit(f"{where} : marqueur de fin manquant, attendu « {end_marker} »")
        out.append(text[pos:start])
        out.append(f"{START_MARKER if name == DEFAULT_BLOCK else f'<!-- INDEX:START:{name} -->'}")
        out.append("\n\n" + blocks[name] + "\n\n")
        out.append(end_marker)
        used.add(name)
        pos = end + len(end_marker)


def _find_named_start(text: str, pos: int):
    """Cherche le prochain `<!-- INDEX:START:<nom> -->` à partir de `pos`."""
    marker = "<!-- INDEX:START:"
    index = text.find(marker, pos)
    if index == -1:
        return None
    end = text.find(" -->", index + len(marker))
    if end == -1:
        return None
    return index, text[index + len(marker) : end].strip()


def build_targets(root: Path) -> dict[Path, dict[str, str]]:
    published: dict[str, list[Writeup]] = defaultdict(list)
    for writeup in iter_writeups(root):
        if writeup.is_published:
            published[writeup.platform].append(writeup)

    targets: dict[Path, dict[str, str]] = {}
    platforms = list(iter_platform_dirs(root))

    index_readme = root / "writeups" / "README.md"
    if index_readme.is_file():
        targets[index_readme] = {
            platform.name: render_table(
                published.get(platform.name, []),
                COLUMNS_BY_PLATFORM.get(platform.name, DEFAULT_COLUMNS),
                index_readme,
            )
            for platform in platforms
        }

    for platform in platforms:
        readme = platform / "README.md"
        if not readme.is_file():
            continue
        targets[readme] = {
            DEFAULT_BLOCK: render_table(
                published.get(platform.name, []),
                COLUMNS_BY_PLATFORM.get(platform.name, DEFAULT_COLUMNS),
                readme,
            )
        }
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT, help="racine du dépôt (défaut : racine du projet)")
    parser.add_argument("--check", action="store_true", help="ne rien écrire, échouer si un index est périmé")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    targets = build_targets(root)
    if not targets:
        print("Aucun index à mettre à jour (writeups/ introuvable ?).", file=sys.stderr)
        return 1

    stale: list[Path] = []
    missing_markers: list[str] = []
    for path, blocks in targets.items():
        original = path.read_text(encoding="utf-8")
        updated, used = apply_blocks(original, blocks, str(path.relative_to(root)))
        unused = set(blocks) - used
        if unused:
            missing_markers.append(str(path.relative_to(root)))
            print(
                f"⚠️  {path.relative_to(root)} : bloc(s) sans marqueur INDEX — {', '.join(sorted(unused))}",
                file=sys.stderr,
            )
        if updated != original:
            stale.append(path)
            if not args.check:
                path.write_text(updated, encoding="utf-8")

    total = sum(1 for _ in iter_writeups(root))
    drafts = sum(1 for w in iter_writeups(root) if not w.is_published)
    print(f"{total - drafts} writeup(s) publié(s), {drafts} brouillon(s) ignoré(s)")

    if args.check and missing_markers:
        print(
            f"❌ Marqueurs INDEX manquants dans : {', '.join(missing_markers)}",
            file=sys.stderr,
        )
        return 1

    if stale:
        names = ", ".join(str(p.relative_to(root)) for p in stale)
        if args.check:
            print(f"❌ Index périmé : {names}", file=sys.stderr)
            print("   Corriger avec : python3 scripts/update_index.py", file=sys.stderr)
            return 1
        print(f"✅ Index mis à jour : {names}")
    else:
        print("✅ Index déjà à jour")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
