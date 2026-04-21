"""Enhanced automations — daily brief, weekly review, repo watcher, recurring reminders."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import textwrap
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Daily brief
# ---------------------------------------------------------------------------

class DailyBrief:
    """Compose a rich daily brief from calendar, tasks, memory and git repos."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._cache = data_dir / "daily_brief_cache.json"

    # ------------------------------------------------------------------
    def build(self, include_repos: list[Path] | None = None) -> str:
        now = datetime.datetime.now()
        sections: list[str] = []

        sections.append(f"# Resumen del día — {now.strftime('%A %d de %B de %Y, %H:%M')}\n")

        # Calendar
        try:
            cal = self._calendar_section(now)
            if cal:
                sections.append(cal)
        except Exception as e:
            sections.append(f"## Calendario\n_(No disponible: {e})_\n")

        # Tasks
        try:
            tasks = self._tasks_section()
            if tasks:
                sections.append(tasks)
        except Exception as e:
            sections.append(f"## Tareas\n_(No disponible: {e})_\n")

        # Repos
        if include_repos:
            for repo in include_repos:
                try:
                    r = self._repo_section(repo)
                    if r:
                        sections.append(r)
                except Exception:
                    pass

        # Pending notes from memory
        try:
            notes = self._pending_notes_section()
            if notes:
                sections.append(notes)
        except Exception:
            pass

        result = "\n".join(sections)
        self._save_cache(result)
        return result

    # ------------------------------------------------------------------
    def _calendar_section(self, now: datetime.datetime) -> str:
        try:
            from adv_archon.tools.personal import calendar_upcoming  # type: ignore
            events = calendar_upcoming(days=1, limit=10)
        except Exception:
            return ""
        if not events:
            return "## Calendario\nSin eventos hoy.\n"
        lines = ["## Calendario hoy"]
        for ev in events:
            t = ev.get("start_time", "")
            lines.append(f"- **{t}** — {ev.get('title', '')}")
        return "\n".join(lines) + "\n"

    def _tasks_section(self) -> str:
        try:
            from adv_archon.core.tasks import TaskStore  # type: ignore
            store = TaskStore(self._data_dir)
            open_tasks = store.list(status="open", limit=10)
            overdue = store.list(status="overdue", limit=5)
        except Exception:
            return ""
        lines = ["## Tareas pendientes"]
        if overdue:
            lines.append("**Vencidas:**")
            for t in overdue:
                lines.append(f"- [!] {t.get('title', '')} — {t.get('due', '')}")
        if open_tasks:
            for t in open_tasks:
                due = f" (vence {t['due']})" if t.get("due") else ""
                lines.append(f"- {t.get('title', '')}{due}")
        if not open_tasks and not overdue:
            lines.append("Sin tareas abiertas.")
        return "\n".join(lines) + "\n"

    def _repo_section(self, repo: Path) -> str:
        if not (repo / ".git").is_dir():
            return ""
        branch = _git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
        log = _git(repo, ["log", "--oneline", "-5"])
        status = _git(repo, ["status", "--short"])
        dirty = f" ({status.count(chr(10)) + 1} cambios)" if status.strip() else " (limpio)"
        lines = [
            f"## Repo: {repo.name}",
            f"Rama: `{branch}`{dirty}",
        ]
        if log:
            lines.append("Últimos commits:")
            for l in log.splitlines()[:5]:
                lines.append(f"  - {l}")
        return "\n".join(lines) + "\n"

    def _pending_notes_section(self) -> str:
        notes_file = self._data_dir / "pending_notes.json"
        if not notes_file.exists():
            return ""
        try:
            notes = json.loads(notes_file.read_text())
        except Exception:
            return ""
        if not notes:
            return ""
        lines = ["## Notas pendientes"]
        for n in notes[:5]:
            lines.append(f"- {n}")
        return "\n".join(lines) + "\n"

    def _save_cache(self, text: str) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._cache.write_text(text)

    def get_cached(self) -> Optional[str]:
        if self._cache.exists():
            return self._cache.read_text()
        return None


# ---------------------------------------------------------------------------
# Weekly review
# ---------------------------------------------------------------------------

