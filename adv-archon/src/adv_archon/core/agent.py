"""Agent — loop agéntico con tool calling real vía Ollama."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Iterator

from adv_archon.core.config import Config
from adv_archon.core.llm import LLMRouter
from adv_archon.core.memory import MemoryManager
from adv_archon.core.context import EnvContext


SYSTEM_PROMPT = """\
Eres ADV ARCHON, el asistente personal de terminal de Pablo.
Eres eficiente, conciso y honesto. Respondes en español peninsular.
Sin disclaimers innecesarios. Sin pedir permiso para pensar.
Cuando uses una tool, dilo en una línea antes: [tool_name: input].
Si detectas un problema adyacente al que te preguntan, menciónalo en una línea al final.
Distingue lo que sabes de lo que inferes. Si necesitas internet para estar seguro, búscalo.

{context}
{memory}
{profile_overlay}
"""


class Agent:
    def __init__(
        self,
        cfg: Config,
        data_dir: Path,
        auto: bool = False,
        incognito: bool = False,
        confirm_callback: Callable[[str], bool] | None = None,
        stream_callback: Callable[[str], None] | None = None,
        profile_overlay: str = "",
    ) -> None:
        self._cfg = cfg
        self._data_dir = data_dir
        self._auto = auto
        self._incognito = incognito
        self._confirm = confirm_callback or _default_confirm
        self._stream_cb = stream_callback
        self._profile_overlay = profile_overlay

        self._llm = LLMRouter(cfg)
        self._memory = MemoryManager(data_dir, incognito=incognito)
        self._tools: dict[str, dict] = {}
        self._register_tools()

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------

    def _register_tools(self) -> None:
        from adv_archon.tools.files import TOOL_DEFINITIONS as FILE_TOOLS
        from adv_archon.tools.web import TOOL_DEFINITIONS as WEB_TOOLS
        from adv_archon.tools.shell import TOOL_DEFINITIONS as SHELL_TOOLS
        from adv_archon.core.memory_entities import TOOL_DEFINITIONS as ENTITY_TOOLS
        from adv_archon.core.automations import TOOL_DEFINITIONS as AUTO_TOOLS

        all_tools = [
            *FILE_TOOLS,
            *WEB_TOOLS,
            *SHELL_TOOLS,
            *ENTITY_TOOLS,
            *AUTO_TOOLS,
        ]

        # Optional tools
        try:
            from adv_archon.tools.personal import TOOL_DEFINITIONS as PERSONAL_TOOLS
            all_tools += PERSONAL_TOOLS
        except ImportError:
            pass
        try:
            from adv_archon.tools.notion import TOOL_DEFINITIONS as NOTION_TOOLS
            all_tools += NOTION_TOOLS
        except ImportError:
            pass
        try:
            from adv_archon.tools.obsidian import TOOL_DEFINITIONS as OBSIDIAN_TOOLS
            all_tools += OBSIDIAN_TOOLS
        except ImportError:
            pass
        try:
            from adv_archon.tools.gmail import TOOL_DEFINITIONS as GMAIL_TOOLS
            all_tools += GMAIL_TOOLS
        except ImportError:
            pass

        for t in all_tools:
            self._tools[t["name"]] = t

    def tool_schemas(self) -> list[dict]:
        """Return tools in Ollama/OpenAI function-calling format."""
        schemas = []
        for name, t in self._tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {"type": "object", "properties": {}}),
                },
            })
        return schemas

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def chat(self, user_input: str) -> str:
        """Process one user turn. Returns the final assistant text."""
        self._memory.add_turn("user", user_input)
        ctx = EnvContext()
        mem_ctx = self._memory.relevant_context(user_input)

        system = SYSTEM_PROMPT.format(
            context=ctx.as_system_snippet(),
            memory=mem_ctx,
            profile_overlay=self._profile_overlay,
        )

        messages: list[dict] = [{"role": "system", "content": system}]
        messages += self._memory.get_turns(last_n=self._cfg.context_window_turns)

        tools = self.tool_schemas()
        max_rounds = self._cfg.max_tool_rounds

        for _round in range(max_rounds):
            response = self._llm.chat(messages, tools=tools)
            tool_calls = response.get("tool_calls", [])

            if not tool_calls:
                # Final answer — stream it
                final = response["content"]
                if self._stream_cb:
                    self._stream_cb(final)
                self._memory.add_turn("assistant", final)
                return final

            # Execute tool calls
            messages.append({"role": "assistant", "content": response["content"], "tool_calls": tool_calls})

            for tc in tool_calls:
                tool_name = tc["name"]
                tool_args = tc.get("arguments", {})
                result = self._execute_tool(tool_name, tool_args)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        # Max rounds hit — ask for summary
        messages.append({"role": "user", "content": "Resume los resultados obtenidos."})
        final_resp = self._llm.chat(messages)
        text = final_resp["content"]
        if self._stream_cb:
            self._stream_cb(text)
        self._memory.add_turn("assistant", text)
        return text

    def run_sync(self, user_input: str) -> str:
        return self.chat(user_input)

    # ------------------------------------------------------------------
    # Tool execution with authorization
    # ------------------------------------------------------------------

    def _execute_tool(self, name: str, args: dict) -> Any:
        if name not in self._tools:
            return {"error": f"Tool '{name}' no registrada"}

        tool = self._tools[name]
        fn = tool.get("function")
        requires_confirm = tool.get("requires_confirmation", False)

        # Shell commands always go through shell.py's own policy
        if not requires_confirm and not self._auto:
            requires_confirm = name in ("shell_exec", "python_exec", "send_email")

        if requires_confirm and not self._auto:
            preview = f"{name}({json.dumps(args, ensure_ascii=False)[:120]})"
            if not self._confirm(preview):
                return {"status": "cancelado", "reason": "Usuario rechazó la ejecución"}

        if fn is None:
            return {"error": "Tool sin función implementada"}

        try:
            # Pass auto flag to shell tools
            if name == "shell_exec":
                return fn(auto=self._auto, **args)
            return fn(**args)
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------

    @property
    def memory(self) -> MemoryManager:
        return self._memory

    @property
    def llm(self) -> LLMRouter:
        return self._llm

    def set_auto(self, value: bool) -> None:
        self._auto = value

    def set_profile_overlay(self, overlay: str) -> None:
        self._profile_overlay = overlay


def _default_confirm(preview: str) -> bool:
    try:
        ans = input(f"\n¿Ejecutar {preview}? (y/N) ").strip().lower()
        return ans in ("y", "s", "si", "sí", "yes")
    except EOFError:
        return False
