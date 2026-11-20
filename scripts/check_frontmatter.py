#!/usr/bin/env python3
"""Valide la structure et le frontmatter de chaque writeup.

Mode par défaut : **conseils non bloquants** (code retour 0). La CI signale les
écarts sans bloquer une contribution. `--strict` transforme les conseils en
échec, pour un passage de contrôle avant merge.

Contrôles :
  - dossier en kebab-case minuscule (sans accent, sans espace) ;
  - frontmatter avec title, platform, category, difficulty, date, author, status ;
  - status parmi draft / published ;
  - date au format AAAA-MM-JJ ;
  - arborescence conforme à la plateforme (Machines/, Rooms/, Challenges/<catégorie>/) ;
  - hackropole : catégorie connue et identique au dossier ;
  - README.md avec un titre de niveau 1.

Usage :
    python3 scripts/check_frontmatter.py            # conseils, code retour 0
    python3 scripts/check_frontmatter.py --strict   # code retour 1 si écart
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, iter_writeups  # noqa: E402

REQUIRED_FIELDS = ("title", "platform", "category", "difficulty", "date", "author", "status")
ALLOWED_STATUS = {"draft", "published"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
H1_RE = re.compile(r"^# \S", re.MULTILINE)

EXPECTED_LAYOUT = {
    "hackthebox": ("Machines",),
    "tryhackme": ("Rooms",),
    "hackropole.fr": ("Challenges",),
}
HACKROPOLE_CATEGORIES = {"crypto", "web", "reverse", "pwn", "forensics", "hardware", "misc"}


def validate(writeup, root: Path) -> list[str]:
    problems: list[str] = []
    meta = writeup.meta
    rel = writeup.path.relative_to(root)

    for field in REQUIRED_FIELDS:
        if not str(meta.get(field, "")).strip():
            problems.append(f"champ obligatoire manquant ou vide : {field}")

    status = writeup.status
    if status and status not in ALLOWED_STATUS:
        problems.append(f"status « {status} » invalide (attendu : draft ou published)")

    raw_date = str(meta.get("date") or "").strip()
    if raw_date:
        try:
            date.fromisoformat(raw_date)
        except ValueError:
            problems.append(f"date « {raw_date} » invalide (format attendu : AAAA-MM-JJ)")

    if not SLUG_RE.match(writeup.directory.name):
        problems.append(
            f"dossier « {writeup.directory.name} » : kebab-case minuscule attendu "
            "(ex. nom-machine, a-laise)"
        )

    expected = EXPECTED_LAYOUT.get(writeup.platform)
    if expected:
        if writeup.parts[0] != expected[0]:
            problems.append(
                f"arborescence : attendu {writeup.platform}/{expected[0]}/<nom>/, "
                f"trouvé {'/'.join(writeup.parts)}/"
            )
        elif writeup.platform == "hackropole.fr":
            if len(writeup.parts) != 3:
                problems.append(
                    f"arborescence : attendu Challenges/<catégorie>/<nom>/, "
                    f"trouvé {'/'.join(writeup.parts)}/"
                )
            else:
                category_dir = writeup.parts[1]
                if category_dir not in HACKROPOLE_CATEGORIES:
                    problems.append(
                        f"catégorie « {category_dir} » inconnue "
                        f"(attendu : {', '.join(sorted(HACKROPOLE_CATEGORIES))})"
                    )
                if writeup.category and writeup.category != category_dir:
                    problems.append(
                        f"category « {writeup.category} » incohérente avec le dossier "
                        f"« {category_dir} »"
                    )
        elif len(writeup.parts) != 2:
            problems.append(
                f"arborescence : attendu {writeup.platform}/{expected[0]}/<nom>/, "
                f"trouvé {'/'.join(writeup.parts)}/"
            )

    text = writeup.path.read_text(encoding="utf-8", errors="replace")
    if not H1_RE.search(text):
        problems.append("README.md sans titre de niveau 1 (« # Nom du challenge »)")

    return problems


def check_template(root: Path) -> list[str]:
    """Le modèle doit rester un point de départ valide pour les contributeurs."""
    template = root / "writeups" / "_template" / "README.md"
    if not template.is_file():
        return []
    text = template.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ["writeups/_template/README.md : frontmatter absent"]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from writeups_lib import parse_frontmatter

    meta = parse_frontmatter(text)
    missing = [f for f in REQUIRED_FIELDS if not str(meta.get(f, "")).strip()]
    return [f"writeups/_template/README.md : champ manquant : {f}" for f in missing]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", help="échouer au lieu de conseiller")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    failures: dict[str, list[str]] = {}
    warnings: list[str] = []
    count = 0

    for writeup in iter_writeups(root):
        count += 1
        problems = validate(writeup, root)
        if problems:
            failures[str(writeup.path.relative_to(root))] = problems
        if writeup.platform not in EXPECTED_LAYOUT:
            warnings.append(
                f"{writeup.path.relative_to(root)} : plateforme « {writeup.platform} » "
                "non reconnue (l'index utilisera les colonnes par défaut)"
            )

    for problem in check_template(root):
        failures.setdefault("writeups/_template/README.md", []).append(problem)

    print(f"{count} writeup(s) analysé(s) dans {root}")
    for warning in warnings:
        print(f"⚠️  {warning}")
    if failures:
        total = sum(len(v) for v in failures.values())
        icon = "❌" if args.strict else "⚠️ "
        print(f"\n{icon} {total} écart(s) de structure (sur {len(failures)} fichier(s)) :", file=sys.stderr)
        for path, problems in failures.items():
            print(f"   {path}", file=sys.stderr)
            for problem in problems:
                print(f"     - {problem}", file=sys.stderr)
        if args.strict:
            print("\n   Voir CONTRIBUTING.md (structure et frontmatter attendus).", file=sys.stderr)
            return 1
        print("\n   Non bloquant : ces écarts n'empêchent pas la contribution.", file=sys.stderr)
        print("   Le mainteneur peut les corriger au merge ; `--strict` les rend bloquants.", file=sys.stderr)
        return 0
    print("✅ Structure et frontmatter conformes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