class WeeklyReview:
    """Generate a weekly summary: completed tasks, git activity, patterns."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir

    def build(self, include_repos: list[Path] | None = None) -> str:
        now = datetime.datetime.now()
        week_start = now - datetime.timedelta(days=now.weekday())
        sections = [
            f"# Revisión semanal — semana del {week_start.strftime('%d/%m/%Y')}\n"
        ]

        # Completed tasks this week
        try:
            from adv_archon.core.tasks import TaskStore  # type: ignore
            store = TaskStore(self._data_dir)
            done = store.list(status="done", since=week_start, limit=20)
            if done:
                sections.append("## Completado esta semana")
                for t in done:
                    sections.append(f"- [x] {t.get('title', '')}")
                sections.append("")
        except Exception:
            pass

        # Git activity
        if include_repos:
            for repo in include_repos:
                try:
                    since = week_start.strftime("%Y-%m-%d")
                    log = _git(repo, ["log", f"--since={since}", "--oneline"])
                    if log.strip():
                        sections.append(f"## Actividad en {repo.name}")
                        for line in log.splitlines()[:15]:
                            sections.append(f"  - {line}")
                        sections.append("")
                except Exception:
                    pass

        # Pending for next week
        try:
            from adv_archon.core.tasks import TaskStore  # type: ignore
            store = TaskStore(self._data_dir)
            upcoming = store.list(status="open", limit=10)
            if upcoming:
                sections.append("## Para la próxima semana")
                for t in upcoming:
                    sections.append(f"- {t.get('title', '')}")
                sections.append("")
        except Exception:
            pass

        return "\n".join(sections)


# ---------------------------------------------------------------------------
# Repo watcher
# ---------------------------------------------------------------------------

class RepoWatcher:
    """Detect changes in a git repo since last check."""

    def __init__(self, data_dir: Path) -> None:
        self._state_file = data_dir / "repo_watcher_state.json"
        self._state: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._state_file.exists():
            try:
                self._state = json.loads(self._state_file.read_text())
            except Exception:
                pass

    def _save(self) -> None:
        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps(self._state))

    def check(self, repo: Path) -> dict:
        """Return new commits and changed files since last check."""
        if not (repo / ".git").is_dir():
            return {"error": "No es un repositorio git"}
        key = str(repo)
        current_head = _git(repo, ["rev-parse", "HEAD"]).strip()
        last_head = self._state.get(key, "")
        if not last_head:
            self._state[key] = current_head
            self._save()
            return {"status": "primera_vez", "head": current_head}
        if last_head == current_head:
            return {"status": "sin_cambios", "head": current_head}
        log = _git(repo, ["log", "--oneline", f"{last_head}..{current_head}"])
        diff_stat = _git(repo, ["diff", "--stat", f"{last_head}..{current_head}"])
        self._state[key] = current_head
        self._save()
        return {
            "status": "cambios",
            "from": last_head[:8],
            "to": current_head[:8],
            "commits": log.strip().splitlines(),
            "diff_stat": diff_stat.strip(),
        }


# ---------------------------------------------------------------------------
# Recurring reminders via launchd
# ---------------------------------------------------------------------------

PLIST_TEMPLATE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>{label}</string>
        <key>ProgramArguments</key>
        <array>
            <string>{adv_path}</string>
            {args}
        </array>
        <key>StartCalendarInterval</key>
        <dict>
            <key>Hour</key>
            <integer>{hour}</integer>
            <key>Minute</key>
            <integer>{minute}</integer>
        </dict>
        <key>StandardOutPath</key>
        <string>{log_path}</string>
        <key>StandardErrorPath</key>
        <string>{log_path}</string>
    </dict>
    </plist>
""")


