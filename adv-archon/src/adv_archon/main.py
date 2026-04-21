"""ADV ARCHON — entrypoint CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _data_dir() -> Path:
    import os
    p = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
    p.mkdir(mode=0o700, parents=True, exist_ok=True)
    return p


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="adv-archon",
        description="ADV ARCHON — asistente personal de terminal",
    )
    parser.add_argument("query", nargs="?", help="Consulta one-shot (responde y sale)")
    parser.add_argument("--mode", choices=["local", "cloud"], default=None,
                        help="Motor LLM: local (Ollama) o cloud (Gemini)")
    parser.add_argument("--model", default=None, help="Modelo específico (ej. llama3.1:8b)")
    parser.add_argument("--auto", action="store_true",
                        help="Modo AUTO: ejecuta comandos shell sin confirmación (excepto destructivos)")
    parser.add_argument("--incognito", action="store_true",
                        help="Sin persistencia de sesión ni memoria")
    parser.add_argument("--listen", action="store_true",
                        help="Activar wake-word STT al arrancar")
    parser.add_argument("subcommand", nargs="?",
                        choices=["daily", "tasks", "weekly", "profile", "watch-repo"],
                        help="Subcomando")

    # Separar subcomandos de queries
    args, extra = parser.parse_known_args()

    data = _data_dir()

    # ----------------------------------------------------------------
    # Subcomandos
    # ----------------------------------------------------------------
    if args.subcommand == "daily" or (args.query and args.query == "daily"):
        _cmd_daily(data)
        return

    if args.subcommand == "tasks" or (args.query and args.query == "tasks"):
        _cmd_tasks(data)
        return

    if args.subcommand == "weekly":
        _cmd_weekly(data)
        return

    if args.subcommand == "profile":
        _cmd_profile(data, extra)
        return

    if args.subcommand == "watch-repo" and extra:
        _cmd_watch_repo(data, extra[0])
        return

    # ----------------------------------------------------------------
    # One-shot
    # ----------------------------------------------------------------
    if args.query and args.query not in ("daily", "tasks", "weekly"):
        _run_oneshot(args, data)
        return

    # ----------------------------------------------------------------
    # REPL interactivo
    # ----------------------------------------------------------------
    _run_repl(args, data)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def _cmd_daily(data: Path) -> None:
    try:
        from adv_archon.core.automations import DailyBrief
        brief = DailyBrief(data).build()
        from rich.console import Console
        from rich.markdown import Markdown
        Console().print(Markdown(brief))
    except ImportError:
        print("[daily] Módulo automations no disponible.")


def _cmd_tasks(data: Path) -> None:
    try:
        from adv_archon.core.tasks import TaskStore
        store = TaskStore(data)
        tasks = store.list(status="open", limit=20)
        if not tasks:
            print("Sin tareas pendientes.")
            return
        for t in tasks:
            due = f" [{t['due']}]" if t.get("due") else ""
            print(f"  [ ] {t['title']}{due}")
    except ImportError:
        print("[tasks] Módulo tasks no disponible.")


def _cmd_weekly(data: Path) -> None:
    try:
        from adv_archon.core.automations import build_weekly_review
        from rich.console import Console
        from rich.markdown import Markdown
        Console().print(Markdown(build_weekly_review()))
    except ImportError:
        print("[weekly] Módulo automations no disponible.")


def _cmd_profile(data: Path, extra: list[str]) -> None:
    try:
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(data)
        pm.load()
        if extra:
            try:
                pm.set(extra[0])
                print(f"Perfil activo: {extra[0]}")
            except ValueError as e:
                print(e)
        else:
            for p in pm.list_all():
                marker = "→" if p["active"] else " "
                print(f"  {marker} {p['name']} — {p['description']}")
    except ImportError:
        print("[profile] Módulo profiles no disponible.")


def _cmd_watch_repo(data: Path, repo_path: str) -> None:
    try:
        from adv_archon.core.automations import RepoWatcher
        result = RepoWatcher(data).check(Path(repo_path).expanduser())
        if result.get("status") == "cambios":
            print(f"Cambios en {repo_path}:")
            for c in result.get("commits", []):
                print(f"  - {c}")
        else:
            print(f"Estado: {result.get('status', 'desconocido')}")
    except ImportError:
        print("[watch-repo] Módulo automations no disponible.")


def _run_oneshot(args: argparse.Namespace, data: Path) -> None:
    from adv_archon.core.config import Config
    from adv_archon.core.agent import Agent

    cfg = Config(data)
    if args.mode:
        cfg.mode = args.mode
    if args.model:
        cfg.ollama_model = args.model

    agent = Agent(cfg, data, auto=args.auto, incognito=args.incognito)
    response = agent.run_sync(args.query)
    print(response)


def _run_repl(args: argparse.Namespace, data: Path) -> None:
    from adv_archon.core.config import Config
    from adv_archon.ui.repl import Repl

    cfg = Config(data)
    if args.mode:
        cfg.mode = args.mode
    if args.model:
        cfg.ollama_model = args.model

    repl = Repl(cfg, data, auto=args.auto, incognito=args.incognito)
    repl.run()


if __name__ == "__main__":
    main()
