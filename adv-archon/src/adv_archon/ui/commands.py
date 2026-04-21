"""Slash commands dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adv_archon.core.agent import Agent
    from adv_archon.core.config import Config


def handle_command(cmd: str, agent: "Agent", cfg: "Config", data_dir: Path) -> str | None:
    """
    Returns a string to print, or None if the command is unknown.
    Returns the special string '__exit__' to quit.
    Returns '__clear__' to clear the screen.
    """
    parts = cmd.strip().lstrip("/").split(None, 1)
    name = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if name in ("exit", "quit", "q"):
        return "__exit__"

    if name == "help":
        return _help_text()

    if name == "clear":
        return "__clear__"

    if name == "mode":
        return _cmd_mode(args, cfg, agent)

    if name == "cost":
        return _cmd_cost(agent)

    if name == "recall":
        return _cmd_recall(args, agent)

    if name == "forget":
        return _cmd_forget(args, agent)

    if name == "remember":
        return _cmd_remember(args, agent)

    if name == "read":
        return _cmd_read(args)

    if name == "web":
        return _cmd_web(args)

    if name == "run":
        return _cmd_run(args, agent, cfg)

    if name == "auto":
        return _cmd_auto(args, agent)

    if name == "profile":
        return _cmd_profile(args, data_dir, agent)

    if name == "dashboard":
        return _cmd_dashboard(data_dir)

    if name == "weekly":
        return _cmd_weekly()

    if name == "people":
        return _cmd_people(args, data_dir)

    if name == "projects":
        return _cmd_projects(data_dir)

    if name == "log":
        return _cmd_log(data_dir)

    if name == "voice":
        return _cmd_voice(args)

    if name in ("listen", "l"):
        return _cmd_listen()

    return None  # unknown command


# ---------------------------------------------------------------------------

def _help_text() -> str:
    return """\
