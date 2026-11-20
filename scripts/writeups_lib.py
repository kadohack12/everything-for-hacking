"""Utilitaires partagés : découverte des writeups et lecture du frontmatter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WRITEUPS_DIRNAME = "writeups"

# Dossiers jamais parcourus (.github reste scanné : il contient du Markdown).
IGNORED_DIR_NAMES = {
    ".git",
    ".openhands",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
}


def is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIR_NAMES or (name.startswith(".") and name != ".github")


def iter_markdown_files(root: Path = ROOT):
    """Tous les fichiers Markdown du dépôt, hors dossiers techniques."""
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(is_ignored_dir(part) for part in rel.parts[:-1]):
            continue
        yield path


def _parse_scalar(raw: str):
    value = raw.strip()
    if not value:
        return ""
    if value[0] in "\"'":
        quote = value[0]
        end = value.find(quote, 1)
        return value[1:end] if end != -1 else value[1:]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [item.strip().strip("\"'") for item in inner.split(",")] if inner else []
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    return value


def parse_frontmatter(text: str) -> dict:
    """Lit un frontmatter YAML minimal (scalaires et listes en ligne).

    Volontairement sans dépendance : le dépôt n'a pas de requirements.
    """
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    if not text.startswith("---"):
        return {}
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}
    meta: dict = {}
    for line in lines[1:]:
        if line.strip() in ("---", "..."):
            return meta
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, raw = stripped.partition(":")
        meta[key.strip().lower()] = _parse_scalar(raw)
    return {}


@dataclass
class Writeup:
    platform: str
    path: Path
    directory: Path
    parts: tuple[str, ...]
    meta: dict = field(default_factory=dict)

    @property
    def kind(self) -> str:
        """`Machines`, `Rooms`, `Challenges`…"""
        return self.parts[0] if len(self.parts) > 1 else ""

    @property
    def group(self) -> str:
        """Sous-dossier de catégorie (`crypto`, `web`…), si présent."""
        return self.parts[-2] if len(self.parts) > 2 else ""

    @property
    def name(self) -> str:
        return self.directory.name

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.name)

    @property
    def status(self) -> str:
        return str(self.meta.get("status") or "").strip().lower()

    @property
    def is_published(self) -> bool:
        return self.status == "published"

    @property
    def category(self) -> str:
        return str(self.meta.get("category") or self.group or self.kind or "")

    def field(self, key: str, default: str = "—") -> str:
        value = self.meta.get(key)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        value = str(value).strip() if value is not None else ""
        return value or default


def iter_writeups(root: Path = ROOT):
    """Tous les writeups : `writeups/<plateforme>/<kind>/<nom>/README.md`."""
    base = root / WRITEUPS_DIRNAME
    if not base.is_dir():
        return
    for platform_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if platform_dir.name.startswith(("_", ".")):
            continue
        for readme in sorted(platform_dir.rglob("README.md")):
            rel = readme.relative_to(platform_dir)
            if len(rel.parts) < 2:
                continue
            if any(is_ignored_dir(part) for part in rel.parts[:-1]):
                continue
            text = readme.read_text(encoding="utf-8", errors="replace")
            yield Writeup(
                platform=platform_dir.name,
                path=readme,
                directory=readme.parent,
                parts=tuple(rel.parts[:-1]),
                meta=parse_frontmatter(text),
            )


def iter_platform_dirs(root: Path = ROOT):
    base = root / WRITEUPS_DIRNAME
    if not base.is_dir():
        return
    for path in sorted(base.iterdir()):
        if path.is_dir() and not path.name.startswith(("_", ".")):
            yield path
