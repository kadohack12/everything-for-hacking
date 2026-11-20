#!/usr/bin/env python3
"""Vérifie que tous les liens relatifs et images locales existent.

Ignore les blocs de code, les liens externes et le dossier `_template/`.

Usage : python3 scripts/check_links.py [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, is_ignored_dir, iter_markdown_files  # noqa: E402

TEMPLATE_DIRNAME = "_template"

FENCE_OPEN_RE = re.compile(r"^(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>\s]*>|[^)\s]+)(?:\s+[\"'(][^)]*)?\)")
DEFINITION_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)")
HTML_ATTR_RE = re.compile(
    r"""<(?:img|a|source|video|audio)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")


def strip_code(text: str) -> list[str]:
    """Neutralise les blocs de code en conservant la numérotation des lignes."""
    lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence:
            if stripped.startswith(fence):
                fence = None
            lines.append("")
            continue
        match = FENCE_OPEN_RE.match(stripped)
        if match:
            fence = match.group(1)
            lines.append("")
            continue
        lines.append(INLINE_CODE_RE.sub("", line))
    return lines


def is_relative(target: str) -> bool:
    if not target or target.startswith(("#", "//")):
        return False
    return not SCHEME_RE.match(target)


def resolve(markdown: Path, target: str, root: Path) -> Path:
    cleaned = target.strip()
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1]
    cleaned = unquote(cleaned.split("#", 1)[0].split("?", 1)[0]).strip()
    if not cleaned:
        return markdown  # ancre seule
    if cleaned.startswith("/"):
        return (root / cleaned.lstrip("/")).resolve()
    return (markdown.parent / cleaned).resolve()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root.resolve()

    problems: list[tuple[str, int, str]] = []
    checked = 0
    for markdown in iter_markdown_files(root):
        rel = markdown.relative_to(root)
        if TEMPLATE_DIRNAME in rel.parts or any(is_ignored_dir(p) for p in rel.parts[:-1]):
            continue
        for number, line in enumerate(strip_code(markdown.read_text(encoding="utf-8", errors="replace")), 1):
            targets = [m.group(1) for m in LINK_RE.finditer(line)]
            targets += [m.group(1) for m in HTML_ATTR_RE.finditer(line)]
            definition = DEFINITION_RE.match(line)
            if definition:
                targets.append(definition.group(1))
            for target in targets:
                if not is_relative(target):
                    continue
                checked += 1
                if not resolve(markdown, target, root).exists():
                    problems.append((str(rel), number, target))

    print(f"{checked} lien(s) relatif(s) vérifié(s) dans {root}")
    if problems:
        print(f"\n❌ {len(problems)} lien(s) cassé(s) :", file=sys.stderr)
        for path, number, target in problems:
            print(f"   {path}:{number}  →  {target}", file=sys.stderr)
        print("\n   Corriger le chemin, ou retirer le lien s'il pointe vers un fichier non versionné.", file=sys.stderr)
        return 1
    print("✅ Tous les liens relatifs et images locales existent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
