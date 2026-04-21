"""Configuration — carga ~/.adv-archon/config.toml y ~/.adv-archon/.env."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "mode": "local",
    "ollama_model": "llama3.1:8b",
    "ollama_host": "http://localhost:11434",
    "gemini_model": "gemini-2.0-flash",
    "max_tool_rounds": 8,
    "context_window_turns": 20,
    "shell_auto": False,
    "budget_cap_usd": 5.0,
    "budget_approval_threshold_usd": 0.50,
    "pii_redaction": False,
    "profile": "default",
    "obsidian_vault_path": "",
    "watch_repos": [],
    "auto_brief_hour": 8,
    "auto_brief_minute": 30,
    "shell_whitelist": [
        "ls", "pwd", "cat", "head", "tail", "wc", "file", "stat", "which", "type",
        "git status", "git log", "git diff", "git branch", "git show", "git remote",
        "grep", "rg", "find", "tree", "echo", "date", "uname", "whoami", "hostname",
        "python --version", "node --version", "uv --version", "pip --version",
        "brew list", "brew info",
    ],
}


class Config:
    def __init__(self, data_dir: Path | None = None) -> None:
        if data_dir is None:
            data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
        self.data_dir = data_dir
        data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Apply defaults
        for k, v in _DEFAULTS.items():
            setattr(self, k, v)

        # Load .env
        self._load_env(data_dir / ".env")

        # Load config.toml
        self._load_toml(data_dir / "config.toml")

        # Env overrides (higher priority)
        self._apply_env_overrides()

    # ------------------------------------------------------------------

    def _load_env(self, env_path: Path) -> None:
        if not env_path.exists():
            return
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

    def _load_toml(self, toml_path: Path) -> None:
        if not toml_path.exists():
            return
        try:
            if sys.version_info >= (3, 11):
                import tomllib
                data = tomllib.loads(toml_path.read_text())
            else:
                import tomli  # type: ignore
                data = tomli.loads(toml_path.read_text())
        except Exception:
            return
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def _apply_env_overrides(self) -> None:
        m = os.environ.get("ADV_ARCHON_DEFAULT_MODE", "")
        if m:
            self.mode = m
        om = os.environ.get("ADV_ARCHON_DEFAULT_OLLAMA_MODEL", "")
        if om:
            self.ollama_model = om
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        self.notion_token = os.environ.get("NOTION_TOKEN", "")
        self.obsidian_vault_path = os.environ.get(
            "OBSIDIAN_VAULT_PATH", self.obsidian_vault_path
        )
        self.gmail_address = os.environ.get("GMAIL_ADDRESS", "")
        self.gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    # ------------------------------------------------------------------

    def save_toml(self) -> None:
        """Persist current config to config.toml (non-secret values only)."""
        lines = [
            f'mode = "{self.mode}"',
            f'ollama_model = "{self.ollama_model}"',
            f'ollama_host = "{self.ollama_host}"',
            f'profile = "{self.profile}"',
            f'pii_redaction = {str(self.pii_redaction).lower()}',
            f'budget_cap_usd = {self.budget_cap_usd}',
        ]
        (self.data_dir / "config.toml").write_text("\n".join(lines) + "\n")
