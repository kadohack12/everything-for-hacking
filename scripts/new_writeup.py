#!/usr/bin/env python3
"""Assistant interactif : crée un nouveau writeup prêt à remplir.

Pose les questions (plateforme, catégorie, nom, difficulté, édition/OS, auteur),
convertit le nom en kebab-case, copie `writeups/_template/` et pré-remplit le
frontmatter YAML (date du jour, `author`, `status: draft`).

Usage interactive :
    python3 scripts/new_writeup.py

Usage non interactive (scripts, tests) :
    python3 scripts/new_writeup.py --platform hackthebox --name "Blue" \
        --difficulty Easy --extra Windows --author "Kadohack12"

Bibliothèque standard uniquement.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path("writeups") / "_template"

PLATFORMS = {
    "hackthebox": {
        "label": "Hack The Box",
        "base": "writeups/hackthebox/Machines",
        "category": "Machine",
        "extra_key": "os",
        "extra_label": "Système (os)",
        "extra_default": "Linux",
        "difficulty_default": "Easy",
    },
    "tryhackme": {
        "label": "TryHackMe",
        "base": "writeups/tryhackme/Rooms",
        "category": "Room",
        "extra_key": "os",
        "extra_label": "Système (os)",
        "extra_default": "Linux",
        "difficulty_default": "Easy",
    },
    "hackropole": {
        "label": "Hackropole",
        "base": "writeups/hackropole.fr/Challenges",
        "category": None,
        "extra_key": "edition",
        "extra_label": "Édition FCSC",
        "extra_default": "2025",
        "difficulty_default": "Intro",
    },
}
HACKROPOLE_CATEGORIES = ("crypto", "web", "reverse", "pwn", "forensics", "hardware", "misc")
IMAGE_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(assets/[^)]*\)\s*$", re.MULTILINE)
NO_INPUT = False


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^A-Za-z0-9]+", "-", value)
    return re.sub(r"-{2,}", "-", value).strip("-").lower()


def ask(prompt: str, default: str = "", choices: tuple[str, ...] | None = None) -> str:
    if NO_INPUT:
        if default:
            return default
        raise SystemExit(f"❌ --no-input : valeur obligatoire manquante ({prompt}).")
    while True:
        hint = f" [{default}]" if default else ""
        listing = f" ({'/'.join(choices)})" if choices else ""
        try:
            answer = input(f"{prompt}{listing}{hint} : ").strip()
        except EOFError:
            raise SystemExit(
                "\n❌ Entrée interrompue. Utilise les options en ligne de commande (--help)."
            )
        if not answer:
            if default:
                return default
            print("   Une valeur est nécessaire.")
            continue
        if choices:
            lowered = answer.lower()
            if lowered.isdigit() and 1 <= int(lowered) <= len(choices):
                return choices[int(lowered) - 1]
            if lowered not in choices:
                print(f"   Choix invalide. Valeurs possibles : {', '.join(choices)}")
                continue
            return lowered
        return answer


def ask_optional(prompt: str, default: str = "") -> str:
    if NO_INPUT:
        return default
    hint = f" [{default}]" if default else ""
    try:
        return input(f"{prompt}{hint} : ").strip() or default
    except EOFError:
        return default


def git_user_name() -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def build_frontmatter(meta: dict) -> str:
    lines = [
        "---",
        f'title: "{meta["title"]}"',
        f'platform: "{meta["platform"]}"',
        f'category: "{meta["category"]}"',
        f'{meta["extra_key"]}: "{meta["extra"]}"',
        f'difficulty: "{meta["difficulty"]}"',
        f'date: {meta["date"]}',
        f'author: "{meta["author"]}"',
    ]
    if meta.get("github"):
        lines.append(f'author_github: "{meta["github"]}"')
    lines += ["tags: []", "status: draft", "---"]
    return "\n".join(lines)


def build_body(template_text: str, meta: dict) -> str:
    parts = template_text.split("---", 2)
    body = parts[2].lstrip("\n") if len(parts) == 3 else template_text
    heading = f'# {meta["title"]} — {meta["platform"]} ({meta["extra"]}, {meta["difficulty"]})'
    body = re.sub(r"^# .*$", heading, body, count=1, flags=re.MULTILINE)
    # Les captures du modèle n'existent pas encore : TODO plutôt que liens morts.
    body = IMAGE_LINE_RE.sub(lambda m: f"[TODO: capture — {m.group(1)}]", body)
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--platform", choices=tuple(PLATFORMS), help="plateforme")
    parser.add_argument("--category", help="catégorie Hackropole (crypto, web…)")
    parser.add_argument("--name", help="nom du challenge ou de la machine")
    parser.add_argument("--difficulty", help="difficulté (Intro, Easy, Medium…)")
    parser.add_argument("--extra", help="système (os) ou édition FCSC")
    parser.add_argument("--author", help="nom affiché dans l'index")
    parser.add_argument("--github", help="login GitHub (optionnel)")
    parser.add_argument("--root", type=Path, default=ROOT, help="racine du dépôt")
    parser.add_argument("--no-input", action="store_true", help="ne poser aucune question (défauts)")
    args = parser.parse_args(argv)
    global NO_INPUT
    NO_INPUT = args.no_input
    root = args.root.resolve()

    template = root / TEMPLATE
    if not (template / "README.md").is_file():
        print(f"❌ Modèle introuvable : {template}", file=sys.stderr)
        return 1

    if not args.platform and not NO_INPUT:
        print("Nouveau writeup — quelques questions (Entrée = valeur par défaut).\n")
    platform = args.platform or ask("Plateforme", "hackthebox", tuple(PLATFORMS))
    spec = PLATFORMS[platform]

    if platform == "hackropole":
        category = args.category or ask("Catégorie", HACKROPOLE_CATEGORIES[0], HACKROPOLE_CATEGORIES)
        if category not in HACKROPOLE_CATEGORIES:
            print(f"❌ Catégorie inconnue : {category}", file=sys.stderr)
            return 1
    else:
        category = spec["category"]

    name = args.name or ask("Nom du challenge ou de la machine")
    slug = slugify(name)
    if not slug:
        print("❌ Le nom ne donne pas un dossier valide (lettres/chiffres attendus).", file=sys.stderr)
        return 1

    difficulty = args.difficulty or ask("Difficulté", spec["difficulty_default"])
    extra = args.extra or ask(spec["extra_label"], spec["extra_default"])
    author = args.author or ask("Auteur (ton nom ou pseudo)", git_user_name() or "Anonyme")
    github = args.github if args.github is not None else ask_optional("Login GitHub (optionnel)")

    relative = Path(spec["base"]) / (category if platform == "hackropole" else "") / slug
    target = root / relative
    if target.exists():
        print(f"❌ Le dossier existe déjà : {relative}", file=sys.stderr)
        return 1

    meta = {
        "title": name,
        "platform": spec["label"],
        "category": category,
        "extra_key": spec["extra_key"],
        "extra": extra,
        "difficulty": difficulty,
        "date": date.today().isoformat(),
        "author": author,
        "github": github,
    }

    template_text = (template / "README.md").read_text(encoding="utf-8")
    target.mkdir(parents=True)
    shutil.copytree(template / "assets", target / "assets", dirs_exist_ok=True)
    readme = target / "README.md"
    readme.write_text(build_frontmatter(meta) + "\n\n" + build_body(template_text, meta), encoding="utf-8")

    print(f"\n✅ Writeup créé : {relative}/")
    print(f"   fichier : {readme.relative_to(root)}")
    print(
        "\nProchaines étapes :\n"
        f"  1. édite le fichier      : $EDITOR {readme.relative_to(root)}\n"
        f"  2. dépose tes captures   : {relative}/assets/\n"
        "  3. régénère l'index      : python3 scripts/update_index.py\n"
        "  4. passe `status: draft` à `status: published` quand c'est prêt"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
