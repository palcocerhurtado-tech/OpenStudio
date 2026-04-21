"""Obsidian connector — read and write a local Obsidian vault (plain markdown)."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ObsidianError(Exception):
    pass


def _vault_path() -> Path:
    env = os.environ.get("OBSIDIAN_VAULT_PATH", "")
    if env:
        p = Path(env).expanduser()
        if p.is_dir():
            return p
    # common default locations
    for candidate in [
        Path.home() / "Obsidian",
        Path.home() / "Documents" / "Obsidian",
        Path.home() / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents",
    ]:
        if candidate.is_dir():
            return candidate
    raise ObsidianError(
        "No se encontró el vault de Obsidian. "
        "Añade OBSIDIAN_VAULT_PATH=<ruta> a ~/.adv-archon/.env"
    )


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Note:
    path: Path
    title: str
    tags: list[str]
    content: str
    modified: float

    def rel_path(self, vault: Path) -> str:
        return str(self.path.relative_to(vault))

    def summary(self, vault: Path) -> dict:
        return {
            "title": self.title,
            "path": self.rel_path(vault),
            "tags": self.tags,
            "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(self.modified)),
            "preview": self.content[:200].replace("\n", " "),
        }


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _parse_note(path: Path) -> Note:
    text = path.read_text(errors="replace")
    # extract frontmatter tags
    tags: list[str] = []
    frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        tag_match = re.search(r"tags:\s*\[([^\]]*)\]", fm)
        if not tag_match:
            tag_match = re.search(r"tags:\n((?:\s*- .+\n)+)", fm)
            if tag_match:
                tags = [t.strip().lstrip("- ") for t in tag_match.group(1).splitlines() if t.strip()]
        else:
            tags = [t.strip().strip("\"'") for t in tag_match.group(1).split(",")]
    # title: first H1 or filename stem
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    return Note(
        path=path,
        title=title,
        tags=tags,
        content=text,
        modified=path.stat().st_mtime,
    )


def _iter_notes(vault: Path):
    for p in sorted(vault.rglob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        # skip hidden dirs like .obsidian
        if any(part.startswith(".") for part in p.parts):
            continue
        yield p


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def search_obsidian(query: str, limit: int = 10) -> list[dict]:
    """Full-text search across the Obsidian vault. Returns note summaries."""
    vault = _vault_path()
    q = query.lower()
    results: list[tuple[int, Note]] = []
    for p in _iter_notes(vault):
        try:
            note = _parse_note(p)
        except Exception:
            continue
        score = 0
        if q in note.title.lower():
            score += 10
        score += note.content.lower().count(q)
        if score > 0:
            results.append((score, note))
        if len(results) >= limit * 3:
            break
    results.sort(key=lambda x: x[0], reverse=True)
    return [n.summary(vault) for _, n in results[:limit]]


def read_obsidian_note(path: str) -> str:
    """Read the full content of a note by its vault-relative path."""
    vault = _vault_path()
    full = vault / path
    if not full.exists():
        raise ObsidianError(f"Nota no encontrada: {path}")
    return full.read_text(errors="replace")


def list_recent_obsidian_notes(limit: int = 10) -> list[dict]:
    """Return the most recently modified notes in the vault."""
    vault = _vault_path()
    notes: list[Note] = []
    for p in _iter_notes(vault):
        try:
            notes.append(_parse_note(p))
        except Exception:
            continue
        if len(notes) >= limit:
            break
    return [n.summary(vault) for n in notes]


def create_obsidian_note(
    title: str,
    content: str,
    folder: str = "",
    tags: Optional[list[str]] = None,
) -> dict:
    """Create a new note in the vault."""
    vault = _vault_path()
    tag_list = tags or []
    frontmatter = "---\n"
    if tag_list:
        frontmatter += "tags: [" + ", ".join(tag_list) + "]\n"
    frontmatter += "---\n\n"
    body = f"# {title}\n\n{content}"
    text = frontmatter + body

    target_dir = vault / folder if folder else vault
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", title) + ".md"
    dest = target_dir / safe_name
    dest.write_text(text)
    return {"path": str(dest.relative_to(vault)), "title": title}


def search_obsidian_by_tag(tag: str, limit: int = 20) -> list[dict]:
    """Return notes that have *tag* in their frontmatter."""
    vault = _vault_path()
    results: list[Note] = []
    tag_lower = tag.lower()
    for p in _iter_notes(vault):
        try:
            note = _parse_note(p)
        except Exception:
            continue
        if any(t.lower() == tag_lower for t in note.tags):
            results.append(note)
        if len(results) >= limit:
            break
    return [n.summary(vault) for n in results]


def get_obsidian_backlinks(path: str) -> list[dict]:
    """Return notes that link to the note at *path*."""
    vault = _vault_path()
    stem = Path(path).stem
    pattern = re.compile(r"\[\[" + re.escape(stem) + r"(\|[^\]]+)?\]\]", re.IGNORECASE)
    results: list[dict] = []
    for p in _iter_notes(vault):
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        if pattern.search(text):
            results.append({"path": str(p.relative_to(vault)), "title": p.stem})
    return results


# ---------------------------------------------------------------------------
# Tool definitions for agent dispatcher
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "search_obsidian",
        "description": "Busca notas en el vault de Obsidian por contenido.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        "function": search_obsidian,
    },
    {
        "name": "read_obsidian_note",
        "description": "Lee el contenido completo de una nota de Obsidian.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "function": read_obsidian_note,
    },
    {
        "name": "list_recent_obsidian_notes",
        "description": "Lista las notas de Obsidian modificadas más recientemente.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
        },
        "function": list_recent_obsidian_notes,
    },
    {
        "name": "create_obsidian_note",
        "description": "Crea una nueva nota en el vault de Obsidian.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "folder": {"type": "string", "default": ""},
                "tags": {"type": "array", "items": {"type": "string"}, "default": []},
            },
            "required": ["title", "content"],
        },
        "function": create_obsidian_note,
    },
    {
        "name": "search_obsidian_by_tag",
        "description": "Devuelve notas de Obsidian con una etiqueta concreta.",
        "parameters": {
            "type": "object",
            "properties": {
                "tag": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["tag"],
        },
        "function": search_obsidian_by_tag,
    },
    {
        "name": "get_obsidian_backlinks",
        "description": "Devuelve las notas que enlazan a una nota concreta.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        "function": get_obsidian_backlinks,
    },
]
