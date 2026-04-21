"""Notion connector — read/write pages, databases and blocks."""

from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
from typing import Any, Optional


class NotionError(Exception):
    pass


class NotionClient:
    BASE = "https://api.notion.com/v1"
    VERSION = "2022-06-28"

    def __init__(self, token: str) -> None:
        self._token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": self.VERSION,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[dict] = None,
    ) -> Any:
        url = f"{self.BASE}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            detail = e.read().decode()
            raise NotionError(f"Notion API {e.code}: {detail}") from e

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search across all pages and databases the integration can access."""
        result = self._request("POST", "/search", {"query": query, "page_size": limit})
        return [self._summarise_object(obj) for obj in result.get("results", [])]

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def get_page(self, page_id: str) -> dict:
        page = self._request("GET", f"/pages/{_clean_id(page_id)}")
        return self._summarise_object(page)

    def get_page_content(self, page_id: str, max_blocks: int = 100) -> str:
        """Return plain-text content of a page."""
        blocks = self._request(
            "GET",
            f"/blocks/{_clean_id(page_id)}/children?page_size={max_blocks}",
        )
        lines: list[str] = []
        for block in blocks.get("results", []):
            text = _extract_rich_text(block)
            if text:
                lines.append(text)
        return "\n".join(lines)

    def create_page(
        self,
        title: str,
        content: str,
        parent_page_id: Optional[str] = None,
        database_id: Optional[str] = None,
    ) -> dict:
        """Create a new page. Needs either parent_page_id or database_id."""
        if parent_page_id:
            parent = {"type": "page_id", "page_id": _clean_id(parent_page_id)}
        elif database_id:
            parent = {"type": "database_id", "database_id": _clean_id(database_id)}
        else:
            raise NotionError("Must supply parent_page_id or database_id")

        body: dict[str, Any] = {
            "parent": parent,
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": title}}]
                }
            },
            "children": _markdown_to_blocks(content),
        }
        result = self._request("POST", "/pages", body)
        return {"id": result["id"], "url": result.get("url", "")}

    def update_page_content(self, page_id: str, content: str) -> None:
        """Append blocks to an existing page."""
        blocks = _markdown_to_blocks(content)
        self._request(
            "PATCH",
            f"/blocks/{_clean_id(page_id)}/children",
            {"children": blocks},
        )

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    def list_databases(self) -> list[dict]:
        result = self._request("POST", "/search", {"filter": {"property": "object", "value": "database"}})
        return [
            {
                "id": db["id"],
                "title": _db_title(db),
                "url": db.get("url", ""),
            }
            for db in result.get("results", [])
        ]

    def query_database(self, database_id: str, limit: int = 20) -> list[dict]:
        result = self._request(
            "POST",
            f"/databases/{_clean_id(database_id)}/query",
            {"page_size": limit},
        )
        return [self._summarise_object(obj) for obj in result.get("results", [])]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _summarise_object(self, obj: dict) -> dict:
        otype = obj.get("object")
        if otype == "page":
            props = obj.get("properties", {})
            title = ""
            for key in ("Name", "title", "Title"):
                if key in props:
                    title = _extract_title_prop(props[key])
                    break
            return {
                "type": "page",
                "id": obj["id"],
                "title": title,
                "url": obj.get("url", ""),
                "last_edited": obj.get("last_edited_time", ""),
            }
        if otype == "database":
            return {
                "type": "database",
                "id": obj["id"],
                "title": _db_title(obj),
                "url": obj.get("url", ""),
            }
        return {"type": otype, "id": obj.get("id", "")}


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def _get_client() -> NotionClient:
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        raise NotionError(
            "NOTION_TOKEN no está configurado. "
            "Añade NOTION_TOKEN=<tu_token> a ~/.adv-archon/.env"
        )
    return NotionClient(token)


def search_notion(query: str, limit: int = 10) -> list[dict]:
    """Search Notion pages and databases matching *query*."""
    return _get_client().search(query, limit)


def read_notion_page(page_id: str) -> str:
    """Return plain-text content of a Notion page."""
    client = _get_client()
    meta = client.get_page(page_id)
    content = client.get_page_content(page_id)
    return f"# {meta.get('title', page_id)}\n\n{content}"


def create_notion_page(
    title: str,
    content: str,
    parent_page_id: str = "",
    database_id: str = "",
) -> dict:
    """Create a Notion page under *parent_page_id* or inside *database_id*."""
    return _get_client().create_page(
        title,
        content,
        parent_page_id=parent_page_id or None,
        database_id=database_id or None,
    )


def list_notion_databases() -> list[dict]:
    """List all Notion databases the integration can access."""
    return _get_client().list_databases()


def query_notion_database(database_id: str, limit: int = 20) -> list[dict]:
    """Return rows from a Notion database."""
    return _get_client().query_database(database_id, limit)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean_id(uid: str) -> str:
    return uid.replace("-", "")


def _extract_title_prop(prop: dict) -> str:
    items = prop.get("title", [])
    return "".join(i.get("plain_text", "") for i in items)


def _db_title(db: dict) -> str:
    title_list = db.get("title", [])
    return "".join(t.get("plain_text", "") for t in title_list)


def _extract_rich_text(block: dict) -> str:
    btype = block.get("type", "")
    data = block.get(btype, {})
    texts = data.get("rich_text", [])
    prefix = ""
    if btype == "heading_1":
        prefix = "# "
    elif btype == "heading_2":
        prefix = "## "
    elif btype == "heading_3":
        prefix = "### "
    elif btype == "bulleted_list_item":
        prefix = "- "
    elif btype == "numbered_list_item":
        prefix = "1. "
    elif btype == "to_do":
        checked = data.get("checked", False)
        prefix = "[x] " if checked else "[ ] "
    elif btype == "code":
        lang = data.get("language", "")
        text = "".join(t.get("plain_text", "") for t in texts)
        return f"```{lang}\n{text}\n```"
    plain = "".join(t.get("plain_text", "") for t in texts)
    return f"{prefix}{plain}" if plain else ""


def _markdown_to_blocks(text: str) -> list[dict]:
    """Convert simple markdown text to Notion block objects."""
    blocks: list[dict] = []
    for line in text.splitlines():
        if line.startswith("# "):
            blocks.append(_heading_block(line[2:], 1))
        elif line.startswith("## "):
            blocks.append(_heading_block(line[3:], 2))
        elif line.startswith("### "):
            blocks.append(_heading_block(line[4:], 3))
        elif line.startswith("- ") or line.startswith("* "):
            blocks.append(_bullet_block(line[2:]))
        elif line.startswith("[ ] "):
            blocks.append(_todo_block(line[4:], False))
        elif line.startswith("[x] "):
            blocks.append(_todo_block(line[4:], True))
        else:
            if line.strip():
                blocks.append(_paragraph_block(line))
    return blocks


def _rt(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _heading_block(text: str, level: int) -> dict:
    key = f"heading_{level}"
    return {"object": "block", "type": key, key: {"rich_text": _rt(text)}}


def _paragraph_block(text: str) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": _rt(text)}}


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rt(text)},
    }


def _todo_block(text: str, checked: bool) -> dict:
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {"rich_text": _rt(text), "checked": checked},
    }


TOOL_DEFINITIONS = [
    {
        "name": "search_notion",
        "description": "Busca en Notion páginas y bases de datos.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        "function": search_notion,
    },
    {
        "name": "read_notion_page",
        "description": "Lee el contenido de una página de Notion.",
        "parameters": {
            "type": "object",
            "properties": {"page_id": {"type": "string"}},
            "required": ["page_id"],
        },
        "function": read_notion_page,
    },
    {
        "name": "create_notion_page",
        "description": "Crea una nueva página en Notion.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "parent_page_id": {"type": "string", "default": ""},
                "database_id": {"type": "string", "default": ""},
            },
            "required": ["title", "content"],
        },
        "function": create_notion_page,
    },
    {
        "name": "list_notion_databases",
        "description": "Lista las bases de datos de Notion accesibles.",
        "parameters": {"type": "object", "properties": {}},
        "function": list_notion_databases,
    },
    {
        "name": "query_notion_database",
        "description": "Devuelve filas de una base de datos de Notion.",
        "parameters": {
            "type": "object",
            "properties": {
                "database_id": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["database_id"],
        },
        "function": query_notion_database,
    },
]
