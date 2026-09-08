#!/usr/bin/env python3
"""Nivra — privat lokal mailprovider (tkinter-klient + lokal SMTP/IMAP)."""

from __future__ import annotations

import logging
import sys

from dpi import enable_dpi_awareness

# Must run before any Tk window is created, or Windows blurs the UI.
enable_dpi_awareness()

from config import APP_NAME, IMAP_HOST, IMAP_PORT, SMTP_HOST, SMTP_PORT  # noqa: E402
from database import init_db  # noqa: E402
from gui import LoginWindow  # noqa: E402
from imap_server import start_imap_server  # noqa: E402
from smtp_server import start_smtp_server  # noqa: E402


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

    login = LoginWindow()
    try:
        login.mainloop()
    finally:
        smtp.stop()
        imap.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
