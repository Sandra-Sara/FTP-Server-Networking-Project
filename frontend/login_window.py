from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QHBoxLayout,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


class LoginWindow(QWidget):
    """
    Beautiful Modern Login Window
    Emits a dict: {
        "username": str,
        "permissions": {"read":bool, "write":bool, "delete":bool}
    }
    """

    login_success = pyqtSignal(dict)

    def __init__(self, client_socket):
        super().__init__()
        self.client = client_socket

        self.setWindowTitle("LockBox FTP — Login")
        self.setFixedSize(900,700)
        self._build_ui()

    # -----------------------------------------------------
    # BUILD UI
    # -----------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #dfe9f3, stop:1 #ffffff
                );
            }
            QLineEdit {
                background: white;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding-left: 10px;
                font-size: 15px;
            }
            QPushButton {
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # -------------------------
        # CARD FRAME (center box)
        # -------------------------
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 14px;
                padding: 22px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(18)

        # Title
        title = QLabel("🔐 LockBox FTP Login")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Enter your server credentials")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 14px;")
        card_layout.addWidget(subtitle)

        # Inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(45)
        card_layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(45)
        card_layout.addWidget(self.password_input)

        # Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.login_btn = QPushButton("🚀 Login")
        self.login_btn.setStyleSheet(
            "background-color: #4b8df9; color: white;"
        )
        self.login_btn.setFixedHeight(44)
        self.login_btn.clicked.connect(self.attempt_login)
        btn_row.addWidget(self.login_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(
            "background-color: #e4e7ef; color: #222;"
        )
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(self.cancel_btn)

        card_layout.addLayout(btn_row)

        # Add card to center layout
        layout.addWidget(card)

    # -----------------------------------------------------
    # READ SERVER RESPONSE
    # -----------------------------------------------------
    def _recv_line(self):
        try:
            return self.client.receive()
        except Exception:
            return None

    # -----------------------------------------------------
    # ATTEMPT LOGIN
    # -----------------------------------------------------
    def attempt_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Missing Info", "Please enter both username and password.")
            return

        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        try:
            self.client.send(f"USER {user}")
            resp = self._recv_line()

            if not resp or not resp.startswith("331"):
                QMessageBox.warning(self, "Login Failed", resp or "Server did not respond.")
                self._reset_buttons()
                return

            self.client.send(f"PASS {pwd}")
            resp = self._recv_line()

            if resp and resp.startswith("230"):
                next_line = self._recv_line()
                perms = {"read": False, "write": False, "delete": False}

                if next_line and next_line.startswith("PERMS"):
                    for p in next_line.split()[1:]:
                        if "=" in p:
                            k, v = p.split("=")
                            perms[k] = bool(int(v))

                QMessageBox.information(self, "Success", "Login successful!")
                self.login_success.emit({"username": user, "permissions": perms})
                self.close()
                return

            else:
                QMessageBox.warning(self, "Login Failed", resp)
                self._reset_buttons()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login error:\n{e}")
            self._reset_buttons()

    def _reset_buttons(self):
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
