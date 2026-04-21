"""Web tools — web_search (DuckDuckGo) y web_fetch (trafilatura)."""

from __future__ import annotations


def web_search(query: str, n: int = 5) -> list[dict]:
    """Busca en DuckDuckGo. Devuelve lista de {title, url, snippet}."""
    try:
        from duckduckgo_search import DDGS  # type: ignore
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=n))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in results
        ]
    except ImportError:
        return [{"error": "duckduckgo-search no instalado. Ejecuta: uv pip install duckduckgo-search"}]
    except Exception as e:
        return [{"error": str(e)}]


def web_fetch(url: str, max_chars: int = 8000) -> str:
    """Descarga una URL y extrae el texto limpio."""
    try:
        import trafilatura  # type: ignore
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=False, include_images=False)
            if text:
                return text[:max_chars]
    except ImportError:
        pass

    # Fallback: requests + basic strip
    try:
        import requests  # type: ignore
        resp = requests.get(url, timeout=10, headers={"User-Agent": "ADV-ARCHON/1.0"})
        resp.raise_for_status()
        # Strip HTML tags naively
        import re
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"Error al obtener {url}: {e}"


# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": "Busca en internet usando DuckDuckGo. Devuelve títulos, URLs y snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "n": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        "function": web_search,
    },
    {
        "name": "web_fetch",
        "description": "Descarga una URL y extrae su contenido como texto limpio.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer", "default": 8000},
            },
            "required": ["url"],
        },
        "function": web_fetch,
    },
]
