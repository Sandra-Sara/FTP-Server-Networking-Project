#!/usr/bin/env python3
"""
Simple threaded TCP FTP-like server with per-user access control.
Supports multiple clients, read/write/delete permissions, and safe path handling.

Commands:
    USER <name>
    PASS <password>
    LIST
    PWD
    CWD <dir>
    RETR <filename>
    STOR <filename> <size>
    DELE <filename>
    QUIT
"""

import os
import socket
import threading
import sqlite3
import hashlib
import hmac
import binascii
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler
from pathlib import Path

# ==========================================================
# DATABASE + PASSWORD HELPERS
# ==========================================================

DB_FILE = "ftp_users.db"

# file-lock table to prevent race conditions
FILE_LOCKS = {}
FILE_LOCKS_LOCK = threading.Lock()


def init_user_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            can_read INTEGER DEFAULT 1,
            can_write INTEGER DEFAULT 1,
            can_delete INTEGER DEFAULT 0,
            home_dir TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def make_password_hash(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200000)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()


def verify_password(stored_hash_hex, stored_salt_hex, provided_pw):
    salt = binascii.unhexlify(stored_salt_hex)
    check_hash, _ = make_password_hash(provided_pw, salt)
    return hmac.compare_digest(stored_hash_hex, check_hash)


def add_user(username, password, home_dir, can_read=1, can_write=1, can_delete=0):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    h, salt = make_password_hash(password)
    cur.execute("""
        INSERT OR REPLACE INTO users(username,password_hash,salt,can_read,can_write,can_delete,home_dir)
        VALUES (?,?,?,?,?,?,?)
    """, (username, h, salt, can_read, can_write, can_delete, str(Path(home_dir).resolve())))
    conn.commit()
    conn.close()


def get_user_record(username):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash, salt, can_read, can_write, can_delete, home_dir FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def get_lock_for_path(path: str):
    with FILE_LOCKS_LOCK:
        if path not in FILE_LOCKS:
            FILE_LOCKS[path] = threading.Lock()
        return FILE_LOCKS[path]


def secure_join(base: Path, *parts):
    """Prevent directory traversal: ensure the result stays inside base."""
    p = base.joinpath(*parts).resolve()
    # Make sure base has trailing separator when comparing on Windows too
    base_res = str(base.resolve())
    p_str = str(p)
    if not p_str.startswith(base_res):
        raise ValueError("Forbidden path")
    return p

# ==========================================================
# HANDLER FOR EACH CLIENT
# ==========================================================


