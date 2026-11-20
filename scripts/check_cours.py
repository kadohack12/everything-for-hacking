#!/usr/bin/env python3
"""Contrôle rigoureux du dossier `cours/` : structure + empreinte des fichiers.

Deux niveaux :

1. **Structure** — chaque module suit `NN-Nom-Du-Module`, possède un `README.md`
   avec un titre et les sections `## Objectifs` et `## Plan`, et il est référencé
   dans le programme (`cours/README.md`).
2. **Intégrité** — `cours/MANIFEST.sha256` contient l'empreinte de chaque fichier.
   Toute modification du contenu sans régénération du manifeste est signalée :
   c'est ce qui détecte une altération silencieuse d'un cours.

Le manifeste ne peut être régénéré que par un mainteneur (le dossier est protégé
par `scripts/check_cours_protection.py`).

Usage :
    python3 scripts/check_cours.py            # vérifie (code retour 1 si écart)
    python3 scripts/check_cours.py --update   # régénère le manifeste
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COURS_DIRNAME = "cours"
MANIFEST_NAME = "MANIFEST.sha256"
MODULE_RE = re.compile(r"^\d{2}-[A-Za-z0-9-]+$")
H1_RE = re.compile(r"^# \S", re.MULTILINE)
ALLOWED_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf"}
MAX_SIZE = 5 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cours_files(root: Path) -> list[Path]:
    base = root / COURS_DIRNAME
    if not base.is_dir():
        return []
    return [
        path
        for path in sorted(base.rglob("*"))
        if path.is_file()
        and path.name != MANIFEST_NAME
        and "__pycache__" not in path.parts
    ]


def build_manifest(root: Path) -> str:
    lines = [
        "# Intégrité du dossier cours/ — généré par `python3 scripts/check_cours.py --update`\n",
        "# Ne pas éditer à la main : toute modification d'un cours doit être suivie d'une régénération.\n",
    ]
    for path in cours_files(root):
        lines.append(f"{sha256(path)}  {path.relative_to(root).as_posix()}\n")
    return "".join(lines)


def read_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        if digest and name:
            entries[name.strip()] = digest.strip()
    return entries


def check_structure(root: Path) -> list[str]:
    problems: list[str] = []
    base = root / COURS_DIRNAME
    index = base / "README.md"

    if not index.is_file():
        return ["cours/README.md absent"]
    index_text = index.read_text(encoding="utf-8", errors="replace")
    if not H1_RE.search(index_text):
        problems.append("cours/README.md : titre de niveau 1 absent")

    modules = sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("."))
    for module in modules:
        if not MODULE_RE.match(module.name):
            problems.append(f"cours/{module.name}/ : nom attendu « NN-Nom-Du-Module »")
            continue
        readme = module / "README.md"
        if not readme.is_file():
            problems.append(f"cours/{module.name}/ : README.md absent")
        else:
            text = readme.read_text(encoding="utf-8", errors="replace")
            if not H1_RE.search(text):
                problems.append(f"cours/{module.name}/README.md : titre de niveau 1 absent")
            for section in ("## Objectifs", "## Plan"):
                if section not in text:
                    problems.append(f"cours/{module.name}/README.md : section « {section} » absente")
        if f"({module.name}/README.md)" not in index_text and f"({module.name}/)" not in index_text:
            problems.append(f"cours/{module.name}/ : module absent du programme (cours/README.md)")

    for path in cours_files(root):
        if path.name == ".gitkeep":
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            problems.append(f"{rel} : extension non autorisée dans cours/ ({', '.join(sorted(ALLOWED_SUFFIXES))})")
        elif path.stat().st_size > MAX_SIZE:
            problems.append(f"{rel} : fichier trop lourd ({path.stat().st_size // 1024} Kio, max 5 Mio)")
    return problems


def check_manifest(root: Path) -> list[str]:
    manifest = root / COURS_DIRNAME / MANIFEST_NAME
    if not manifest.is_file():
        return [f"cours/{MANIFEST_NAME} absent — lancer : python3 scripts/check_cours.py --update"]

    expected = read_manifest(manifest)
    actual = {path.relative_to(root).as_posix(): sha256(path) for path in cours_files(root)}

    problems: list[str] = []
    for name, digest in actual.items():
        if name not in expected:
            problems.append(f"{name} : fichier non répertorié dans le manifeste (ajout non validé)")
        elif expected[name] != digest:
            problems.append(f"{name} : contenu modifié sans régénération du manifeste")
    for name in expected:
        if name not in actual:
            problems.append(f"{name} : listé dans le manifeste mais absent du dossier")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--update", action="store_true", help="régénérer cours/MANIFEST.sha256")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    base = root / COURS_DIRNAME
    if not base.is_dir():
        print(f"❌ {COURS_DIRNAME}/ introuvable dans {root}", file=sys.stderr)
        return 1

    if args.update:
        manifest = base / MANIFEST_NAME
        manifest.write_text(build_manifest(root), encoding="utf-8")
        print(f"✅ cours/{MANIFEST_NAME} régénéré ({len(cours_files(root))} fichier(s))")
        return 0

    problems = check_structure(root) + check_manifest(root)
    files = cours_files(root)
    print(f"{len(files)} fichier(s) de cours, {sum(1 for p in base.iterdir() if p.is_dir())} module(s)")

    if problems:
        print(f"\n❌ {len(problems)} écart(s) sur cours/ :", file=sys.stderr)
        for problem in problems:
            print(f"   {problem}", file=sys.stderr)
        print(
            "\n   Après une modification volontaire : python3 scripts/check_cours.py --update",
            file=sys.stderr,
        )
        return 1
    print("✅ Structure des cours conforme et empreintes vérifiées")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
