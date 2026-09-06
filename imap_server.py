"""Minimal localhost IMAP-ish skeleton for Nivra.

Full IMAP is a large protocol. This module exposes a threaded TCP
listener on 127.0.0.1 that speaks a tiny subset useful for learning
and future expansion (LOGIN, SELECT, FETCH, LOGOUT).
"""

from __future__ import annotations

import logging
import socket
import threading
from email.message import EmailMessage

from auth import login_user, normalize_username
from config import DOMAIN, IMAP_HOST, IMAP_PORT
from mail import get_folder, get_mail

logger = logging.getLogger(__name__)


def _as_rfc822(row) -> bytes:
    msg = EmailMessage()
    msg["From"] = row["sender"]
    msg["To"] = row["recipient"]
    msg["Subject"] = row["subject"]
    msg["Date"] = row["created_at"]
    msg.set_content(row["body"] or "")
    return msg.as_bytes()


class IMAPSession:
    def __init__(self, conn: socket.socket):
        self.conn = conn
        self.user: str | None = None
        self.folder = "inbox"
        self.file = conn.makefile("rwb")

    def send(self, text: str) -> None:
        self.conn.sendall((text + "\r\n").encode("utf-8"))

    def handle(self) -> None:
        self.send("* OK Nivra IMAP ready")
        while True:
            line = self.file.readline()
            if not line:
                break
            raw = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not raw:
                continue
            parts = raw.split(" ", 2)
            tag = parts[0]
            cmd = parts[1].upper() if len(parts) > 1 else ""
            args = parts[2] if len(parts) > 2 else ""

            if cmd == "CAPABILITY":
                self.send("* CAPABILITY IMAP4rev1 AUTH=PLAIN")
                self.send(f"{tag} OK CAPABILITY completed")
            elif cmd == "LOGIN":
                tokens = args.split(" ", 1)
                if len(tokens) != 2:
                    self.send(f"{tag} BAD LOGIN args")
                    continue
                user = tokens[0].strip('"')
                password = tokens[1].strip('"')
                user = normalize_username(user.split("@", 1)[0])
                if login_user(user, password):
                    self.user = user
                    self.send(f"{tag} OK LOGIN completed")
                else:
                    self.send(f"{tag} NO LOGIN failed")
            elif cmd == "SELECT":
                if not self.user:
                    self.send(f"{tag} NO not authenticated")
                    continue
                folder = args.strip().strip('"').lower() or "inbox"
                if folder in ("inbox", "sent", "trash", "drafts"):
                    self.folder = folder
                    mails = get_folder(self.user, folder)
                    self.send(f"* {len(mails)} EXISTS")
                    self.send(f"{tag} OK [READ-WRITE] SELECT completed")
                else:
                    self.send(f"{tag} NO unknown mailbox")
            elif cmd == "FETCH":
                if not self.user:
                    self.send(f"{tag} NO not authenticated")
                    continue
                # FETCH <seq> BODY[] — seq is 1-based over current folder
                seq_s = args.split(" ", 1)[0]
                try:
                    seq = int(seq_s)
                except ValueError:
                    self.send(f"{tag} BAD FETCH")
                    continue
                mails = get_folder(self.user, self.folder)
                if seq < 1 or seq > len(mails):
                    self.send(f"{tag} NO no such message")
                    continue
                # get_folder returns newest first; IMAP seq usually oldest first
                row = list(reversed(mails))[seq - 1]
                data = _as_rfc822(row)
                self.send(f"* {seq} FETCH (BODY[] {{{len(data)}}}")
                self.conn.sendall(data + b")\r\n")
                # Mark read via get_mail when inbox
                get_mail(row["id"], self.user, self.folder)
                self.send(f"{tag} OK FETCH completed")
            elif cmd == "LOGOUT":
                self.send("* BYE Nivra logging out")
                self.send(f"{tag} OK LOGOUT completed")
                break
            elif cmd == "NOOP":
                self.send(f"{tag} OK NOOP completed")
            else:
                self.send(f"{tag} BAD unknown command {cmd}")


class IMAPServerThread(threading.Thread):
    def __init__(self, host: str = IMAP_HOST, port: int = IMAP_PORT):
        super().__init__(daemon=True, name="nivra-imap")
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
            logger.info("IMAP listening on %s:%s", self.host, self.port)

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
            logger.error("IMAP server failed to start: %s", exc)
        finally:
            if self._sock is not None:
                self._sock.close()

    def _serve(self, conn: socket.socket) -> None:
        try:
            IMAPSession(conn).handle()
        except Exception:
            logger.exception("IMAP session error")
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def stop(self) -> None:
        self._stop.set()


def start_imap_server(
    host: str = IMAP_HOST,
    port: int = IMAP_PORT,
) -> IMAPServerThread:
    thread = IMAPServerThread(host, port)
    thread.start()
    return thread


# Silence unused import warning in type checkers: DOMAIN used by docs/clients
__all__ = ["start_imap_server", "IMAPServerThread", "DOMAIN"]
