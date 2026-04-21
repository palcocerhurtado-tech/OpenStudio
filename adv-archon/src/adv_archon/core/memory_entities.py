"""Structured memory entities — people, projects, preferences, decisions.

Drop-in extension for the existing memory.py.  Stores records in the same
SQLite database under separate tables, so it doesn't break anything already there.
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Generator, Optional


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS persons (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    company     TEXT DEFAULT '',
    role        TEXT DEFAULT '',
    email       TEXT DEFAULT '',
    phone       TEXT DEFAULT '',
    tags        TEXT DEFAULT '[]',
    notes       TEXT DEFAULT '',
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    status      TEXT DEFAULT 'active',
    tech_stack  TEXT DEFAULT '[]',
    team        TEXT DEFAULT '[]',
    deadline    TEXT DEFAULT '',
    repo_path   TEXT DEFAULT '',
    notes       TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS preferences (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    UNIQUE(category, key)
);

CREATE TABLE IF NOT EXISTS decisions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    context     TEXT DEFAULT '',
    decision    TEXT NOT NULL,
    rationale   TEXT DEFAULT '',
    project     TEXT DEFAULT '',
    made_at     TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Person:
    name: str
    company: str = ""
    role: str = ""
    email: str = ""
    phone: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    id: Optional[int] = None
    first_seen: str = ""
    last_seen: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tags"] = json.dumps(d["tags"])
        return d


@dataclass
class Project:
    name: str
    status: str = "active"
    tech_stack: list[str] = field(default_factory=list)
    team: list[str] = field(default_factory=list)
    deadline: str = ""
    repo_path: str = ""
    notes: str = ""
    id: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tech_stack"] = json.dumps(d["tech_stack"])
        d["team"] = json.dumps(d["team"])
        return d


@dataclass
class Preference:
    category: str
    key: str
    value: str
    id: Optional[int] = None
    updated_at: str = ""


@dataclass
class Decision:
    title: str
    decision: str
    context: str = ""
    rationale: str = ""
    project: str = ""
    id: Optional[int] = None
    made_at: str = ""


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

class EntityStore:
    def __init__(self, db_path: Path) -> None:
        self._db = db_path
        self._init()

    def _init(self) -> None:
        with self._conn() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _now(self) -> str:
        return datetime.datetime.now().isoformat(timespec="seconds")

    # ------------------------------------------------------------------
    # Persons
    # ------------------------------------------------------------------

    def upsert_person(self, p: Person) -> int:
        now = self._now()
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM persons WHERE lower(name)=lower(?)", (p.name,)
            ).fetchone()
            if existing:
                pid = existing["id"]
                conn.execute(
                    """UPDATE persons SET company=?, role=?, email=?, phone=?,
                       tags=?, notes=?, last_seen=? WHERE id=?""",
                    (
                        p.company, p.role, p.email, p.phone,
                        json.dumps(p.tags), p.notes, now, pid,
                    ),
                )
                return pid
            cur = conn.execute(
                """INSERT INTO persons (name,company,role,email,phone,tags,notes,first_seen,last_seen)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (p.name, p.company, p.role, p.email, p.phone, json.dumps(p.tags), p.notes, now, now),
            )
            return cur.lastrowid  # type: ignore

    def search_persons(self, query: str) -> list[dict]:
        q = f"%{query.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM persons
                   WHERE lower(name) LIKE ? OR lower(company) LIKE ?
                      OR lower(email) LIKE ? OR lower(notes) LIKE ?
                   ORDER BY last_seen DESC LIMIT 20""",
                (q, q, q, q),
            ).fetchall()
        return [self._person_row(r) for r in rows]

    def get_person(self, name_or_id: str) -> Optional[dict]:
        with self._conn() as conn:
            if name_or_id.isdigit():
                row = conn.execute("SELECT * FROM persons WHERE id=?", (int(name_or_id),)).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM persons WHERE lower(name)=lower(?)", (name_or_id,)
                ).fetchone()
        return self._person_row(row) if row else None

    def list_persons(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM persons ORDER BY last_seen DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._person_row(r) for r in rows]

    def _person_row(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["tags"] = json.loads(d.get("tags", "[]"))
        return d

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def upsert_project(self, p: Project) -> int:
        now = self._now()
        with self._conn() as conn:
            existing = conn.execute(
                "SELECT id FROM projects WHERE lower(name)=lower(?)", (p.name,)
            ).fetchone()
            if existing:
                pid = existing["id"]
                conn.execute(
                    """UPDATE projects SET status=?, tech_stack=?, team=?,
                       deadline=?, repo_path=?, notes=?, updated_at=? WHERE id=?""",
                    (
                        p.status, json.dumps(p.tech_stack), json.dumps(p.team),
                        p.deadline, p.repo_path, p.notes, now, pid,
                    ),
                )
                return pid
            cur = conn.execute(
                """INSERT INTO projects (name,status,tech_stack,team,deadline,repo_path,notes,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    p.name, p.status, json.dumps(p.tech_stack), json.dumps(p.team),
                    p.deadline, p.repo_path, p.notes, now, now,
                ),
            )
            return cur.lastrowid  # type: ignore

    def search_projects(self, query: str) -> list[dict]:
        q = f"%{query.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM projects
                   WHERE lower(name) LIKE ? OR lower(notes) LIKE ? OR lower(status) LIKE ?
                   ORDER BY updated_at DESC LIMIT 20""",
                (q, q, q),
            ).fetchall()
        return [self._project_row(r) for r in rows]

    def get_project(self, name: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE lower(name)=lower(?)", (name,)
            ).fetchone()
        return self._project_row(row) if row else None

    def list_projects(self, status: str = "") -> list[dict]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM projects WHERE status=? ORDER BY updated_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM projects ORDER BY updated_at DESC"
                ).fetchall()
        return [self._project_row(r) for r in rows]

    def _project_row(self, row: sqlite3.Row) -> dict:
        d = dict(row)
        d["tech_stack"] = json.loads(d.get("tech_stack", "[]"))
        d["team"] = json.loads(d.get("team", "[]"))
        return d

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------

    def set_preference(self, category: str, key: str, value: str) -> None:
        now = self._now()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO preferences (category,key,value,updated_at)
                   VALUES (?,?,?,?)
                   ON CONFLICT(category,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (category, key, value, now),
            )

    def get_preference(self, category: str, key: str) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM preferences WHERE category=? AND key=?", (category, key)
            ).fetchone()
        return row["value"] if row else None

    def list_preferences(self, category: str = "") -> list[dict]:
        with self._conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM preferences WHERE category=? ORDER BY category,key", (category,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM preferences ORDER BY category,key"
                ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Decisions
    # ------------------------------------------------------------------

    def add_decision(self, d: Decision) -> int:
        now = self._now()
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO decisions (title,context,decision,rationale,project,made_at)
                   VALUES (?,?,?,?,?,?)""",
                (d.title, d.context, d.decision, d.rationale, d.project, now),
            )
            return cur.lastrowid  # type: ignore

    def search_decisions(self, query: str) -> list[dict]:
        q = f"%{query.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM decisions
                   WHERE lower(title) LIKE ? OR lower(decision) LIKE ? OR lower(context) LIKE ?
                   ORDER BY made_at DESC LIMIT 20""",
                (q, q, q),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_decisions(self, project: str = "", limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            if project:
                rows = conn.execute(
                    "SELECT * FROM decisions WHERE lower(project)=lower(?) ORDER BY made_at DESC LIMIT ?",
                    (project, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM decisions ORDER BY made_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Singleton access
# ---------------------------------------------------------------------------

_store: Optional[EntityStore] = None


def get_entity_store(data_dir: Optional[Path] = None) -> EntityStore:
    global _store
    if _store is None:
        if data_dir is None:
            import os
            data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
        data_dir.mkdir(parents=True, exist_ok=True)
        _store = EntityStore(data_dir / "memory.db")
    return _store


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------

def remember_person(
    name: str,
    company: str = "",
    role: str = "",
    email: str = "",
    phone: str = "",
    notes: str = "",
    tags: str = "",
) -> dict:
    """Guarda o actualiza información de una persona en la memoria."""
    store = get_entity_store()
    p = Person(
        name=name, company=company, role=role,
        email=email, phone=phone, notes=notes,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    pid = store.upsert_person(p)
    return {"status": "guardado", "id": pid, "name": name}


def recall_person(query: str) -> list[dict]:
    """Busca personas en la memoria por nombre, empresa o notas."""
    return get_entity_store().search_persons(query)


def remember_project(
    name: str,
    status: str = "active",
    tech_stack: str = "",
    team: str = "",
    deadline: str = "",
    repo_path: str = "",
    notes: str = "",
) -> dict:
    """Guarda o actualiza información de un proyecto en la memoria."""
    store = get_entity_store()
    p = Project(
        name=name,
        status=status,
        tech_stack=[t.strip() for t in tech_stack.split(",") if t.strip()],
        team=[t.strip() for t in team.split(",") if t.strip()],
        deadline=deadline,
        repo_path=repo_path,
        notes=notes,
    )
    pid = store.upsert_project(p)
    return {"status": "guardado", "id": pid, "name": name}


def recall_project(query: str) -> list[dict]:
    """Busca proyectos en la memoria."""
    return get_entity_store().search_projects(query)


def set_preference(category: str, key: str, value: str) -> dict:
    """Guarda una preferencia personal (ej. category='trabajo', key='horario', value='9-18')."""
    get_entity_store().set_preference(category, key, value)
    return {"status": "guardado", "category": category, "key": key, "value": value}


def list_preferences(category: str = "") -> list[dict]:
    """Lista las preferencias personales guardadas."""
    return get_entity_store().list_preferences(category)


def log_decision(
    title: str,
    decision: str,
    context: str = "",
    rationale: str = "",
    project: str = "",
) -> dict:
    """Registra una decisión importante en la memoria."""
    store = get_entity_store()
    d = Decision(title=title, decision=decision, context=context, rationale=rationale, project=project)
    did = store.add_decision(d)
    return {"status": "guardado", "id": did, "title": title}


def recall_decisions(query: str = "", project: str = "") -> list[dict]:
    """Busca decisiones registradas en la memoria."""
    store = get_entity_store()
    if query:
        return store.search_decisions(query)
    return store.list_decisions(project=project)


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "remember_person",
        "description": "Guarda o actualiza información de una persona (nombre, empresa, rol, email, notas).",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "company": {"type": "string", "default": ""},
                "role": {"type": "string", "default": ""},
                "email": {"type": "string", "default": ""},
                "phone": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
                "tags": {"type": "string", "default": ""},
            },
            "required": ["name"],
        },
        "function": remember_person,
    },
    {
        "name": "recall_person",
        "description": "Busca personas en la memoria por nombre, empresa o notas.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "function": recall_person,
    },
    {
        "name": "remember_project",
        "description": "Guarda o actualiza información de un proyecto activo.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "status": {"type": "string", "default": "active"},
                "tech_stack": {"type": "string", "description": "Tecnologías separadas por coma", "default": ""},
                "team": {"type": "string", "description": "Miembros del equipo separados por coma", "default": ""},
                "deadline": {"type": "string", "default": ""},
                "repo_path": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
            },
            "required": ["name"],
        },
        "function": remember_project,
    },
    {
        "name": "recall_project",
        "description": "Busca proyectos en la memoria.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "function": recall_project,
    },
    {
        "name": "set_preference",
        "description": "Guarda una preferencia personal.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "key": {"type": "string"},
                "value": {"type": "string"},
            },
            "required": ["category", "key", "value"],
        },
        "function": set_preference,
    },
    {
        "name": "list_preferences",
        "description": "Lista preferencias personales guardadas, opcionalmente filtradas por categoría.",
        "parameters": {
            "type": "object",
            "properties": {"category": {"type": "string", "default": ""}},
        },
        "function": list_preferences,
    },
    {
        "name": "log_decision",
        "description": "Registra una decisión importante con contexto y justificación.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "decision": {"type": "string"},
                "context": {"type": "string", "default": ""},
                "rationale": {"type": "string", "default": ""},
                "project": {"type": "string", "default": ""},
            },
            "required": ["title", "decision"],
        },
        "function": log_decision,
    },
    {
        "name": "recall_decisions",
        "description": "Busca decisiones registradas en la memoria.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "default": ""},
                "project": {"type": "string", "default": ""},
            },
        },
        "function": recall_decisions,
    },
]
