"""Shell execution — whitelist de solo lectura + blacklist absoluta + modo AUTO."""

from __future__ import annotations

import re
import shlex
import subprocess
from typing import Optional


# Comandos que se ejecutan sin confirmación
_WHITELIST_PREFIXES = [
    "ls", "pwd", "cat", "head", "tail", "wc", "file", "stat", "which", "type",
    "git status", "git log", "git diff", "git branch", "git show", "git remote",
    "git stash list", "git tag",
    "grep", "rg", "find", "tree", "echo", "date", "uname", "whoami", "hostname",
    "python --version", "python3 --version", "node --version", "uv --version",
    "pip --version", "pip3 --version", "brew list", "brew info", "brew --version",
    "df -h", "du -sh", "ps aux", "top -l 1", "uptime",
    "env", "printenv", "open --version",
]

# Siempre requieren confirmación, incluso en modo AUTO
_BLACKLIST_PATTERNS = [
    r"\brm\b", r"\brmdir\b", r"\bmv\b.*\s",
    r"\bdd\b", r"\bmkfs\b",
    r"\bsudo\b", r"\bchmod\s+-R\b", r"\bchown\s+-R\b",
    r"git\s+push\s+--force", r"git\s+reset\s+--hard", r"git\s+clean\b",
    r"git\s+push\b(?!.*--dry-run)",
    r"curl\b.+\|\s*(bash|sh|zsh)",
    r"wget\b.+\|\s*(bash|sh|zsh)",
    r"/dev/",
    r"/etc/", r"/System/", r"/Library/", r"/usr/",
    r">\s*/",  # redirect to system path
    r":\(\)\{.*\}", r"fork\s+bomb",
]


def _is_whitelisted(cmd: str) -> bool:
    cmd_lower = cmd.strip().lower()
    for prefix in _WHITELIST_PREFIXES:
        if cmd_lower == prefix or cmd_lower.startswith(prefix + " "):
            return True
    return False


def _is_blacklisted(cmd: str) -> bool:
    for pattern in _BLACKLIST_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False


def shell_exec(
    cmd: str,
    cwd: str = "",
    timeout: int = 30,
    auto: bool = False,
) -> str:
    """Ejecuta un comando shell con política de confirmación."""
    blacklisted = _is_blacklisted(cmd)
    whitelisted = _is_whitelisted(cmd)

    if blacklisted:
        # Always confirm blacklisted commands, even in auto mode
        from adv_archon.ui.render import confirm_prompt
        if not confirm_prompt(f"⚠ COMANDO POTENCIALMENTE DESTRUCTIVO:\n  {cmd}"):
            return "Ejecución cancelada por el usuario."

    elif not whitelisted and not auto:
        # Non-whitelisted in normal mode: ask
        from adv_archon.ui.render import confirm_prompt
        if not confirm_prompt(cmd):
            return "Ejecución cancelada por el usuario."

    # Execute
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or None,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return output.strip() or "(sin salida)"
    except subprocess.TimeoutExpired:
        return f"Timeout tras {timeout}s."
    except Exception as e:
        return f"Error: {e}"


def python_exec(code: str) -> str:
    """Ejecuta un snippet Python en subproceso efímero. Siempre pide confirmación."""
    from adv_archon.ui.render import confirm_prompt
    preview = code[:120].replace("\n", "↵")
    if not confirm_prompt(f"python_exec: {preview}"):
        return "Ejecución cancelada."
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True, text=True, timeout=30,
        )
        out = result.stdout + result.stderr
        return out.strip() or "(sin salida)"
    except subprocess.TimeoutExpired:
        return "Timeout tras 30s."
    except Exception as e:
        return f"Error: {e}"


def clipboard_read() -> str:
    """Lee el portapapeles (macOS)."""
    try:
        result = subprocess.run(["pbpaste"], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"


def clipboard_write(text: str) -> str:
    """Escribe texto en el portapapeles (macOS)."""
    try:
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return "Copiado al portapapeles."
    except Exception as e:
        return f"Error: {e}"


def open_app(path_or_url: str) -> str:
    """Abre una aplicación o URL con el comando 'open' de macOS."""
    try:
        subprocess.Popen(["open", path_or_url])
        return f"Abierto: {path_or_url}"
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "shell_exec",
        "description": (
            "Ejecuta un comando shell en el Mac del usuario. "
            "Los comandos de solo lectura (ls, git status, etc.) se ejecutan sin confirmación. "
            "El resto requiere autorización explícita del usuario."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "Comando shell a ejecutar"},
                "cwd": {"type": "string", "default": "", "description": "Directorio de trabajo"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["cmd"],
        },
        "function": lambda cmd, cwd="", timeout=30, auto=False: shell_exec(cmd, cwd, timeout, auto),
    },
    {
        "name": "python_exec",
        "description": "Ejecuta un snippet Python en subproceso. Siempre pide confirmación.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string"}},
            "required": ["code"],
        },
        "function": python_exec,
        "requires_confirmation": True,
    },
    {
        "name": "clipboard_read",
        "description": "Lee el contenido del portapapeles del Mac.",
        "parameters": {"type": "object", "properties": {}},
        "function": clipboard_read,
    },
    {
        "name": "clipboard_write",
        "description": "Escribe texto en el portapapeles del Mac.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        "function": clipboard_write,
    },
    {
        "name": "open_app",
        "description": "Abre una aplicación, archivo o URL en macOS.",
        "parameters": {
            "type": "object",
            "properties": {"path_or_url": {"type": "string"}},
            "required": ["path_or_url"],
        },
        "function": open_app,
    },
]
