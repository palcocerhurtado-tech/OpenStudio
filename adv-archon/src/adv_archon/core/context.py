"""Environment context — pwd, git, time, project working set."""

from __future__ import annotations

import datetime
import subprocess
from pathlib import Path


class EnvContext:
    """Snapshot of the current execution environment."""

    def __init__(self) -> None:
        self.cwd = Path.cwd()
        self.now = datetime.datetime.now()
        self.git_branch: str = ""
        self.git_dirty: bool = False
        self.git_change_count: int = 0
        self.project_files: list[str] = []
        self._detect_git()
        self._detect_project()

    def _detect_git(self) -> None:
        try:
            branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=3,
            )
            if branch.returncode == 0:
                self.git_branch = branch.stdout.strip()
                status = subprocess.run(
                    ["git", "status", "--short"],
                    capture_output=True, text=True, timeout=3,
                )
                lines = [l for l in status.stdout.splitlines() if l.strip()]
                self.git_dirty = bool(lines)
                self.git_change_count = len(lines)
        except Exception:
            pass

    def _detect_project(self) -> None:
        markers = [
            "pyproject.toml", "package.json", "Cargo.toml", "go.mod",
            "Makefile", "README.md", "README.rst",
        ]
        for m in markers:
            if (self.cwd / m).exists():
                self.project_files.append(m)

    # ------------------------------------------------------------------

    def greeting_line(self) -> str:
        hour = self.now.hour
        if hour < 12:
            saludo = "Buenos días"
        elif hour < 20:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"

        day_es = {
            "Monday": "lunes", "Tuesday": "martes", "Wednesday": "miércoles",
            "Thursday": "jueves", "Friday": "viernes",
            "Saturday": "sábado", "Sunday": "domingo",
        }
        day = day_es.get(self.now.strftime("%A"), self.now.strftime("%A"))
        time_str = self.now.strftime("%H:%M")
        return f"{saludo}, Pablo. {day}, {time_str}."

    def location_line(self) -> str:
        loc = str(self.cwd).replace(str(Path.home()), "~")
        if self.git_branch:
            dirty = f", {self.git_change_count} cambios" if self.git_dirty else ", limpio"
            return f"Estás en {loc} (git: {self.git_branch}{dirty})."
        return f"Estás en {loc}."

    def as_system_snippet(self) -> str:
        parts = [
            f"Directorio actual: {self.cwd}",
            f"Fecha y hora: {self.now.strftime('%A %d de %B de %Y, %H:%M')}",
        ]
        if self.git_branch:
            dirty = f" ({self.git_change_count} cambios sin commitear)" if self.git_dirty else " (limpio)"
            parts.append(f"Repositorio git: rama {self.git_branch}{dirty}")
        if self.project_files:
            parts.append(f"Archivos de proyecto detectados: {', '.join(self.project_files)}")
        return "\n".join(parts)
