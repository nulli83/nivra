#!/usr/bin/env python3
"""Headless smoke tests for auth + mail (no GTK display required)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Use a temp DB so we never touch the real mailbox during tests
TMP = tempfile.mkdtemp(prefix="nivra-test-")
os.environ.setdefault("NIVRA_TEST", "1")

import config  # noqa: E402

config.DB_FILE = str(Path(TMP) / "mail.db")

from auth import create_user, login_user  # noqa: E402
from database import init_db  # noqa: E402
from mail import get_inbox, get_mail, get_sent, send_mail  # noqa: E402


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    init_db()

    ok, msg = create_user("alice", "secret")
    expect(ok, msg)
    ok, msg = create_user("bob", "secret")
    expect(ok, msg)
    ok, msg = create_user("alice", "x")
    expect(not ok, "duplicate should fail")

    expect(login_user("alice", "secret"), "alice login")
    expect(not login_user("alice", "wrong"), "bad password")

    ok, msg = send_mail("alice", "bob@nivra.local", "Hej", "Hej Bob!")
    expect(ok, msg)

    inbox = get_inbox("bob")
    expect(len(inbox) == 1, "bob should have 1 mail")
    expect(inbox[0]["subject"] == "Hej", "subject")
    expect(inbox[0]["is_read"] == 0, "unread")

    mail = get_mail(inbox[0]["id"], "bob")
    expect(mail is not None, "open mail")
    expect(mail["body"] == "Hej Bob!", "body")

    inbox2 = get_inbox("bob")
    expect(inbox2[0]["is_read"] == 1, "marked read")

    sent = get_sent("alice")
    expect(len(sent) == 1, "alice sent folder")

    ok, msg = send_mail("alice", "nobody", "x", "y")
    expect(not ok, "unknown recipient")

    print("OK — all smoke tests passed")
    print(f"temp db: {config.DB_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
