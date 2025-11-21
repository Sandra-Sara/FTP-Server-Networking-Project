from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor


class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self, client):
        super().__init__()
        self.client = client

        self.setWindowTitle("LockBox FTP — Login")
        self.setFixedSize(900, 700)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6DD5FA, stop:1 #00C1FF
                );
            }
        """)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # ——— Title & Description (outside the card) ———
        title = QLabel("LockBox FTP")
        title.setFont(QFont("Segoe UI", 36, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        description = QLabel("Connect securely to your LockBox FTP server to manage files")
        description.setFont(QFont("Segoe UI", 14))
        description.setStyleSheet("color: #e0f7fa; font-weight: 500;")
        description.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(description)

        subtitle = QLabel("Secure Login Access")
        subtitle.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
        subtitle.setStyleSheet("color: white;")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        # Push everything to the true vertical center
        main_layout.addStretch(1)

        # ——— Horizontal centering for the card ———
        h_center = QHBoxLayout()
        h_center.addStretch(1)
        h_center.addWidget(self.create_login_card())
        h_center.addStretch(1)

        main_layout.addLayout(h_center)
        main_layout.addStretch(1)  # bottom stretch

    def create_login_card(self):
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background-color: #a2d4f7;
                border-radius: 20px;
            }
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(22)

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(52)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #81cbee;
                border: 2px solid #5fb6e0;
                border-radius: 12px;
                padding-left: 15px;
                color: #004466;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 3px solid white;
                background-color: #9eddff;
            }
        """)
        layout.addWidget(self.username_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(52)
        self.password_input.setStyleSheet(self.username_input.styleSheet())  # reuse style
        layout.addWidget(self.password_input)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)

        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(52)
        self.login_btn.clicked.connect(self.attempt_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FFD1, stop:1 #00AFFF);
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FFE5, stop:1 #33CFFF);
            }
        """)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(52)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BFFF;
                border-radius: 12px;
                color: white;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #0099CC; }
        """)

        btn_row.addWidget(self.login_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        return card

    # —————————————————————— Login Logic (unchanged) ——————————————————————
    def _recv_line(self):
        try:
            return self.client.receive()
        except:
            return None

    def attempt_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Missing Fields", "Please enter both username and password.")
            return

        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        try:
            self.client.send(f"USER {user}")
            resp = self._recv_line()
            if not resp or not resp.startswith("331"):
                QMessageBox.warning(self, "Login Failed", resp or "Server error")
                return

            self.client.send(f"PASS {pwd}")
            resp = self._recv_line()
            if not resp or not resp.startswith("230"):
                QMessageBox.warning(self, "Login Failed", resp or "Invalid credentials")
                return

            perms = {"read": True, "write": True, "delete": True}
            perms_line = self._recv_line()
            if perms_line and perms_line.startswith("PERMS"):
                try:
                    for item in perms_line.split()[1:]:
                        k, v = item.split("=")
                        perms[k] = bool(int(v))
                except:
                    pass

            QMessageBox.information(self, "Success", "Login successful!\nWelcome to LockBox FTP")
            self.login_success.emit({"username": user, "permissions": perms})
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed:\n{e}")
        finally:
            self.login_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)