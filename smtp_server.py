"""Minimal localhost SMTP server for Nivra (stdlib sockets only).

Binds only to 127.0.0.1. Speaks enough SMTP for local delivery:
EHLO/HELO, MAIL FROM, RCPT TO, DATA, RSET, NOOP, QUIT.
"""

from __future__ import annotations

import email
import logging
import socket
import threading
from email.utils import parseaddr

from auth import normalize_username, user_exists
from config import DOMAIN, SMTP_HOST, SMTP_PORT
from mail import send_mail

logger = logging.getLogger(__name__)


def _extract_smtp_address(raw: str) -> str:
    """Pull an email address out of MAIL FROM / RCPT TO arguments."""
    text = (raw or "").strip()
    if "<" in text and ">" in text:
        text = text[text.index("<") + 1 : text.index(">")].strip()
    else:
        # Drop ESMTP params: user@host SIZE=123
        text = text.split()[0] if text else ""
    return text.strip().strip("<>").lower()


def _local_user(address: str) -> str | None:
    addr = _extract_smtp_address(address)
    if not addr:
        _, parsed = parseaddr(address)
        addr = (parsed or "").strip().lower()
    if not addr:
        return None
    if "@" not in addr:
        local = normalize_username(addr)
        return local if user_exists(local) else None
    local, domain = addr.rsplit("@", 1)
    if domain != DOMAIN:
        return None
    local = normalize_username(local)
    return local if user_exists(local) else None

def _extract_body_and_subject(data: bytes) -> tuple[str, str]:
    subject = "(Inget ämne)"
    body = ""
    try:
        msg = email.message_from_bytes(data)
    except Exception:
        return subject, data.decode("utf-8", errors="replace")

    subject = msg.get("Subject") or subject
    payload = msg.get_payload(decode=True)
    if payload is None:
        raw = msg.get_payload()
        body = raw if isinstance(raw, str) else str(raw)
    else:
        charset = msg.get_content_charset() or "utf-8"
        body = payload.decode(charset, errors="replace")
    return subject, body


class SMTPSession:
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.file = conn.makefile("rwb")
        self.mail_from: str | None = None
        self.rcpt_to: list[str] = []
        self.reset_transaction()

    def reset_transaction(self) -> None:
        self.mail_from = None
        self.rcpt_to = []

    def send(self, line: str) -> None:
        self.conn.sendall((line + "\r\n").encode("utf-8"))

    def handle(self) -> None:
        self.send("220 nivra.local ESMTP Nivra ready")
        while True:
            raw = self.file.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                continue

            cmd, _, arg = line.partition(" ")
            cmd = cmd.upper()
            arg = arg.strip()

            if cmd in ("HELO", "EHLO"):
                if cmd == "EHLO":
                    self.send(f"250-{DOMAIN} Hello")
                    self.send("250-SIZE 10485760")
                    self.send("250-8BITMIME")
                    self.send("250 OK")
                else:
                    self.send(f"250 {DOMAIN} Hello")
            elif cmd == "MAIL":
                # MAIL FROM:<user@domain>
                addr = arg
                if addr.upper().startswith("FROM:"):
                    addr = addr[5:].strip()
                user = _local_user(addr)
                if user is None:
                    self.send("550 Sender not allowed")
                else:
                    self.mail_from = user
                    self.rcpt_to = []
                    self.send("250 OK")
            elif cmd == "RCPT":
                addr = arg
                if addr.upper().startswith("TO:"):
                    addr = addr[3:].strip()
                user = _local_user(addr)
                if self.mail_from is None:
                    self.send("503 Need MAIL FROM first")
                elif user is None:
                    self.send("550 No such user")
                else:
                    self.rcpt_to.append(user)
                    self.send("250 OK")
            elif cmd == "DATA":
                if self.mail_from is None or not self.rcpt_to:
                    self.send("503 Need MAIL FROM and RCPT TO")
                    continue
                self.send("354 End data with <CR><LF>.<CR><LF>")
                chunks: list[bytes] = []
                while True:
                    data_line = self.file.readline()
                    if not data_line:
                        break
                    if data_line == b".\r\n":
                        break
                    # Dot-stuffing
                    if data_line.startswith(b".."):
                        data_line = data_line[1:]
                    chunks.append(data_line)
                subject, body = _extract_body_and_subject(b"".join(chunks))
                for recipient in self.rcpt_to:
                    ok, message = send_mail(
                        self.mail_from, recipient, subject, body
                    )
                    if not ok:
                        logger.warning("SMTP deliver failed: %s", message)
                self.reset_transaction()
                self.send("250 OK queued")
            elif cmd == "RSET":
                self.reset_transaction()
                self.send("250 OK")
            elif cmd == "NOOP":
                self.send("250 OK")
            elif cmd == "QUIT":
                self.send("221 Bye")
                break
            else:
                self.send(f"502 Command not implemented")


class SMTPServerThread(threading.Thread):
    """Background thread that runs the localhost SMTP server."""

    def __init__(self, host: str = SMTP_HOST, port: int = SMTP_PORT):
        super().__init__(daemon=True, name="nivra-smtp")
        self.host = host
        self.port = port
        self._stop = threading.Event()
        self._sock: socket.socket | None = None

    def run(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind((self.host, self.port))
            self._sock.listen(5)
            self._sock.settimeout(0.5)
            logger.info("SMTP listening on %s:%s", self.host, self.port)

            while not self._stop.is_set():
                try:
                    conn, _addr = self._sock.accept()
                except socket.timeout:
                    continue
                threading.Thread(
                    target=self._serve,
                    args=(conn,),
                    daemon=True,
                ).start()
        except OSError as exc:
            logger.error("SMTP server failed to start: %s", exc)
        finally:
            if self._sock is not None:
                self._sock.close()

    def _serve(self, conn: socket.socket) -> None:
        try:
            SMTPSession(conn).handle()
        except Exception:
            logger.exception("SMTP session error")
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def stop(self) -> None:
        self._stop.set()


def start_smtp_server(
    host: str = SMTP_HOST,
    port: int = SMTP_PORT,
) -> SMTPServerThread:
    thread = SMTPServerThread(host, port)
    thread.start()
    return thread
