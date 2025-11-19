import os
from pathlib import Path
from utils.send_file import send_file
from utils.receive_file import receive_file


class FTPCommands:
    def __init__(self, conn, addr, users_db):
        self.conn = conn
        self.addr = addr
        self.users_db = users_db  # dict of users + permissions
        self.user = None
        self.cwd: Path = None

    # -----------------------------
    # Sending helper
    # -----------------------------
    def send(self, msg: str):
        self.conn.sendall((msg + "\r\n").encode())

    # -----------------------------
    # Authentication
    # -----------------------------
    def cmd_USER(self, username):
        if username not in self.users_db:
            self.send("530 User not found")
            return

        self.user = username
        self.send("331 Username OK, need password")

    def cmd_PASS(self, password):
        if not self.user:
            self.send("530 Provide USER first")
            return

        if self.users_db[self.user]["password"] != password:
            self.send("530 Login incorrect")
            self.user = None
            return

        home = Path(self.users_db[self.user]["home_dir"]).resolve()
        if not home.exists():
            home.mkdir(parents=True, exist_ok=True)

        self.cwd = home
        self.send("230 Login successful")

    # -----------------------------
    # Permission checking
    # -----------------------------
    def require_auth(self):
        if not self.user:
            self.send("530 Not logged in")
            return False
        return True

    def has_perm(self, perm):
        return perm in self.users_db[self.user]["permissions"]

    # -----------------------------
    # PWD
    # -----------------------------
    def cmd_PWD(self):
        if not self.require_auth(): 
            return

        home = Path(self.users_db[self.user]["home_dir"]).resolve()

        if self.cwd == home:
            rel = "/"
        else:
            rel = "/" + str(self.cwd.relative_to(home)).replace("\\", "/")

        self.send(f'257 "{rel}"')

    # -----------------------------
    # CWD
    # -----------------------------
    def cmd_CWD(self, directory):
        if not self.require_auth(): 
            return

        if directory in ["", None]:
            self.send("501 Syntax: CWD <directory>")
            return

        new_dir = (self.cwd / directory).resolve()

        # prevent escaping home folder
        home = Path(self.users_db[self.user]["home_dir"]).resolve()
        if home not in new_dir.parents and new_dir != home:
            self.send("550 Access denied")
            return

        if not new_dir.exists() or not new_dir.is_dir():
            self.send("550 Directory does not exist")
            return

        self.cwd = new_dir
        self.send("250 Directory changed")

    # -----------------------------
    # LIST
    # -----------------------------
    def cmd_LIST(self):
        if not self.require_auth(): 
            return
        if not self.has_perm("read"):
            self.send("550 Permission denied")
            return

        self.send("150 Here comes directory listing")

        try:
            items = os.listdir(self.cwd)
        except Exception:
            self.send("550 Failed to list directory")
            return

        if not items:
            self.send("(empty)")
        else:
            for name in items:
                full_path = self.cwd / name
                if full_path.is_dir():
                    self.send(f"DIR 0 {name}")
                else:
                    size = full_path.stat().st_size
                    self.send(f"FILE {size} {name}")

        self.send("226 Directory send OK")

    # -----------------------------
    # RETR (download)
    # -----------------------------
    def cmd_RETR(self, filename):
        if not self.require_auth():
            return
        if not self.has_perm("read"):
            self.send("550 Permission denied")
            return

        file_path = (self.cwd / filename).resolve()
        if not file_path.exists():
            self.send("550 File does not exist")
            return

        self.send(f"150 Opening data connection for {filename}")
        send_file(self.conn, file_path)
        self.send("226 Transfer complete")

    # -----------------------------
    # STOR (upload)
    # -----------------------------
    def cmd_STOR(self, filename):
        if not self.require_auth():
            return
        if not self.has_perm("write"):
            self.send("550 Permission denied")
            return

        file_path = (self.cwd / filename).resolve()

        self.send("150 Ready to receive file")
        receive_file(self.conn, file_path)
        self.send("226 Upload complete")

    # -----------------------------
    # DELE (delete)
    # -----------------------------
    def cmd_DELE(self, filename):
        if not self.require_auth():
            return
        if not self.has_perm("delete"):
            self.send("550 Permission denied")
            return

        file_path = (self.cwd / filename).resolve()
        if not file_path.exists():
            self.send("550 File not found")
            return

        os.remove(file_path)
        self.send("250 File deleted successfully")

    # -----------------------------
    # QUIT
    # -----------------------------
    def cmd_QUIT(self):
        self.send("221 Goodbye")
        self.conn.close()
