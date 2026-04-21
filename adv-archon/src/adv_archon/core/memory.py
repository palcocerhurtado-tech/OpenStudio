"""Memory — corto plazo (RAM) y largo plazo (SQLite + embeddings opcionales)."""

from __future__ import annotations

import datetime
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional


_DDL = """
CREATE TABLE IF NOT EXISTS memories (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    content   TEXT NOT NULL,
    tags      TEXT DEFAULT '[]',
    namespace TEXT DEFAULT 'general',
    created   TEXT NOT NULL
);
"""


class MemoryManager:
    def __init__(self, data_dir: Path, incognito: bool = False) -> None:
        self._incognito = incognito
        self._db_path = data_dir / "memory.db"
        self._short_term: list[dict] = []  # conversation turns
        if not incognito:
            self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(_DDL)

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Short-term (conversation)
    # ------------------------------------------------------------------

    def add_turn(self, role: str, content: str) -> None:
        self._short_term.append({"role": role, "content": content})

    def get_turns(self, last_n: int = 20) -> list[dict]:
        return self._short_term[-last_n:]

    def clear_turns(self) -> None:
        self._short_term.clear()

    # ------------------------------------------------------------------
    # Long-term
    # ------------------------------------------------------------------

    def remember(self, fact: str, tags: list[str] | None = None, namespace: str = "general") -> int:
        if self._incognito:
            return -1
        now = datetime.datetime.now().isoformat(timespec="seconds")
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO memories (content, tags, namespace, created) VALUES (?,?,?,?)",
                (fact, json.dumps(tags or []), namespace, now),
            )
            return cur.lastrowid  # type: ignore

    def recall(self, query: str, limit: int = 5, namespace: str = "") -> list[dict]:
        if self._incognito:
            return []
        q = f"%{query.lower()}%"
        with self._conn() as conn:
            if namespace:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE lower(content) LIKE ? AND namespace=? ORDER BY id DESC LIMIT ?",
                    (q, namespace, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE lower(content) LIKE ? ORDER BY id DESC LIMIT ?",
                    (q, limit),
                ).fetchall()
        return [dict(r) for r in rows]

    def forget(self, memory_id: int) -> bool:
        if self._incognito:
            return False
        with self._conn() as conn:
            conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        return True

    def list_recent(self, limit: int = 10) -> list[dict]:
        if self._incognito:
            return []
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def relevant_context(self, query: str, limit: int = 3) -> str:
        """Return a brief context string of relevant memories for injecting into prompts."""
        hits = self.recall(query, limit=limit)
        if not hits:
            return ""
        lines = ["Recuerdos relevantes:"]
        for h in hits:
            lines.append(f"- {h['content']}")
        return "\n".join(lines)
