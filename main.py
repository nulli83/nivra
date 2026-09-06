#!/usr/bin/env python3
"""Nivra — privat lokal mailprovider (GTK-desktopklient + lokal SMTP/IMAP)."""

from __future__ import annotations

import logging
import sys

from config import APP_NAME, IMAP_HOST, IMAP_PORT, SMTP_HOST, SMTP_PORT
from database import init_db
from gui import LoginWindow, apply_css
from imap_server import start_imap_server
from smtp_server import start_smtp_server

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(APP_NAME)


def main() -> int:
    init_db()

    smtp = start_smtp_server()
    imap = start_imap_server()
    logger.info("SMTP  %s:%s", SMTP_HOST, SMTP_PORT)
    logger.info("IMAP  %s:%s", IMAP_HOST, IMAP_PORT)

    apply_css()
    login = LoginWindow()
    login.show_all()

    try:
        Gtk.main()
    finally:
        smtp.stop()
        imap.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
