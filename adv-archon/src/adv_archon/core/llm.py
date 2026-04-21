"""LLM router — Ollama (local) + Gemini (cloud) con streaming y tool calling."""

from __future__ import annotations

import json
from typing import Any, Generator, Iterator

from adv_archon.core.config import Config


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

class UsageAccumulator:
    def __init__(self) -> None:
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost_usd = 0.0

    def add(self, prompt: int, completion: int, cost: float = 0.0) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.cost_usd += cost

    def summary(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.prompt_tokens + self.completion_tokens,
            "cost_usd": round(self.cost_usd, 6),
        }


# ---------------------------------------------------------------------------
# Ollama client
# ---------------------------------------------------------------------------

class OllamaLLM:
    def __init__(self, cfg: Config, usage: UsageAccumulator) -> None:
        self._cfg = cfg
        self._usage = usage

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = True,
    ) -> dict:
        import ollama  # type: ignore

        kwargs: dict[str, Any] = {
            "model": self._cfg.ollama_model,
            "messages": messages,
            "stream": False,  # tool calling needs non-streaming first pass
        }
        if tools:
            kwargs["tools"] = tools

        response = ollama.chat(**kwargs)  # type: ignore
        msg = response.message  # type: ignore

        # accumulate usage (Ollama returns token counts)
        if hasattr(response, "prompt_eval_count"):
            self._usage.add(
                response.prompt_eval_count or 0,
                response.eval_count or 0,
            )

        return {
            "content": msg.content or "",
            "tool_calls": [
                {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                    if isinstance(tc.function.arguments, dict)
                    else json.loads(tc.function.arguments or "{}"),
                }
                for tc in (msg.tool_calls or [])
            ],
        }

    def stream_chat(self, messages: list[dict]) -> Iterator[str]:
        import ollama  # type: ignore

        for chunk in ollama.chat(  # type: ignore
            model=self._cfg.ollama_model,
            messages=messages,
            stream=True,
        ):
            delta = chunk.message.content  # type: ignore
            if delta:
                yield delta


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------

class GeminiLLM:
    def __init__(self, cfg: Config, usage: UsageAccumulator) -> None:
        self._cfg = cfg
        self._usage = usage
        self._client = None

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai  # type: ignore
            if not self._cfg.gemini_api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY no configurado. "
                    "Añádelo a ~/.adv-archon/.env o usa /mode local"
                )
            genai.configure(api_key=self._cfg.gemini_api_key)
            self._client = genai.GenerativeModel(self._cfg.gemini_model)
        return self._client

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> dict:
        import google.generativeai as genai  # type: ignore

        client = self._get_client()
        # Convert OpenAI-style messages to Gemini format
        history = []
        system_text = ""
        for m in messages:
            role = m["role"]
            content = m["content"] or ""
            if role == "system":
                system_text = content
                continue
            gemini_role = "user" if role == "user" else "model"
            history.append({"role": gemini_role, "parts": [content]})

        # Gemini doesn't support system role in history; prepend to first user message
        if system_text and history and history[0]["role"] == "user":
            history[0]["parts"][0] = f"{system_text}\n\n{history[0]['parts'][0]}"

        last = history.pop() if history else {"role": "user", "parts": [""]}
        chat = client.start_chat(history=history)
        response = chat.send_message(last["parts"][0])
        text = response.text or ""

        if hasattr(response, "usage_metadata"):
            um = response.usage_metadata
            # Gemini pricing (flash): ~$0.075/1M input, $0.30/1M output
            cost = (getattr(um, "prompt_token_count", 0) * 0.075 +
                    getattr(um, "candidates_token_count", 0) * 0.30) / 1_000_000
            self._usage.add(
                getattr(um, "prompt_token_count", 0),
                getattr(um, "candidates_token_count", 0),
                cost,
            )

        return {"content": text, "tool_calls": []}

    def stream_chat(self, messages: list[dict]) -> Iterator[str]:
        # Gemini streaming is similar but simpler here
        result = self.chat(messages, stream=False)
        yield result["content"]


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class LLMRouter:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self.usage = UsageAccumulator()
        self._ollama = OllamaLLM(cfg, self.usage)
        self._gemini = GeminiLLM(cfg, self.usage)

    def _backend(self):
        return self._ollama if self._cfg.mode == "local" else self._gemini

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        return self._backend().chat(messages, tools=tools)

    def stream_chat(self, messages: list[dict]) -> Iterator[str]:
        return self._backend().stream_chat(messages)

    def current_mode(self) -> str:
        return f"{self._cfg.mode} ({self._cfg.ollama_model if self._cfg.mode == 'local' else self._cfg.gemini_model})"
