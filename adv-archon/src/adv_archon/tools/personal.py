"""macOS personal connectors — Calendar, Reminders, Notes, Contacts, Mail."""

from __future__ import annotations

import datetime
import subprocess
from typing import Optional


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

def calendar_upcoming(days: int = 7, limit: int = 20) -> list[dict]:
    """Devuelve eventos del Calendario de macOS para los próximos N días."""
    now = datetime.datetime.now()
    end = now + datetime.timedelta(days=days)
    script = f"""
set startDate to (current date)
set endDate to startDate + ({days} * days)
set output to ""
tell application "Calendar"
    repeat with cal in calendars
        set evts to (every event of cal whose start date >= startDate and start date <= endDate)
        repeat with e in evts
            set t to summary of e
            set sd to start date of e
            set output to output & t & "|" & (sd as string) & "\\n"
        end repeat
    end repeat
end tell
return output
"""
    return _run_applescript_events(script, limit)


def _run_applescript_events(script: str, limit: int) -> list[dict]:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return []
        events: list[dict] = []
        for line in result.stdout.strip().splitlines():
            if "|" not in line:
                continue
            parts = line.split("|", 1)
            title = parts[0].strip()
            time_str = parts[1].strip() if len(parts) > 1 else ""
            if title:
                events.append({"title": title, "start_time": time_str})
            if len(events) >= limit:
                break
        return events
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------

def list_reminders(limit: int = 20, incomplete_only: bool = True) -> list[dict]:
    """Lista recordatorios de macOS Reminders."""
    filter_clause = "whose completion date is missing value" if incomplete_only else ""
    script = f"""
set output to ""
tell application "Reminders"
    set rems to (every reminder {filter_clause})
    repeat with r in rems
        set n to name of r
        set d to ""
        try
            set d to due date of r as string
        end try
        set output to output & n & "|" & d & "\\n"
    end repeat
end tell
return output
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10,
        )
        reminders: list[dict] = []
        for line in result.stdout.strip().splitlines()[:limit]:
            if "|" not in line:
                continue
            parts = line.split("|", 1)
            reminders.append({
                "title": parts[0].strip(),
                "due": parts[1].strip() if len(parts) > 1 else "",
            })
        return reminders
    except Exception:
        return []


def create_reminder(title: str, due_date: str = "", notes: str = "") -> dict:
    """Crea un recordatorio en macOS Reminders."""
    date_part = ""
    if due_date:
        date_part = f'\n        set due date of newReminder to date "{due_date}"'
    notes_part = ""
    if notes:
        safe_notes = notes.replace('"', '\\"')
        notes_part = f'\n        set body of newReminder to "{safe_notes}"'
    safe_title = title.replace('"', '\\"')
    script = f"""
tell application "Reminders"
    set newReminder to make new reminder with properties {{name:"{safe_title}"}}{date_part}{notes_part}
end tell
return "ok"
"""
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        return {"status": "creado", "title": title, "due": due_date}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

def list_notes(limit: int = 10) -> list[dict]:
    """Lista notas recientes de macOS Notes."""
    script = f"""
set output to ""
tell application "Notes"
    set ns to (every note)
    set i to 0
    repeat with n in ns
        if i >= {limit} then exit repeat
        set t to name of n
        set output to output & t & "\\n"
        set i to i + 1
    end repeat
end tell
return output
"""
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        notes = [{"title": l.strip()} for l in result.stdout.strip().splitlines() if l.strip()]
        return notes
    except Exception:
        return []


def create_note(title: str, content: str, folder: str = "") -> dict:
    """Crea una nota en macOS Notes."""
    safe_title = title.replace('"', '\\"')
    safe_content = content.replace('"', '\\"').replace("\n", "\\n")
    folder_part = f'in folder "{folder}" of default account' if folder else ""
    script = f"""
tell application "Notes"
    make new note {folder_part} with properties {{name:"{safe_title}", body:"{safe_content}"}}
end tell
return "ok"
"""
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        return {"status": "creada", "title": title}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------

def search_contacts(query: str) -> list[dict]:
    """Busca contactos en macOS Contacts."""
    safe_query = query.replace('"', '\\"')
    script = f"""
set output to ""
tell application "Contacts"
    set ps to (every person whose (name contains "{safe_query}"))
    repeat with p in ps
        set n to name of p
        set e to ""
        try
            set e to value of email 1 of p
        end try
        set ph to ""
        try
            set ph to value of phone 1 of p
        end try
        set output to output & n & "|" & e & "|" & ph & "\\n"
    end repeat
end tell
return output
"""
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        contacts: list[dict] = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            if parts and parts[0].strip():
                contacts.append({
                    "name": parts[0].strip(),
                    "email": parts[1].strip() if len(parts) > 1 else "",
                    "phone": parts[2].strip() if len(parts) > 2 else "",
                })
        return contacts
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Mail
# ---------------------------------------------------------------------------

def create_mail_draft(to: str, subject: str, body: str) -> dict:
    """Crea un borrador de email en macOS Mail."""
    safe_to = to.replace('"', '\\"')
    safe_subject = subject.replace('"', '\\"')
    safe_body = body.replace('"', '\\"').replace("\n", "\\n")
    script = f"""
tell application "Mail"
    set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", content:"{safe_body}", visible:true}}
    tell newMessage
        make new to recipient with properties {{address:"{safe_to}"}}
    end tell
end tell
return "ok"
"""
    try:
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        return {"status": "borrador creado", "to": to, "subject": subject}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "calendar_upcoming",
        "description": "Devuelve los próximos eventos del Calendario de macOS.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 7},
                "limit": {"type": "integer", "default": 20},
            },
        },
        "function": calendar_upcoming,
    },
    {
        "name": "list_reminders",
        "description": "Lista los recordatorios pendientes de macOS Reminders.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
                "incomplete_only": {"type": "boolean", "default": True},
            },
        },
        "function": list_reminders,
    },
    {
        "name": "create_reminder",
        "description": "Crea un recordatorio en macOS Reminders.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_date": {"type": "string", "default": ""},
                "notes": {"type": "string", "default": ""},
            },
            "required": ["title"],
        },
        "function": create_reminder,
        "requires_confirmation": True,
    },
    {
        "name": "list_notes",
        "description": "Lista las notas recientes de macOS Notes.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
        },
        "function": list_notes,
    },
    {
        "name": "create_note",
        "description": "Crea una nueva nota en macOS Notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "folder": {"type": "string", "default": ""},
            },
            "required": ["title", "content"],
        },
        "function": create_note,
        "requires_confirmation": True,
    },
    {
        "name": "search_contacts",
        "description": "Busca personas en macOS Contacts.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "function": search_contacts,
    },
    {
        "name": "create_mail_draft",
        "description": "Crea un borrador de email en macOS Mail para revisión antes de enviar.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        "function": create_mail_draft,
        "requires_confirmation": True,
    },
]
