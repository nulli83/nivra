#!/usr/bin/env python3
"""SMTP + IMAP integration smoke test (localhost only)."""

from __future__ import annotations

import socket
import smtplib
import sys
import tempfile
import time
from email.message import EmailMessage
from pathlib import Path

# Patch DB path before importing app modules that open the DB.
import config

TMP = tempfile.mkdtemp(prefix="nivra-srv-")
config.DB_FILE = str(Path(TMP) / "mail.db")
config.SMTP_PORT = 2526
config.IMAP_PORT = 1144

from auth import create_user  # noqa: E402
from database import init_db  # noqa: E402
from imap_server import start_imap_server  # noqa: E402
from mail import get_inbox  # noqa: E402
from smtp_server import start_smtp_server  # noqa: E402


def main() -> int:
    init_db()
    assert create_user("alice", "pass")[0]
    assert create_user("bob", "pass")[0]

    smtp = start_smtp_server(config.SMTP_HOST, config.SMTP_PORT)
    imap = start_imap_server(config.IMAP_HOST, config.IMAP_PORT)
    time.sleep(0.4)

    try:
        msg = EmailMessage()
        msg["From"] = "alice@nivra.local"
        msg["To"] = "bob@nivra.local"
        msg["Subject"] = "SMTP test"
        msg.set_content("via smtp")
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=5) as client:
            client.send_message(msg)

        time.sleep(0.2)
        rows = get_inbox("bob")
        assert len(rows) == 1, rows
        assert rows[0]["subject"] == "SMTP test"
        assert "via smtp" in rows[0]["body"]

        sock = socket.create_connection(
            (config.IMAP_HOST, config.IMAP_PORT), timeout=3
        )
        f = sock.makefile("rwb")
        greet = f.readline().decode()
        assert "OK" in greet, greet
        sock.sendall(b'a1 LOGIN bob pass\r\n')
        assert b"OK LOGIN" in f.readline()
        sock.sendall(b'a2 SELECT INBOX\r\n')
        exists = f.readline().decode()
        assert "1 EXISTS" in exists, exists
        f.readline()  # OK SELECT
        sock.sendall(b'a3 LOGOUT\r\n')
        f.readline()
        f.readline()
        sock.close()

        print("OK — SMTP/IMAP integration passed")
        return 0
    finally:
        smtp.stop()
        imap.stop()


if __name__ == "__main__":
    sys.exit(main())
