#!/usr/bin/env python3
"""Prépare le site statique (mkdocs) à partir des Markdown du dépôt.

Le dépôt n'est pas une arborescence de documentation classique : les pages
s'appellent `README.md`, les dossiers contiennent des `assets/`, et les liens
relatifs pointent vers des `README.md`. Ce script assemble un `docs_dir`
propre pour mkdocs :

  1. copie les Markdown, les `assets/` et la licence dans `build/docs/` ;
  2. renomme chaque `README.md` en `index.md` (une page par dossier) ;
  3. réécrit les liens `…/README.md` en `…/index.md` pour qu'ils restent valides ;
  4. génère `build/mkdocs.yml` avec un `nav` déduit des titres (frontmatter ou H1).

Usage :
    python3 scripts/build_docs.py            # prépare build/
    mkdocs build -f build/mkdocs.yml -d site # construit le site

Aucune dépendance : seul mkdocs (installé en CI) est requis pour l'étape 2.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from writeups_lib import ROOT, parse_frontmatter  # noqa: E402

BUILD_DIR = ROOT / "build"
DOCS_DIR = BUILD_DIR / "docs"
SITE_URL = "https://kadohack12.github.io/everything-for-hacking/"
REPO_URL = "https://github.com/kadohack12/everything-for-hacking"

SKIP_DIRS = {".git", ".github", ".openhands", "build", "site", "scripts", "node_modules", "__pycache__"}
SKIP_DIR_PREFIXES = ("_", ".")

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
README_LINK_RE = re.compile(r"(\]\((?:[^)\s]*/)?)README\.md((?:#[^)\s]*)?\))")
TEMPLATE_LINK_RE = re.compile(r"\]\((?:[^)\s]*/)?_template/(?:index|README)\.md((?:#[^)\s]*)?)\)")
DOTFILE_LINK_RE = re.compile(r"\]\((?:\.\./)*(\.github|scripts)/[^)\s]+\)")


def is_skipped(path: Path) -> bool:
    return path.name in SKIP_DIRS or path.name.startswith(SKIP_DIR_PREFIXES)


def natural_key(path: Path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def page_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = parse_frontmatter(text)
    title = str(meta.get("title") or "").strip()
    if title:
        return title
    match = H1_RE.search(text)
    return match.group(1).strip() if match else path.parent.name.replace("-", " ").title()


def copy_tree(src: Path, dst: Path) -> None:
    for entry in src.iterdir():
        if is_skipped(entry):
            continue
        target = dst / entry.name
        if entry.is_dir():
            if entry.name == "assets":
                shutil.copytree(entry, target, dirs_exist_ok=True)
                continue
            target.mkdir(parents=True, exist_ok=True)
            copy_tree(entry, target)
        elif entry.suffix.lower() in {".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".sha256"}:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)
        elif entry.name in {"LICENSE", "LICENCE"}:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, target)


def rename_readmes(directory: Path) -> None:
    for readme in sorted(directory.rglob("README.md")):
        readme.rename(readme.with_name("index.md"))


def rewrite_links(directory: Path) -> int:
    changed = 0
    for page in directory.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        new = README_LINK_RE.sub(r"\1index.md\2", text)
        # le modèle n'est pas publié (dossier _*) : renvoyer vers GitHub
        new = TEMPLATE_LINK_RE.sub(lambda m: f"]({REPO_URL}/tree/main/writeups/_template{m.group(1)})", new)
        # les fichiers de .github/ ne sont pas publiés : renvoyer vers GitHub
        new = DOTFILE_LINK_RE.sub(lambda m: f"]({REPO_URL}/tree/main/{m.group(1)})", new)
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def build_nav(directory: Path, rel: Path):
    """Retourne la liste des entrées de navigation d'un dossier."""
    index = directory / "index.md"
    children: list = []
    for entry in sorted(directory.iterdir(), key=natural_key):
        if entry.is_dir() and not is_skipped(entry) and entry.name != "assets":
            children.extend(build_nav(entry, rel / entry.name))
        elif entry.suffix == ".md" and entry.name != "index.md":
            children.append({page_title(entry): (rel / entry.name).as_posix()})

    if not rel.parts:
        return [{"Accueil": "index.md"}, *children]
    if index.exists():
        page = (rel / "index.md").as_posix()
        title = page_title(index)
        return [{title: [{"Vue d'ensemble": page}, *children]}]
    if children:
        return [{directory.name.replace("-", " "): children}]
    return []


def write_config(nav) -> Path:
    config = BUILD_DIR / "mkdocs.yml"
    lines = [
        "site_name: Everything For Hacking",
        "site_description: Writeups CTF (Hack The Box, TryHackMe, Hackropole) et cours de cybersécurité",
        f"site_url: {SITE_URL}",
        f"repo_url: {REPO_URL}",
        "repo_name: kadohack12/everything-for-hacking",
        "edit_uri: edit/main/",
        "docs_dir: docs",
        "use_directory_urls: true",
        "theme:",
        "  name: material",
        "  language: fr",
        "  features:",
        "    - navigation.sections",
        "    - navigation.top",
        "    - navigation.footer",
        "    - search.suggest",
        "    - search.highlight",
        "    - content.code.copy",
        "    - toc.follow",
        "  palette:",
        "    - media: '(prefers-color-scheme: light)'",
        "      scheme: default",
        "      toggle:",
        "        icon: material/weather-night",
        "        name: Thème sombre",
        "    - media: '(prefers-color-scheme: dark)'",
        "      scheme: slate",
        "      toggle:",
        "        icon: material/weather-sunny",
        "        name: Thème clair",
        "markdown_extensions:",
        "  - admonition",
        "  - md_in_html",
        "  - tables",
        "  - toc:",
        "      permalink: true",
        "      slugify: !!python/object/apply:pymdownx.slugs.slugify",
        "        kwds:",
        "          case: lower",
        "  - pymdownx.details",
        "  - pymdownx.superfences",
        "  - pymdownx.highlight:",
        "      anchor_linenums: true",
        "plugins:",
        "  - search",
        "nav:",
    ]
    lines.extend(yaml_lines(nav, indent=2))
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config


def yaml_lines(node, indent: int) -> list[str]:
    pad = " " * indent
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str):
                out.append(f"{pad}- {quote(key)}: {quote(value)}")
            else:
                out.append(f"{pad}- {quote(key)}:")
                out.extend(yaml_lines(value, indent + 4))
    elif isinstance(node, list):
        for item in node:
            if isinstance(item, str):
                out.append(f"{pad}- {quote(item)}")
            else:
                out.extend(yaml_lines(item, indent))
    return out


def quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main() -> int:
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)

    copy_tree(ROOT, DOCS_DIR)
    rename_readmes(DOCS_DIR)
    rewritten = rewrite_links(DOCS_DIR)

    nav = build_nav(DOCS_DIR, Path())
    config = write_config(nav)

    pages = len(list(DOCS_DIR.rglob("*.md")))
    print(f"{pages} page(s) Markdown, {rewritten} fichier(s) avec liens réécrits")
    print(f"configuration écrite : {config.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