class FTPHandler(StreamRequestHandler):

    def handle(self):
        self.user = None
        self.auth = False
        self.home = None
        self.cwd = None

        self.send("220 PyFTP server ready.")

        while True:
            line = self.rfile.readline()
            if not line:
                break

            try:
                cmdline = line.decode().strip()
            except:
                self.send("500 Invalid encoding")
                continue

            if not cmdline:
                continue

            parts = cmdline.split()
            cmd = parts[0].upper()
            args = parts[1:]

            try:
                if cmd == "USER": self.cmd_USER(args)
                elif cmd == "PASS": self.cmd_PASS(args)
                elif cmd == "PWD":  self.cmd_PWD()
                elif cmd == "CWD":  self.cmd_CWD(args)
                elif cmd == "LIST": self.cmd_LIST()
                elif cmd == "RETR": self.cmd_RETR(args)
                elif cmd == "STOR": self.cmd_STOR(args)
                elif cmd == "DELE": self.cmd_DELE(args)
                elif cmd == "QUIT":
                    self.send("221 Goodbye.")
                    break
                else:
                    self.send("502 Command not implemented.")
            except Exception as e:
                # never leak internal types, but send message
                self.send(f"550 {str(e)}")

    def send(self, msg):
        self.wfile.write((msg + "\r\n").encode())

    def require_auth(self):
        if not self.auth:
            self.send("530 Not logged in.")
            raise PermissionError()

    # ======================================================
    # FTP COMMANDS
    # ======================================================

    def cmd_USER(self, args):
        if len(args) != 1:
            self.send("501 Syntax: USER <name>")
            return
        self.user = args[0]
        self.send("331 Username OK, need password.")

    def cmd_PASS(self, args):
        if self.user is None:
            self.send("503 Send USER first.")
            return

        if len(args) != 1:
            self.send("501 Syntax: PASS <password>")
            return

        rec = get_user_record(self.user)
        if rec is None:
            self.send("530 Invalid user/pass.")
            return

        username, pw_hash, salt, can_read, can_write, can_delete, home_dir = rec

        if not verify_password(pw_hash, salt, args[0]):
            self.send("530 Invalid user/pass.")
            return

        # authenticated
        self.auth = True
        self.permissions = {
            "read": bool(can_read),
            "write": bool(can_write),
            "delete": bool(can_delete)
        }
        self.home = Path(home_dir).resolve()
        self.cwd = self.home
        Path(self.home).mkdir(parents=True, exist_ok=True)

        # helpful debug in server console (optional)
        # print(f"[DEBUG] User '{self.user}' home: {self.home}")

        self.send("230 Logged in.")

    def cmd_PWD(self):
        self.require_auth()
        if self.cwd == self.home:
            rel = "/"
        else:
            rel = "/" + str(self.cwd.relative_to(self.home)).replace("\\", "/")
        self.send(f'257 "{rel}"')

    def cmd_CWD(self, args):
        self.require_auth()
        if len(args) != 1:
            self.send("501 Syntax: CWD <dir>")
            return

        target = args[0]
        # allow 'cwd /' to return to home
        if target == "/" or target == "\\":
            self.cwd = self.home
            self.send("250 Directory changed.")
            return

        try:
            newpath = secure_join(self.home, target)
        except:
            self.send("550 Invalid path.")
            return

        if not newpath.exists() or not newpath.is_dir():
            self.send("550 Directory not found.")
            return

        self.cwd = newpath
        self.send("250 Directory changed.")

    def cmd_LIST(self):
        self.require_auth()
        if not self.permissions.get("read", False):
            self.send("550 Permission denied.")
            return

        self.send("150 Listing directory:")

        try:
            items = sorted(self.cwd.iterdir(), key=lambda p: p.name)
        except Exception:
            self.send("550 Failed to list directory.")
            return

        if not items:
            self.send("(empty)")
        else:
            for item in items:
                size = item.stat().st_size if item.is_file() else 0
                t = "DIR" if item.is_dir() else "FILE"
                # clearer, consistent formatting
                self.send(f"{t} {size} {item.name}")

        self.send("226 Done.")

    def cmd_RETR(self, args):
        self.require_auth()
        if not self.permissions.get("read", False):
            self.send("550 Permission denied.")
            return

        if len(args) != 1:
            self.send("501 Syntax: RETR <file>")
            return

        # use cwd as base for file retrieval
        try:
            path = secure_join(self.cwd, args[0])
        except:
            self.send("550 Invalid path.")
            return

        if not path.exists() or not path.is_file():
            self.send("550 File not found.")
            return

        lock = get_lock_for_path(str(path))
        with lock:
            size = path.stat().st_size
            self.send(f"150 {size}")
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

            # follow with an empty line and final code
            self.send("")
            self.send("226 Transfer complete.")

    def cmd_STOR(self, args):
        self.require_auth()
        if not self.permissions.get("write", False):
            self.send("550 Permission denied.")
            return

        if len(args) != 2:
            self.send("501 Syntax: STOR <filename> <size>")
            return

        fname, size_s = args
        try:
            size = int(size_s)
        except:
            self.send("501 Invalid size.")
            return

        try:
            path = secure_join(self.cwd, fname)
        except:
            self.send("550 Invalid path.")
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        lock = get_lock_for_path(str(path))

        with lock:
            self.send("150 Ready to receive.")
            remain = size

            with open(path, "wb") as f:
                while remain > 0:
                    chunk = self.request.recv(min(8192, remain))
                    if not chunk:
                        break
                    f.write(chunk)
                    remain -= len(chunk)

            if remain != 0:
                # incomplete transfer: remove partial file
                try:
                    path.unlink(missing_ok=True)
                except Exception:
                    pass
                self.send("426 Transfer aborted.")
                return

            self.send("226 Transfer complete.")

    def cmd_DELE(self, args):
        self.require_auth()
        if not self.permissions.get("delete", False):
            self.send("550 Permission denied.")
            return

        if len(args) != 1:
            self.send("501 Syntax: DELE <file>")
            return

        try:
            path = secure_join(self.cwd, args[0])
        except:
            self.send("550 Invalid path.")
            return

        if not path.exists() or not path.is_file():
            self.send("550 File not found.")
            return

        lock = get_lock_for_path(str(path))
        with lock:
            path.unlink()
            self.send("250 File deleted.")

# ==========================================================
# SERVER BOOTSTRAP
# ==========================================================


class ThreadedFTPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True


def run_server(host="0.0.0.0", port=2121):
    init_user_db()
    srv = ThreadedFTPServer((host, port), FTPHandler)
    print(f"Server running on {host}:{port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        srv.shutdown()
        srv.server_close()


# Optional helper to create default users
def create_sample_users():
    home = Path("ftp_homes")
    home.mkdir(exist_ok=True)
    add_user("alice", "alicepwd", str(home / "alice"), can_read=1, can_write=1, can_delete=0)
    add_user("bob", "bobpwd", str(home / "bob"),   can_read=1, can_write=0, can_delete=0)
    add_user("admin", "adminpwd", str(home / "admin"), can_read=1, can_write=1, can_delete=1)
    print("Sample users created.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--init":
        init_user_db()
        create_sample_users()
    else:
        run_server()
