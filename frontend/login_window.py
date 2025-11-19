from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class LoginWindow(QWidget):
    """
    LoginWindow expects a connected ClientSocket instance:
        win = LoginWindow(client_socket)
    It will use client_socket.send(...) and client_socket.receive() to talk
    to your server.py FTP-like backend.
    """
    # Emits a dict: { "username": str, "permissions": {"read":bool,"write":bool,"delete":bool} }
    login_success = pyqtSignal(dict)

    def __init__(self, client_socket):
        super().__init__()
        self.client = client_socket

        self.setWindowTitle("LockBox FTP — Login")
        self.setFixedSize(520, 380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        title = QLabel("🔐 LockBox Login")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Authenticate using server-registered credentials")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #555;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background: white; border-radius: 10px; padding: 16px; }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)

        # Username row
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(42)
        frame_layout.addWidget(self.username_input)

        # Password row
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(42)
        frame_layout.addWidget(self.password_input)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.login_btn = QPushButton("🚀 Login")
        self.login_btn.setFixedHeight(42)
        self.login_btn.clicked.connect(self.attempt_login)
        self.login_btn.setStyleSheet(
            "background-color: #4b8df9; color: white; font-weight: bold; border-radius: 8px;"
        )
        btn_row.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(42)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setStyleSheet(
            "background-color: #e4e7ef; color: #222; border-radius: 8px;"
        )
        btn_row.addWidget(self.cancel_btn)

        frame_layout.addLayout(btn_row)
        layout.addWidget(frame)
        self.setLayout(layout)

    # -----------------------------
    # Helper: read a single server response line (already provided by client_socket)
    # -----------------------------
    def _recv_line(self):
        try:
            return self.client.receive()
        except Exception as e:
            return None

    # -----------------------------
    # Attempt login flow
    # -----------------------------
    def attempt_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Missing", "Please enter both username and password.")
            return

        # disable UI while talking to server
        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        try:
            # Send USER
            self.client.send(f"USER {user}")
            resp = self._recv_line()
            if resp is None:
                raise RuntimeError("No response from server (USER).")
            if not resp.startswith("331"):
                # server rejects username
                QMessageBox.warning(self, "Login Failed", resp)
                self._reset_buttons()
                return

            # Send PASS
            self.client.send(f"PASS {pwd}")
            resp = self._recv_line()
            if resp is None:
                raise RuntimeError("No response from server (PASS).")

            # If PASS successful, server sends "230 Logged in." then a PERMS line per your server
            if resp.startswith("230"):
                # try read the next line; in your server you send PERMS after 230
                next_line = self._recv_line()
                perms = {"read": False, "write": False, "delete": False}
                if next_line and next_line.startswith("PERMS"):
                    # parse "PERMS read=1 write=1 delete=0"
                    # safe parse
                    try:
                        parts = next_line.split()
                        for p in parts[1:]:
                            if "=" in p:
                                k, v = p.split("=", 1)
                                if k.strip() == "read":
                                    perms["read"] = bool(int(v))
                                elif k.strip() == "write":
                                    perms["write"] = bool(int(v))
                                elif k.strip() == "delete":
                                    perms["delete"] = bool(int(v))
                    except Exception:
                        # ignore parsing errors and continue with defaults
                        pass

                # success: emit username + perms
                login_data = {"username": user, "permissions": perms}
                QMessageBox.information(self, "Success", "Login successful.")
                self.login_success.emit(login_data)
                self.close()
                return

            else:
                # PASS failed — server returns 530 or other code
                QMessageBox.warning(self, "Login Failed", resp)
                self._reset_buttons()
                return

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Login error:\n{exc}")
            self._reset_buttons()
            return

    def _reset_buttons(self):
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
