"""Rich rendering helpers."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

console = Console()


def greeting_panel(line1: str, line2: str) -> None:
    body = Text()
    body.append(line1 + "\n", style="bold")
    body.append(line2 + "\n")
    body.append("¿En qué te ayudo?")
    console.print(Panel(body, border_style="dim"))


def tool_line(tool_name: str, preview: str) -> None:
    console.print(f"[dim cyan][{tool_name}: {preview[:80]}][/dim cyan]")


def assistant_markdown(text: str) -> None:
    if text.strip():
        console.print(Markdown(text))


def assistant_stream(text: str) -> None:
    console.print(text, end="", markup=False)


def error_line(msg: str) -> None:
    console.print(f"[red]{msg}[/red]")


def info_line(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")


def confirm_prompt(preview: str) -> bool:
    console.print(f"\n[yellow]¿Ejecutar [bold]{preview}[/bold]?[/yellow] (y/N) ", end="")
    try:
        ans = input("").strip().lower()
        return ans in ("y", "s", "si", "sí", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def mode_line(mode: str) -> None:
    console.print(f"[dim]Modo: {mode}[/dim]")
