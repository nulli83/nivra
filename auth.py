"""Authentication and user accounts."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3

from config import DOMAIN, PBKDF2_ITERATIONS, SALT_BYTES
from database import get_db


USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,31}$")


def password_hash(password: str, salt: bytes | None = None) -> str:
    """Return salt$hash using PBKDF2-SHA256."""
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored salt$hash (or legacy sha256 hex)."""
    if "$" not in stored:
        # Older builds used bare sha256
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored)

    salt_hex, digest_hex = stored.split("$", 1)
    salt = bytes.fromhex(salt_hex)
    expected = password_hash(password, salt)
    return hmac.compare_digest(expected, stored)


def normalize_username(username: str) -> str:
    return username.strip().lower()


def address_for(username: str) -> str:
    return f"{normalize_username(username)}@{DOMAIN}"


def create_user(username: str, password: str) -> tuple[bool, str]:
    username = normalize_username(username)

    if not username:
        return False, "Användarnamn saknas."
    if not password:
        return False, "Lösenord saknas."
    if len(password) < 4:
        return False, "Lösenordet måste vara minst 4 tecken."
    if "@" in username:
        return False, f"Skriv bara användarnamnet, utan @{DOMAIN}."
    if not USERNAME_RE.match(username):
        return False, (
            "Användarnamnet får bara innehålla a–z, 0–9, punkt, "
            "understreck och bindestreck."
        )

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password_hash(password)),
        )
        conn.commit()
        return True, "Kontot skapades."
    except sqlite3.IntegrityError:
        return False, "Användarnamnet finns redan."
    finally:
        conn.close()


def login_user(username: str, password: str) -> bool:
    username = normalize_username(username)
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if row is None:
            return False
        return verify_password(password, row["password"])
    finally:
        conn.close()


def user_exists(username: str) -> bool:
    username = normalize_username(username)
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
