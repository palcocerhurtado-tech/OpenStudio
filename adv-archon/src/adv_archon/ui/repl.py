"""REPL interactivo — prompt_toolkit + rich + streaming."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown

from adv_archon.core.config import Config
from adv_archon.core.agent import Agent
from adv_archon.core.context import EnvContext
from adv_archon.ui.render import greeting_panel, assistant_markdown, error_line, info_line, tool_line

console = Console()

_STYLE = Style.from_dict({
    "prompt": "bold cyan",
})


class Repl:
    def __init__(
        self,
        cfg: Config,
        data_dir: Path,
        auto: bool = False,
        incognito: bool = False,
    ) -> None:
        self._cfg = cfg
        self._data_dir = data_dir
        self._auto = auto
        self._incognito = incognito

        history_path = None if incognito else data_dir / "history.txt"

        self._session: PromptSession = PromptSession(
            history=FileHistory(str(history_path)) if history_path else None,
            auto_suggest=AutoSuggestFromHistory(),
            style=_STYLE,
            mouse_support=False,
        )

        # Profile
        profile_overlay = ""
        try:
            from adv_archon.core.profiles import ProfileManager
            pm = ProfileManager(data_dir)
            pm.load()
            profile_overlay = pm.system_overlay()
            cfg.profile = pm.active.name
        except Exception:
            pass

        self._agent = Agent(
            cfg,
            data_dir,
            auto=auto,
            incognito=incognito,
            confirm_callback=self._confirm,
            stream_callback=self._on_stream,
            profile_overlay=profile_overlay,
        )
        self._streaming_buf: list[str] = []

    # ------------------------------------------------------------------

    def run(self) -> None:
        self._print_greeting()

        while True:
            try:
                user_input = self._session.prompt("> ", style=_STYLE)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[dim]Hasta luego.[/dim]")
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            # Slash commands
            if user_input.startswith("/"):
                result = self._handle_slash(user_input)
                if result == "__exit__":
                    console.print("[dim]Hasta luego.[/dim]")
                    break
                if result == "__clear__":
                    os.system("clear")
                    continue
                if result is not None:
                    console.print(Markdown(result))
                continue

            # Normal chat
            self._streaming_buf = []
            console.print()
            try:
                self._agent.chat(user_input)
                # If streamed, already printed; if not, print now
                if self._streaming_buf:
                    pass  # already printed via callback
                console.print()
            except KeyboardInterrupt:
                console.print("\n[dim]Interrumpido.[/dim]")
            except Exception as e:
                error_line(f"Error: {e}")

    # ------------------------------------------------------------------

    def _print_greeting(self) -> None:
        ctx = EnvContext()
        greeting_panel(ctx.greeting_line(), ctx.location_line())
        mode = self._agent.llm.current_mode()
        info_line(f"Motor: {mode}" + (" | incógnito" if self._incognito else ""))

        # Suggest profile change if in a coding repo
        try:
            from adv_archon.core.profiles import ProfileManager
            pm = ProfileManager(self._data_dir)
            pm.load()
            suggested = pm.auto_detect(Path.cwd())
            if suggested and suggested.name != pm.active.name:
                info_line(f"Perfil sugerido para este directorio: {suggested.name} (/profile {suggested.name})")
        except Exception:
            pass

    def _handle_slash(self, cmd: str) -> str | None:
        from adv_archon.ui.commands import handle_command
        return handle_command(cmd, self._agent, self._cfg, self._data_dir)

    def _confirm(self, preview: str) -> bool:
        from adv_archon.ui.render import confirm_prompt
        return confirm_prompt(preview)

    def _on_stream(self, text: str) -> None:
        self._streaming_buf.append(text)
        assistant_markdown(text)
