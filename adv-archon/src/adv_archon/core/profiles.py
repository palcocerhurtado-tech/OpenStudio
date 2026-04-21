"""Profile system — work / personal / research / coding modes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


PROFILES: dict[str, "ProfileDef"] = {}


@dataclass
class ProfileDef:
    name: str
    description: str
    system_overlay: str  # appended to base system prompt
    default_mode: str = "local"  # local | cloud
    knowledge_scope: list[str] = field(default_factory=list)  # extra dirs to index
    tool_whitelist: list[str] = field(default_factory=list)  # empty = all tools
    preferred_model: str = ""  # empty = inherit from config
    auto_detect_dirs: list[str] = field(default_factory=list)  # cwd patterns

    def to_dict(self) -> dict:
        return asdict(self)


def _register(p: ProfileDef) -> ProfileDef:
    PROFILES[p.name] = p
    return p


PROFILE_DEFAULT = _register(ProfileDef(
    name="default",
    description="Asistente general polivalente.",
    system_overlay="",
))

PROFILE_WORK = _register(ProfileDef(
    name="work",
    description="Foco en productividad profesional: propuestas, clientes, proyectos.",
    system_overlay=(
        "Estás en perfil TRABAJO. Prioriza la productividad profesional. "
        "Antes de redactar documentos revisa el contexto del cliente en memoria. "
        "Sé especialmente preciso con fechas, importes y compromisos contractuales. "
        "Cuando detectes tareas accionables, propón crearlas automáticamente."
    ),
    default_mode="cloud",
    knowledge_scope=["~/Documents", "~/Desktop", "~/Proposals"],
))

PROFILE_PERSONAL = _register(ProfileDef(
    name="personal",
    description="Asistente personal: agenda, finanzas, salud, ocio.",
    system_overlay=(
        "Estás en perfil PERSONAL. Tono más distendido pero igualmente eficiente. "
        "Recuerda preferencias personales (comida, deporte, hobbies) cuando sean relevantes. "
        "Para recordatorios personales usa siempre Reminders de macOS."
    ),
    default_mode="local",
))

PROFILE_RESEARCH = _register(ProfileDef(
    name="research",
    description="Investigación profunda: búsqueda, síntesis, citación.",
    system_overlay=(
        "Estás en perfil RESEARCH. Busca siempre al menos 3 fuentes antes de concluir. "
        "Cita URLs de origen. Distingue explícitamente entre hechos verificados e inferencias. "
        "Cuando sea útil, genera un resumen estructurado con secciones y puntos clave."
    ),
    default_mode="cloud",
    knowledge_scope=["~/Documents/Research", "~/Papers"],
))

PROFILE_CODING = _register(ProfileDef(
    name="coding",
    description="Asistente de código: análisis, debug, refactor, docs.",
    system_overlay=(
        "Estás en perfil CODING. Prioriza calidad de código sobre brevedad. "
        "Muestra siempre el diff exacto de los cambios, no el archivo completo salvo petición. "
        "Detecta el lenguaje y framework del repo activo y adapta respuestas. "
        "Propón tests cuando implementes funcionalidad nueva."
    ),
    default_mode="local",
    auto_detect_dirs=["pyproject.toml", "package.json", "Cargo.toml", "go.mod", ".git"],
))


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

class ProfileManager:
    """Manages the active profile for a session."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._state_file = data_dir / "profile_state.json"
        self._active: ProfileDef = PROFILE_DEFAULT

    # ------------------------------------------------------------------
    def load(self) -> None:
        """Load persisted active profile."""
        if self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text())
                name = data.get("active", "default")
                if name in PROFILES:
                    self._active = PROFILES[name]
            except Exception:
                pass

    def save(self) -> None:
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps({"active": self._active.name}))

    # ------------------------------------------------------------------
    @property
    def active(self) -> ProfileDef:
        return self._active

    def set(self, name: str) -> ProfileDef:
        if name not in PROFILES:
            raise ValueError(f"Unknown profile '{name}'. Available: {', '.join(PROFILES)}")
        self._active = PROFILES[name]
        self.save()
        return self._active

    def auto_detect(self, cwd: Path) -> Optional[ProfileDef]:
        """Return a suggested profile based on cwd contents."""
        for fname in PROFILE_CODING.auto_detect_dirs:
            if (cwd / fname).exists():
                return PROFILE_CODING
        return None

    # ------------------------------------------------------------------
    def system_overlay(self) -> str:
        return self._active.system_overlay

    def list_all(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "description": p.description,
                "active": p.name == self._active.name,
            }
            for p in PROFILES.values()
        ]