def install_daily_brief_launchd(hour: int = 8, minute: int = 30) -> dict:
    """Install a launchd agent that runs `adv daily` every day at hh:mm."""
    import shutil

    adv_path = shutil.which("adv") or shutil.which("adv-archon") or ""
    if not adv_path:
        return {"error": "adv-archon no está en PATH. Instálalo primero con uv tool install."}

    label = "com.advarchon.daily"
    log_path = Path.home() / ".adv-archon" / "logs" / "daily.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / f"{label}.plist"

    args = "<string>daily</string>"
    plist = PLIST_TEMPLATE.format(
        label=label,
        adv_path=adv_path,
        args=args,
        hour=hour,
        minute=minute,
        log_path=str(log_path),
    )
    plist_path.write_text(plist)
    # unload if already loaded
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    result = subprocess.run(
        ["launchctl", "load", "-w", str(plist_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip(), "plist": str(plist_path)}
    return {
        "status": "instalado",
        "schedule": f"cada día a las {hour:02d}:{minute:02d}",
        "plist": str(plist_path),
        "log": str(log_path),
    }


def uninstall_daily_brief_launchd() -> dict:
    label = "com.advarchon.daily"
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{label}.plist"
    if not plist_path.exists():
        return {"status": "no_instalado"}
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    plist_path.unlink()
    return {"status": "desinstalado"}


def install_repo_watcher_launchd(repo_path: str, interval_minutes: int = 30) -> dict:
    """Install a launchd agent that monitors a repo every N minutes."""
    import shutil

    adv_path = shutil.which("adv") or shutil.which("adv-archon") or ""
    if not adv_path:
        return {"error": "adv-archon no está en PATH"}
    label = "com.advarchon.repowatcher"
    log_path = Path.home() / ".adv-archon" / "logs" / "repo_watcher.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / f"{label}.plist"
    plist = textwrap.dedent(f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
          "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{label}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{adv_path}</string>
                <string>watch-repo</string>
                <string>{repo_path}</string>
            </array>
            <key>StartInterval</key>
            <integer>{interval_minutes * 60}</integer>
            <key>StandardOutPath</key>
            <string>{log_path}</string>
            <key>StandardErrorPath</key>
            <string>{log_path}</string>
        </dict>
        </plist>
    """)
    plist_path.write_text(plist)
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    result = subprocess.run(
        ["launchctl", "load", "-w", str(plist_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()}
    return {
        "status": "instalado",
        "repo": repo_path,
        "interval": f"cada {interval_minutes} minutos",
        "plist": str(plist_path),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git(repo: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

def build_daily_brief(include_repos: str = "") -> str:
    """Genera el resumen diario: calendario, tareas, repos y notas."""
    data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
    repos = [Path(r.strip()).expanduser() for r in include_repos.split(",") if r.strip()]
    return DailyBrief(data_dir).build(repos or None)


def build_weekly_review(include_repos: str = "") -> str:
    """Genera la revisión semanal: completado, actividad en repos, próxima semana."""
    data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
    repos = [Path(r.strip()).expanduser() for r in include_repos.split(",") if r.strip()]
    return WeeklyReview(data_dir).build(repos or None)


def check_repo_changes(repo_path: str) -> dict:
    """Comprueba si hay cambios nuevos en un repo git desde la última revisión."""
    data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
    return RepoWatcher(data_dir).check(Path(repo_path).expanduser())


TOOL_DEFINITIONS = [
    {
        "name": "build_daily_brief",
        "description": "Genera el resumen diario: calendario, tareas pendientes, actividad en repos y notas.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_repos": {
                    "type": "string",
                    "description": "Rutas de repos separadas por coma, ej. ~/code/myproject",
                    "default": "",
                }
            },
        },
        "function": build_daily_brief,
    },
    {
        "name": "build_weekly_review",
        "description": "Genera la revisión semanal: tareas completadas, actividad en repos y planificación.",
        "parameters": {
            "type": "object",
            "properties": {
                "include_repos": {"type": "string", "default": ""}
            },
        },
        "function": build_weekly_review,
    },
    {
        "name": "check_repo_changes",
        "description": "Detecta commits nuevos en un repo git desde la última comprobación.",
        "parameters": {
            "type": "object",
            "properties": {"repo_path": {"type": "string"}},
            "required": ["repo_path"],
        },
        "function": check_repo_changes,
    },
    {
        "name": "install_daily_brief_launchd",
        "description": "Instala un agente launchd para ejecutar el daily brief automáticamente cada día.",
        "parameters": {
            "type": "object",
            "properties": {
                "hour": {"type": "integer", "default": 8},
                "minute": {"type": "integer", "default": 30},
            },
        },
        "function": install_daily_brief_launchd,
        "requires_confirmation": True,
    },
]
