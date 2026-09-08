"""Nivra configuration."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = str(DATA_DIR / "mail.db")

DOMAIN = "nivra.local"
APP_NAME = "Nivra"
APP_TAGLINE = "Privat lokal mailprovider"

SMTP_HOST = "127.0.0.1"
SMTP_PORT = 2525
IMAP_HOST = "127.0.0.1"
IMAP_PORT = 1143

PBKDF2_ITERATIONS = 200_000
SALT_BYTES = 16
