# Fase 3 — Guía de integración

Aplica estos cambios sobre el código ya existente en `~/ADV ARCHON/`.

---

## 1. Copiar archivos nuevos

```bash
cd ~/ADV\ ARCHON

# Copia los archivos nuevos de Fase 3
cp path/to/adv-archon/src/adv_archon/core/profiles.py          src/adv_archon/core/
cp path/to/adv-archon/src/adv_archon/core/automations.py       src/adv_archon/core/
cp path/to/adv-archon/src/adv_archon/core/memory_entities.py   src/adv_archon/core/
cp path/to/adv-archon/src/adv_archon/tools/notion.py            src/adv_archon/tools/
cp path/to/adv-archon/src/adv_archon/tools/obsidian.py          src/adv_archon/tools/
cp path/to/adv-archon/src/adv_archon/tools/gmail.py             src/adv_archon/tools/
cp path/to/adv-archon/src/adv_archon/tools/dashboard.py        src/adv_archon/tools/
```

---

## 2. Añadir dependencias en `pyproject.toml`

Dentro de `[project] dependencies = [...]`, agrega:

```toml
# Fase 3
"notion-client>=2.2.1",    # (opcional, alternativa a urllib nativo)
# Gmail usa imaplib/smtplib de stdlib — no requiere dependencia extra
```

**No se necesitan dependencias adicionales**: Notion usa `urllib` nativo, Obsidian lee archivos locales, Gmail usa `imaplib`/`smtplib` de stdlib.

---

## 3. Añadir variables en `~/.adv-archon/.env`

```env
# Notion (obtén el token en notion.so/my-integrations)
NOTION_TOKEN=secret_xxxxxxxxxxxx

# Obsidian (ruta al vault local)
OBSIDIAN_VAULT_PATH=~/Documents/ObsidianVault

# Gmail (genera app password en myaccount.google.com → Security → App passwords)
GMAIL_ADDRESS=tu@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

## 4. Parche en `src/adv_archon/core/config.py`

Añade al final de la clase `AdvArchonConfig` (o donde estén los campos de config):

```python
# Fase 3
profile: str = "default"
notion_token: str = ""
obsidian_vault_path: str = ""
gmail_address: str = ""
gmail_app_password: str = ""
auto_brief_hour: int = 8
auto_brief_minute: int = 30
watch_repos: list[str] = field(default_factory=list)
```

Y en el método que carga `.env`, añade:

```python
self.notion_token      = os.environ.get("NOTION_TOKEN", "")
self.obsidian_vault_path = os.environ.get("OBSIDIAN_VAULT_PATH", "")
self.gmail_address     = os.environ.get("GMAIL_ADDRESS", "")
self.gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
```

---

## 5. Parche en `src/adv_archon/core/agent.py`

En el método que registra tools (normalmente `_build_tools()` o similar), añade:

```python
# Fase 3 tools
from adv_archon.tools.notion          import TOOL_DEFINITIONS as NOTION_TOOLS
from adv_archon.tools.obsidian        import TOOL_DEFINITIONS as OBSIDIAN_TOOLS
from adv_archon.tools.gmail            import TOOL_DEFINITIONS as GMAIL_TOOLS
from adv_archon.core.automations       import TOOL_DEFINITIONS as AUTOMATION_TOOLS
from adv_archon.core.memory_entities   import TOOL_DEFINITIONS as ENTITY_TOOLS

all_tools = [
    *NOTION_TOOLS,
    *OBSIDIAN_TOOLS,
    *GMAIL_TOOLS,
    *AUTOMATION_TOOLS,
    *ENTITY_TOOLS,
    # ...los tools existentes ya registrados...
]
```

En el system prompt que se inyecta al agente, incluir el overlay del perfil activo:

```python
from adv_archon.core.profiles import ProfileManager

profile_manager = ProfileManager(self._data_dir)
profile_manager.load()
profile_overlay = profile_manager.system_overlay()
# Añade profile_overlay al final del system prompt
```

---

## 6. Parche en `src/adv_archon/ui/commands.py`

Añade estos slash commands al diccionario/dispatcher de comandos:

```python
from adv_archon.core.profiles      import PROFILES, ProfileManager
from adv_archon.tools.dashboard     import build_dashboard_data, format_dashboard
from adv_archon.core.memory_entities import get_entity_store

# /profile
def cmd_profile(args: str, ctx) -> str:
    pm = ProfileManager(ctx.data_dir)
    pm.load()
    if not args.strip():
        profiles = pm.list_all()
        lines = ["Perfiles disponibles:"]
        for p in profiles:
            marker = "→" if p["active"] else " "
            lines.append(f"  {marker} {p['name']} — {p['description']}")
        return "\n".join(lines)
    try:
        active = pm.set(args.strip())
        return f"Perfil cambiado a: {active.name}"
    except ValueError as e:
        return str(e)

