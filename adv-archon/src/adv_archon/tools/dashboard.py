"""Dashboard tool — live panel with profile, tasks, calendar, cost and memory snapshot."""

from __future__ import annotations

import datetime
import os
from pathlib import Path
from typing import Any


def build_dashboard_data() -> dict[str, Any]:
    """Collect all dashboard data and return as a structured dict."""
    data: dict[str, Any] = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "profile": "default",
        "calendar_today": [],
        "tasks_open": [],
        "tasks_overdue": [],
        "memory_snapshot": [],
        "cost": {},
        "repos": [],
    }

    # Profile
    try:
        from adv_archon.core.profiles import ProfileManager  # type: ignore
        data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
        pm = ProfileManager(data_dir)
        pm.load()
        data["profile"] = pm.active.name
    except Exception:
        pass

    # Calendar today
    try:
        from adv_archon.tools.personal import calendar_upcoming  # type: ignore
        data["calendar_today"] = calendar_upcoming(days=1, limit=5)
    except Exception:
        pass

    # Tasks
    try:
        from adv_archon.core.tasks import TaskStore  # type: ignore
        data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
        store = TaskStore(data_dir)
        data["tasks_open"] = store.list(status="open", limit=5)
        data["tasks_overdue"] = store.list(status="overdue", limit=3)
    except Exception:
        pass

    # Cost
    try:
        from adv_archon.core.costs import CostTracker  # type: ignore
        data_dir = Path(os.environ.get("ADV_ARCHON_HOME", str(Path.home() / ".adv-archon")))
        tracker = CostTracker(data_dir)
        data["cost"] = tracker.summary()
    except Exception:
        pass

    # Recent people in memory
    try:
        from adv_archon.core.memory_entities import get_entity_store  # type: ignore
        store = get_entity_store()
        data["memory_snapshot"] = store.list_persons(limit=3)
    except Exception:
        pass

    return data


def format_dashboard(data: dict[str, Any]) -> str:
    """Format dashboard data as a rich-friendly string."""
    lines = [
        f"ADV ARCHON — {data['timestamp']} — perfil: {data['profile'].upper()}",
        "=" * 60,
    ]

    # Calendar
    lines.append("\nCALENDARIO HOY")
    cal = data.get("calendar_today", [])
    if cal:
        for ev in cal:
            lines.append(f"  {ev.get('start_time', '')}  {ev.get('title', '')}")
    else:
        lines.append("  Sin eventos.")

    # Tasks
    overdue = data.get("tasks_overdue", [])
    open_tasks = data.get("tasks_open", [])
    lines.append("\nTAREAS")
    if overdue:
        for t in overdue:
            lines.append(f"  [!] {t.get('title', '')} (vencida)")
    if open_tasks:
        for t in open_tasks:
            lines.append(f"  [ ] {t.get('title', '')}")
    if not overdue and not open_tasks:
        lines.append("  Sin tareas pendientes.")

    # Cost
    cost = data.get("cost", {})
    if cost:
        total = cost.get("total_usd", 0)
        lines.append(f"\nCOSTE SESIÓN  ${total:.4f}")

    lines.append("")
    return "\n".join(lines)
