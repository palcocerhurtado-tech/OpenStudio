"""Gmail connector — IMAP read + SMTP send using app passwords."""

from __future__ import annotations

import email
import imaplib
import os
import smtplib
import textwrap
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parsedate_to_datetime
from typing import Optional


class GmailError(Exception):
    pass


def _creds() -> tuple[str, str]:
    addr = os.environ.get("GMAIL_ADDRESS", "")
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not addr or not pwd:
        raise GmailError(
            "Credenciales de Gmail no configuradas. "
            "Añade GMAIL_ADDRESS y GMAIL_APP_PASSWORD a ~/.adv-archon/.env. "
            "Genera la app password en: myaccount.google.com → Security → App passwords."
        )
    return addr, pwd


# ---------------------------------------------------------------------------
# IMAP helpers
# ---------------------------------------------------------------------------

def _imap_connect() -> imaplib.IMAP4_SSL:
    addr, pwd = _creds()
    try:
        conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        conn.login(addr, pwd)
        return conn
    except imaplib.IMAP4.error as e:
        raise GmailError(f"Error al conectar con Gmail IMAP: {e}") from e


def _decode_header_value(raw: str) -> str:
    parts = email.header.decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _extract_body(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


def _parse_message(raw_data: bytes, uid: str) -> dict:
    msg = email.message_from_bytes(raw_data)
    subject = _decode_header_value(msg.get("Subject", ""))
    sender = _decode_header_value(msg.get("From", ""))
    date_str = msg.get("Date", "")
    date = ""
    if date_str:
        try:
            date = parsedate_to_datetime(date_str).isoformat()
        except Exception:
            date = date_str
    body = _extract_body(msg)
    return {
        "uid": uid,
        "subject": subject,
        "from": sender,
        "date": date,
        "body_preview": body[:400].replace("\n", " ").strip(),
        "body": body,
    }


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def list_inbox(limit: int = 10, unread_only: bool = False) -> list[dict]:
    """Return recent messages from Gmail inbox."""
    conn = _imap_connect()
    try:
        conn.select("INBOX")
        criteria = "UNSEEN" if unread_only else "ALL"
        _, data = conn.uid("search", None, criteria)
        uids = data[0].split()
        uids = uids[-limit:]  # most recent last
        uids.reverse()
        messages: list[dict] = []
        for uid in uids:
            _, raw = conn.uid("fetch", uid, "(RFC822)")
            if raw and raw[0]:
                msg_data = raw[0][1]
                if isinstance(msg_data, bytes):
                    m = _parse_message(msg_data, uid.decode())
                    del m["body"]  # summary only
                    messages.append(m)
        return messages
    finally:
        conn.logout()


def search_email(query: str, limit: int = 10) -> list[dict]:
    """Search Gmail using IMAP search. Supports Gmail-style queries."""
    conn = _imap_connect()
    try:
        conn.select("INBOX")
        # Gmail supports X-GM-RAW for full Gmail search syntax
        try:
            _, data = conn.uid("search", None, f'X-GM-RAW "{query}"')
        except imaplib.IMAP4.error:
            # Fallback: search subject and body separately
            q = query.replace('"', "")
            _, data = conn.uid("search", None, f'OR SUBJECT "{q}" BODY "{q}"')
        uids = data[0].split()
        uids = uids[-limit:]
        uids.reverse()
        messages: list[dict] = []
        for uid in uids:
            _, raw = conn.uid("fetch", uid, "(RFC822)")
            if raw and raw[0]:
                msg_data = raw[0][1]
                if isinstance(msg_data, bytes):
                    m = _parse_message(msg_data, uid.decode())
                    del m["body"]
                    messages.append(m)
        return messages
    finally:
        conn.logout()


def read_email(uid: str) -> dict:
    """Read the full content of a specific email by UID."""
    conn = _imap_connect()
    try:
        conn.select("INBOX")
        _, raw = conn.uid("fetch", uid.encode(), "(RFC822)")
        if not raw or not raw[0]:
            raise GmailError(f"Mensaje {uid} no encontrado")
        msg_data = raw[0][1]
        if not isinstance(msg_data, bytes):
            raise GmailError("Respuesta inesperada del servidor IMAP")
        return _parse_message(msg_data, uid)
    finally:
        conn.logout()


def send_email(to: str, subject: str, body: str, cc: str = "", html: bool = False) -> dict:
    """Send an email via Gmail SMTP."""
    addr, pwd = _creds()
    msg = MIMEMultipart("alternative")
    msg["From"] = addr
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if html:
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))
    recipients = [to] + ([cc] if cc else [])
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(addr, pwd)
            server.sendmail(addr, recipients, msg.as_string())
        return {"status": "sent", "to": to, "subject": subject}
    except smtplib.SMTPException as e:
        raise GmailError(f"Error al enviar email: {e}") from e


def create_draft_email(to: str, subject: str, body: str) -> dict:
    """Return a formatted draft without sending — for review before send."""
    preview = textwrap.dedent(f"""
    BORRADOR DE EMAIL
    -----------------
    Para: {to}
    Asunto: {subject}

    {body}
    """).strip()
    return {"draft": preview, "to": to, "subject": subject, "body": body}


def mark_as_read(uid: str) -> None:
    """Mark a message as read."""
    conn = _imap_connect()
    try:
        conn.select("INBOX")
        conn.uid("store", uid.encode(), "+FLAGS", "\\Seen")
    finally:
        conn.logout()


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "list_inbox",
        "description": "Lista emails recientes del inbox de Gmail.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "unread_only": {"type": "boolean", "default": False},
            },
        },
        "function": list_inbox,
    },
    {
        "name": "search_email",
        "description": "Busca emails en Gmail. Admite operadores tipo 'from:x subject:y'.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        "function": search_email,
    },
    {
        "name": "read_email",
        "description": "Lee el contenido completo de un email por su UID.",
        "parameters": {
            "type": "object",
            "properties": {"uid": {"type": "string"}},
            "required": ["uid"],
        },
        "function": read_email,
    },
    {
        "name": "send_email",
        "description": "Envía un email desde la cuenta de Gmail configurada. SIEMPRE pide confirmación antes de llamar.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "cc": {"type": "string", "default": ""},
            },
            "required": ["to", "subject", "body"],
        },
        "function": send_email,
        "requires_confirmation": True,
    },
    {
        "name": "create_draft_email",
        "description": "Crea un borrador de email para revisión, sin enviarlo.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        "function": create_draft_email,
    },
]