# /dashboard
def cmd_dashboard(args: str, ctx) -> str:
    data = build_dashboard_data()
    return format_dashboard(data)

# /weekly
def cmd_weekly(args: str, ctx) -> str:
    from adv_archon.core.automations import build_weekly_review
    repos = args.strip() if args.strip() else ""
    return build_weekly_review(include_repos=repos)

# /people  (lista personas en memoria)
def cmd_people(args: str, ctx) -> str:
    store = get_entity_store(ctx.data_dir)
    if args.strip():
        results = store.search_persons(args.strip())
    else:
        results = store.list_persons(limit=10)
    if not results:
        return "Sin personas en memoria."
    lines = []
    for p in results:
        lines.append(f"- **{p['name']}** ({p.get('company','')}) {p.get('email','')}")
        if p.get("notes"):
            lines.append(f"  {p['notes'][:80]}")
    return "\n".join(lines)

# /projects
def cmd_projects(args: str, ctx) -> str:
    store = get_entity_store(ctx.data_dir)
    projects = store.list_projects(status="active")
    if not projects:
        return "Sin proyectos activos en memoria."
    lines = []
    for p in projects:
        deadline = f" (deadline: {p['deadline']})" if p.get("deadline") else ""
        lines.append(f"- **{p['name']}** [{p['status']}]{deadline}")
        if p.get("notes"):
            lines.append(f"  {p['notes'][:80]}")
    return "\n".join(lines)

# Registro en el dispatcher:
COMMANDS = {
    # ...comandos existentes...
    "profile":    cmd_profile,
    "dashboard":  cmd_dashboard,
    "weekly":     cmd_weekly,
    "people":     cmd_people,
    "projects":   cmd_projects,
}
```

---

## 7. Parche en `src/adv_archon/main.py`

Añade estos subcomandos en el entrypoint CLI (junto a `daily`, `tasks`, etc.):

```python
# adv-archon weekly
if args.command == "weekly":
    from adv_archon.core.automations import build_weekly_review
    repos = ",".join(args.repos) if hasattr(args, "repos") and args.repos else ""
    print(build_weekly_review(include_repos=repos))
    return

# adv-archon profile [name]
if args.command == "profile":
    from adv_archon.core.profiles import ProfileManager
    pm = ProfileManager(data_dir)
    pm.load()
    if hasattr(args, "name") and args.name:
        pm.set(args.name)
        print(f"Perfil activo: {args.name}")
    else:
        for p in pm.list_all():
            marker = "→" if p["active"] else " "
            print(f"  {marker} {p['name']} — {p['description']}")

# adv-archon watch-repo <path>  (llamado por launchd)
if args.command == "watch-repo":
    from adv_archon.core.automations import check_repo_changes
    result = check_repo_changes(args.repo_path)
    if result.get("status") == "cambios":
        print(f"Cambios en {args.repo_path}:")
        for c in result.get("commits", []):
            print(f"  - {c}")
    return
```

---

## 8. Auto-detect de perfil al arrancar

En `src/adv_archon/ui/repl.py`, después de detectar el cwd y git:

```python
from adv_archon.core.profiles import ProfileManager

pm = ProfileManager(data_dir)
pm.load()
suggested = pm.auto_detect(Path.cwd())
if suggested and suggested.name != pm.active.name:
    console.print(f"[dim]Perfil sugerido para este directorio: {suggested.name} (/profile {suggested.name} para activar)[/dim]")
```

---

## 9. Reinstalar tras los cambios

```bash
cd ~/ADV\ ARCHON
uv pip install -e .
# o bien reinstalar globalmente:
uv tool install . --force
```

---

## 10. Tests de Fase 3

```bash
cd ~/ADV\ ARCHON
pytest tests/test_phase3.py -v
```

Copia también el archivo de tests:

```bash
cp path/to/adv-archon/tests/test_phase3.py tests/
```

---

## Resumen de nuevas capacidades

| Comando / Petición natural | Qué hace |
|---|---|
| `/profile work` | Activa el perfil de trabajo |
| `/dashboard` | Panel con calendario, tareas y coste |
| `/weekly` | Revisión semanal |
| `/people Acme` | Busca personas relacionadas con Acme |
| `/projects` | Lista proyectos activos |
| "busca en mis notas de Obsidian sobre X" | `search_obsidian(X)` |
| "crea una página en Notion con este resumen" | `create_notion_page(...)` |
| "léeme los últimos emails de Juan" | `search_email("from:Juan")` |
| "recuerda que María es la CTO de Acme" | `remember_person(...)` |
| "anota que decidimos usar PostgreSQL porque..." | `log_decision(...)` |
| "instala el daily brief automático a las 8:30" | `install_daily_brief_launchd(8,30)` |
| "monitoriza el repo quantbot cada 30 minutos" | `install_repo_watcher_launchd(...)` |
