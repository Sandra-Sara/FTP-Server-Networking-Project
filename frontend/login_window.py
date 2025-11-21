# frontend/login_window.py
#!/usr/bin/env python3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox, QHBoxLayout, QCheckBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor

class LoginWindow(QWidget):
    """
    Modern, attractive Login window compatible with your ClientSocket.

    Constructor:
        win = LoginWindow(client_socket)

    Signals:
        login_success (dict) -> emitted with {"username": str, "permissions": {"read":bool,"write":bool,"delete":bool}}
        log_event (str)     -> emitted with human-readable log lines for the LogWindow
    """
    login_success = pyqtSignal(dict)
    log_event = pyqtSignal(str)

    def __init__(self, client):
        super().__init__()
        self.client = client  # instance of ClientSocket (connected)
        self.setWindowTitle("LockBox FTP — Secure Login")
        self.setFixedSize(920, 700)

        # high-level style (gradient background)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eef9ff, stop:1 #d7f0ff);
                font-family: "Segoe UI", Arial, sans-serif;
            }
        """)

        self._build_ui()

    # ---------------- UI ----------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(18)
        root.setAlignment(Qt.AlignTop)

        # Title
        title = QLabel("🔐 LockBox FTP")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 34, QFont.Bold))
        title.setStyleSheet("color: #063b57;")
        root.addWidget(title)

        subtitle = QLabel("Secure, modern file transfers — sign in to manage your files")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #1f5166;")
        root.addWidget(subtitle)

        root.addSpacing(10)

        # Center card container (white card)
        hbox = QHBoxLayout()
        hbox.addStretch(1)

        card = QFrame()
        card.setFixedWidth(520)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
                border: 1px solid #d6e7f2;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        # Card title
        card_title = QLabel("Sign in to LockBox")
        card_title.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
        card_title.setStyleSheet("color: #083b52;")
        card_title.setAlignment(Qt.AlignLeft)
        card_layout.addWidget(card_title)

        card_desc = QLabel("Enter credentials registered in the server. Passwords are verified by the server.")
        card_desc.setWordWrap(True)
        card_desc.setStyleSheet("color: #4b6b78;")
        card_layout.addWidget(card_desc)

        card_layout.addSpacing(6)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(44)
        self.username_input.setStyleSheet(self._input_style())
        card_layout.addWidget(self.username_input)

        # Password input + toggle
        pwd_row = QHBoxLayout()
        pwd_row.setSpacing(10)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet(self._input_style())
        pwd_row.addWidget(self.password_input)

        self.show_pwd_cb = QCheckBox("Show")
        self.show_pwd_cb.setToolTip("Show / hide password")
        self.show_pwd_cb.toggled.connect(self._toggle_password)
        pwd_row.addWidget(self.show_pwd_cb)
        card_layout.addLayout(pwd_row)

        # Remember me checkbox and spacer
        extras_row = QHBoxLayout()
        self.remember_cb = QCheckBox("Remember username")
        extras_row.addWidget(self.remember_cb)
        extras_row.addStretch(1)
        card_layout.addLayout(extras_row)

        # Buttons (Login + Cancel)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.login_btn = QPushButton("🔓 Login")
        self.login_btn.setFixedHeight(46)
        self.login_btn.setStyleSheet(self._primary_button_style())
        self.login_btn.clicked.connect(self.attempt_login)
        btn_row.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(46)
        self.cancel_btn.setStyleSheet(self._secondary_button_style())
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn)

        card_layout.addLayout(btn_row)

        # status line
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #d14;")
        card_layout.addWidget(self.status_label)

        hbox.addWidget(card)
        hbox.addStretch(1)
        root.addLayout(hbox)

        # small footer note
        footer = QLabel("Tip: Use the server configuration page to change host/port. Login attempts are logged.")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #397288; font-size: 11px;")
        root.addSpacing(8)
        root.addWidget(footer)

    def _input_style(self):
        return """
            QLineEdit {
                border: 1px solid #cfeaf7;
                background: #f7fbff;
                border-radius: 10px;
                padding-left: 12px;
                font-size: 14px;
                color: #063b57;
            }
            QLineEdit:focus {
                border: 2px solid #6ec7ff;
                background: white;
            }
        """

    def _primary_button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #00bfa5, stop:1 #00a0d6);
                color: white;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
            }
            QPushButton:pressed { padding-top: 2px; }
        """

    def _secondary_button_style(self):
        return """
            QPushButton {
                background: #eef6fb;
                color: #2a6d86;
                border-radius: 10px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid #d5eaf6;
            }
            QPushButton:hover { background: #e6f2f9; }
        """

    def _toggle_password(self, show: bool):
        self.password_input.setEchoMode(QLineEdit.Normal if show else QLineEdit.Password)

    # ---------------- Login logic ----------------
    def _recv_line(self):
        try:
            return self.client.receive()
        except Exception:
            return None

    def _emit_log(self, text: str):
        """Emit a log line for the LogWindow; also update compact status_label for immediate feedback."""
        self.log_event.emit(text)
        # short status update (clears after 4s)
        self.status_label.setText(text)
        QTimer.singleShot(4000, lambda: self.status_label.setText(""))

    def attempt_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Missing fields", "Please enter both username and password.")
            return

        # disable controls while communicating
        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self._emit_log(f"Attempting login for user '{user}'...")

        try:
            # send USER
            try:
                self.client.send(f"USER {user}")
            except Exception as e:
                raise RuntimeError(f"Failed to send USER: {e}")

            resp = self._recv_line()
            if resp is None:
                self._emit_log("No response from server after USER.")
                raise RuntimeError("No response from server (USER).")
            self._emit_log(f"Server (USER): {resp}")

            if not resp.startswith("331"):
                # username rejected
                QMessageBox.warning(self, "Login failed", resp)
                self._emit_log(f"Login failed for '{user}': server response: {resp}")
                return

            # send PASS
            self.client.send(f"PASS {pwd}")
            resp = self._recv_line()
            if resp is None:
                self._emit_log("No response from server after PASS.")
                raise RuntimeError("No response from server (PASS).")

            self._emit_log(f"Server (PASS): {resp}")

            if resp.startswith("230"):
                # optional PERMS line follows (server.py sends PERMS after 230 in your setup)
                perms = {"read": False, "write": False, "delete": False}
                next_line = self._recv_line()
                if next_line and next_line.startswith("PERMS"):
                    # parse: "PERMS read=1 write=1 delete=0"
                    try:
                        for token in next_line.split()[1:]:
                            if "=" in token:
                                k, v = token.split("=", 1)
                                perms[k.strip()] = bool(int(v))
                    except Exception:
                        # keep defaults if parsing fails
                        pass
                    self._emit_log(f"Permissions for '{user}': {perms}")
                else:
                    # no perms line, assume default full or request server later
                    self._emit_log(f"No PERMS line received for '{user}', using default flags.")

                # remember username if requested
                if self.remember_cb.isChecked():
                    try:
                        with open("remember_user.txt", "w", encoding="utf-8") as f:
                            f.write(user)
                        self._emit_log(f"Username '{user}' saved (remember).")
                    except Exception:
                        pass

                QMessageBox.information(self, "Success", "Login successful — welcome!")
                self._emit_log(f"Login successful for '{user}'.")
                self.login_success.emit({"username": user, "permissions": perms})
                self.close()
                return

            else:
                # login failed (530 etc)
                QMessageBox.warning(self, "Login failed", resp)
                self._emit_log(f"Login failed for '{user}': {resp}")
                return

        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Login error:\n{exc}")
            self._emit_log(f"Login error for '{user}': {exc}")

        finally:
            self.login_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)