Comandos disponibles:
  /mode local|cloud    Cambiar motor LLM
  /recall <query>      Buscar en memoria a largo plazo
  /remember <text>     Guardar recuerdo
  /forget <id>         Borrar recuerdo por ID
  /read <path>         Leer archivo
  /web <query>         Búsqueda web
  /run <cmd>           Ejecutar comando shell
  /auto on|off         Activar/desactivar modo automático
  /profile [name]      Ver o cambiar perfil activo
  /dashboard           Panel con calendario, tareas y coste
  /weekly              Revisión semanal
  /people [query]      Personas en memoria
  /projects            Proyectos activos en memoria
  /cost                Coste de la sesión
  /log                 Últimas entradas del log
  /voice on|off        Activar/desactivar TTS
  /listen              Dictar entrada por voz
  /clear               Limpiar pantalla
  /exit                Salir"""


def _cmd_mode(args: str, cfg: "Config", agent: "Agent") -> str:
    mode = args.strip().lower()
    if mode in ("local", "cloud"):
        cfg.mode = mode
        return f"Modo cambiado a: {agent.llm.current_mode()}"
    return f"Modo actual: {agent.llm.current_mode()}\nUsa /mode local o /mode cloud"


def _cmd_cost(agent: "Agent") -> str:
    s = agent.llm.usage.summary()
    return (
        f"Tokens usados: {s['total_tokens']:,} "
        f"(prompt: {s['prompt_tokens']:,}, respuesta: {s['completion_tokens']:,})\n"
        f"Coste estimado: ${s['cost_usd']:.6f}"
    )


def _cmd_recall(args: str, agent: "Agent") -> str:
    if not args.strip():
        recent = agent.memory.list_recent(10)
        if not recent:
            return "Memoria a largo plazo vacía."
        lines = ["Recuerdos recientes:"]
        for r in recent:
            lines.append(f"  [{r['id']}] {r['content'][:100]}")
        return "\n".join(lines)
    hits = agent.memory.recall(args.strip())
    if not hits:
        return f"Sin resultados para '{args.strip()}'."
    lines = [f"Resultados para '{args.strip()}':"]
    for r in hits:
        lines.append(f"  [{r['id']}] {r['content'][:120]}")
    return "\n".join(lines)


def _cmd_remember(args: str, agent: "Agent") -> str:
    if not args.strip():
        return "Uso: /remember <hecho a recordar>"
    mid = agent.memory.remember(args.strip())
    return f"Guardado con ID {mid}."


def _cmd_forget(args: str, agent: "Agent") -> str:
    if not args.strip().isdigit():
        return "Uso: /forget <id>  (usa /recall para ver IDs)"
    mid = int(args.strip())
    ok = agent.memory.forget(mid)
    return f"Recuerdo {mid} eliminado." if ok else "No se encontró ese recuerdo."


def _cmd_read(args: str) -> str:
    if not args.strip():
        return "Uso: /read <ruta>"
    try:
        from adv_archon.tools.files import read_file
        return read_file(args.strip())
    except Exception as e:
        return f"Error: {e}"


def _cmd_web(args: str) -> str:
    if not args.strip():
        return "Uso: /web <consulta>"
    try:
        from adv_archon.tools.web import web_search
        results = web_search(args.strip())
        lines = []
        for r in results:
            lines.append(f"- **{r['title']}**\n  {r['url']}\n  {r['snippet']}")
        return "\n".join(lines) if lines else "Sin resultados."
    except Exception as e:
        return f"Error: {e}"


def _cmd_run(args: str, agent: "Agent", cfg: "Config") -> str:
    if not args.strip():
        return "Uso: /run <comando>"
    try:
        from adv_archon.tools.shell import shell_exec
        return shell_exec(args.strip(), auto=agent._auto)
    except Exception as e:
        return f"Error: {e}"


def _cmd_auto(args: str, agent: "Agent") -> str:
    val = args.strip().lower()
    if val == "on":
        from adv_archon.ui.render import confirm_prompt
        ok = confirm_prompt(
            "MODO AUTO: todos los comandos se ejecutarán sin confirmación "
            "(excepto destructivos). ¿Confirmar?"
        )
        if ok:
            agent.set_auto(True)
            return "Modo AUTO activado. Usa /auto off para desactivar."
        return "Modo AUTO no activado."
    if val == "off":
        agent.set_auto(False)
        return "Modo AUTO desactivado."
    status = "ACTIVADO" if agent._auto else "desactivado"
    return f"Modo AUTO: {status}. Usa /auto on|off"


def _cmd_profile(args: str, data_dir: Path, agent: "Agent") -> str:
    try:
        from adv_archon.core.profiles import ProfileManager
        pm = ProfileManager(data_dir)
        pm.load()
        if args.strip():
            try:
                active = pm.set(args.strip())
                agent.set_profile_overlay(active.system_overlay)
                return f"Perfil activo: {active.name} — {active.description}"
            except ValueError as e:
                return str(e)
        lines = ["Perfiles disponibles:"]
        for p in pm.list_all():
            marker = "→" if p["active"] else " "
            lines.append(f"  {marker} {p['name']} — {p['description']}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _cmd_dashboard(data_dir: Path) -> str:
    try:
        from adv_archon.tools.dashboard import build_dashboard_data, format_dashboard
        return format_dashboard(build_dashboard_data())
    except Exception as e:
        return f"Error: {e}"


def _cmd_weekly() -> str:
    try:
        from adv_archon.core.automations import build_weekly_review
        return build_weekly_review()
    except Exception as e:
        return f"Error: {e}"


def _cmd_people(args: str, data_dir: Path) -> str:
    try:
        from adv_archon.core.memory_entities import get_entity_store
        store = get_entity_store(data_dir)
        results = store.search_persons(args.strip()) if args.strip() else store.list_persons(10)
        if not results:
            return "Sin personas en memoria."
        lines = []
        for p in results:
            co = f" ({p['company']})" if p.get("company") else ""
            em = f" <{p['email']}>" if p.get("email") else ""
            lines.append(f"- **{p['name']}**{co}{em}")
            if p.get("notes"):
                lines.append(f"  {p['notes'][:80]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _cmd_projects(data_dir: Path) -> str:
    try:
        from adv_archon.core.memory_entities import get_entity_store
        store = get_entity_store(data_dir)
        projects = store.list_projects(status="active")
        if not projects:
            return "Sin proyectos activos en memoria."
        lines = []
        for p in projects:
            deadline = f" (deadline: {p['deadline']})" if p.get("deadline") else ""
            stack = ", ".join(p.get("tech_stack", []))
            lines.append(f"- **{p['name']}** [{p['status']}]{deadline}")
            if stack:
                lines.append(f"  Stack: {stack}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


def _cmd_log(data_dir: Path) -> str:
    log_dir = data_dir / "logs"
    if not log_dir.exists():
        return "Sin logs."
    logs = sorted(log_dir.glob("*.jsonl"), reverse=True)
    if not logs:
        return "Sin logs."
    lines = []
    import json
    for entry in open(logs[0]).readlines()[-10:]:
        try:
            d = json.loads(entry)
            lines.append(f"[{d.get('time','')}] {d.get('event','')}: {d.get('msg','')}")
        except Exception:
            lines.append(entry.strip())
    return "\n".join(lines) if lines else "Log vacío."


def _cmd_voice(args: str) -> str:
    val = args.strip().lower()
    if val in ("on", "off"):
        return f"Voz {'activada' if val == 'on' else 'desactivada'} (requiere módulo voice)."
    return "Uso: /voice on|off"


def _cmd_listen() -> str:
    try:
        from adv_archon.voice.stt import listen_once
        result = listen_once()
        return f"Transcripción: {result}"
    except ImportError:
        return "Módulo STT no instalado. Ejecuta: uv pip install faster-whisper sounddevice"
    except Exception as e:
        return f"Error STT: {e}"
