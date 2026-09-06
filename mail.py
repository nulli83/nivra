"""Local mail operations (send / inbox / read)."""

from __future__ import annotations

from datetime import datetime

from auth import address_for, normalize_username, user_exists
from config import DOMAIN
from database import get_db


def _strip_domain(address: str) -> str:
    address = address.strip().lower()
    suffix = f"@{DOMAIN}"
    if address.endswith(suffix):
        return address[: -len(suffix)]
    if "@" in address:
        local, domain = address.rsplit("@", 1)
        if domain == DOMAIN:
            return local
        # Foreign domains not supported in v1 (localhost-only)
        return ""
    return address


def send_mail(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
) -> tuple[bool, str]:
    sender = normalize_username(sender)
    recipient = _strip_domain(recipient)

    if not recipient:
        return False, "Mottagare saknas eller är ogiltig."

    if not user_exists(recipient):
        return False, f"Mottagaren {recipient}@{DOMAIN} finns inte."

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = (subject or "").strip() or "(Inget ämne)"
    body = body or ""

    sender_addr = address_for(sender)
    recipient_addr = address_for(recipient)

    conn = get_db()
    try:
        # Recipient copy → inbox
        conn.execute(
            """
            INSERT INTO emails
                (sender, recipient, subject, body, created_at, is_read, folder)
            VALUES (?, ?, ?, ?, ?, 0, 'inbox')
            """,
            (sender_addr, recipient_addr, subject, body, now),
        )

        # Sender copy → sent
        conn.execute(
            """
            INSERT INTO emails
                (sender, recipient, subject, body, created_at, is_read, folder)
            VALUES (?, ?, ?, ?, ?, 1, 'sent')
            """,
            (sender_addr, recipient_addr, subject, body, now),
        )

        conn.commit()
        return True, "Meddelandet skickades."
    finally:
        conn.close()


def get_folder(username: str, folder: str = "inbox"):
    username = normalize_username(username)
    addr = address_for(username)

    if folder == "sent":
        where = "sender = ? AND folder = 'sent' AND deleted = 0"
        params = (addr,)
    else:
        where = "recipient = ? AND folder = ? AND deleted = 0"
        params = (addr, folder)

    conn = get_db()
    try:
        return conn.execute(
            f"""
            SELECT *
            FROM emails
            WHERE {where}
            ORDER BY id DESC
            """,
            params,
        ).fetchall()
    finally:
        conn.close()


def get_inbox(username: str):
    return get_folder(username, "inbox")


def get_sent(username: str):
    return get_folder(username, "sent")


def get_mail(mail_id: int, username: str, folder: str = "inbox"):
    username = normalize_username(username)
    addr = address_for(username)

    conn = get_db()
    try:
        if folder == "sent":
            row = conn.execute(
                """
                SELECT *
                FROM emails
                WHERE id = ? AND sender = ? AND folder = 'sent' AND deleted = 0
                """,
                (mail_id, addr),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT *
                FROM emails
                WHERE id = ? AND recipient = ? AND folder = ? AND deleted = 0
                """,
                (mail_id, addr, folder),
            ).fetchone()

        if row and folder != "sent":
            conn.execute(
                "UPDATE emails SET is_read = 1 WHERE id = ?",
                (mail_id,),
            )
            conn.commit()

        return row
    finally:
        conn.close()


def move_to_trash(mail_id: int, username: str) -> bool:
    """Soft-delete: mark as trash (foundation for later UI)."""
    username = normalize_username(username)
    addr = address_for(username)
    conn = get_db()
    try:
        cur = conn.execute(
            """
            UPDATE emails
            SET folder = 'trash', deleted = 0
            WHERE id = ?
              AND (recipient = ? OR sender = ?)
            """,
            (mail_id, addr, addr),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def search_mails(username: str, query: str, folder: str = "inbox"):
    """Simple full-text-ish search (foundation for later UI)."""
    username = normalize_username(username)
    addr = address_for(username)
    q = f"%{(query or '').strip().lower()}%"

    conn = get_db()
    try:
        if folder == "sent":
            return conn.execute(
                """
                SELECT *
                FROM emails
                WHERE sender = ?
                  AND folder = 'sent'
                  AND deleted = 0
                  AND (
                    lower(subject) LIKE ?
                    OR lower(body) LIKE ?
                    OR lower(recipient) LIKE ?
                  )
                ORDER BY id DESC
                """,
                (addr, q, q, q),
            ).fetchall()

        return conn.execute(
            """
            SELECT *
            FROM emails
            WHERE recipient = ?
              AND folder = ?
              AND deleted = 0
              AND (
                lower(subject) LIKE ?
                OR lower(body) LIKE ?
                OR lower(sender) LIKE ?
              )
            ORDER BY id DESC
            """,
            (addr, folder, q, q, q),
        ).fetchall()
    finally:
        conn.close()
