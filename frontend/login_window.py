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
        self.setFixedSize(900,700)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6DD5FA, stop:1 #00C1FF
                );
            }
        """)
        self.build_ui()

    # -------------------------------------------------------
    # Build UI
    # -------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # ---------------------------------------------------
        # TITLE
        # ---------------------------------------------------
        title = QLabel("🔐 LockBox FTP")
        title.setFont(QFont("Segoe UI", 30, QFont.Bold))
        title.setStyleSheet("color: #ffffff;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ---------------------------------------------------
        # FTP Server Description
        # ---------------------------------------------------
        description = QLabel("Connect securely to your LockBox FTP server to manage files")
        description.setFont(QFont("Segoe UI", 14))
        description.setStyleSheet("color: #e0f7fa; font-weight: 500;")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)

        subtitle = QLabel("Secure Login Access")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #e0f7fa;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # ---------------------------------------------------
        # CARD FRAME
        # ---------------------------------------------------
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #a2d4f7;
                border-radius: 20px;
            }
        """)
        card.setFixedWidth(420)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # ---------------------------------------------------
        # USERNAME FIELD
        # ---------------------------------------------------
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(50)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: #81cbee;
                border: 2px solid #5fb6e0;
                border-radius: 12px;
                padding-left: 12px;
                color: #004466;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
            }
        """)
        card_layout.addWidget(self.username_input)

        # ---------------------------------------------------
        # PASSWORD FIELD
        # ---------------------------------------------------
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(50)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: #81cbee;
                border: 2px solid #5fb6e0;
                border-radius: 12px;
                padding-left: 12px;
                color: #004466;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #ffffff;
            }
        """)
        card_layout.addWidget(self.password_input)

        # ---------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(50)
        self.login_btn.clicked.connect(self.attempt_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FFD1, stop:1 #00AFFF
                );
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FFE5, stop:1 #33CFFF
                );
            }
        """)
        btn_row.addWidget(self.login_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(50)
        self.cancel_btn.clicked.connect(self.close)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #00BFFF;
                border-radius: 12px;
                color: #ffffff;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #0099CC;
            }
        """)
        btn_row.addWidget(self.cancel_btn)

        card_layout.addLayout(btn_row)
        layout.addWidget(card)

    # -------------------------------------------------------
    # Read response
    # -------------------------------------------------------
    def _recv_line(self):
        try:
            return self.client.receive()
        except:
            return None

    # -------------------------------------------------------
    # LOGIN PROCESS
    # -------------------------------------------------------
    def attempt_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, "Missing Fields", "Username and password required.")
            return

        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        try:
            self.client.send(f"USER {user}")
            resp = self._recv_line()
            if not resp or not resp.startswith("331"):
                QMessageBox.warning(self, "Login Failed", resp or "Server error")
                self._reset_buttons()
                return

            self.client.send(f"PASS {pwd}")
            resp = self._recv_line()
            if not resp or not resp.startswith("230"):
                QMessageBox.warning(self, "Login Failed", resp or "Server error")
                self._reset_buttons()
                return

            perms_line = self._recv_line()
            perms = {"read": False, "write": False, "delete": False}

            if perms_line and perms_line.startswith("PERMS"):
                parts = perms_line.split()
                for p in parts[1:]:
                    key, val = p.split("=")
                    perms[key] = bool(int(val))

            # -------------------------------
            # Custom QMessageBox for Success
            # -------------------------------
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Success")
            msg_box.setText("Login successful!")
            msg_box.setIcon(QMessageBox.Information)

            ok_button = msg_box.addButton(QMessageBox.Ok)
            ok_button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #00BFFF;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 35px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #e0f7fa;
                }
            """)
            msg_box.exec_()

            self.login_success.emit({"username": user, "permissions": perms})
            self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login error: {e}")

        self._reset_buttons()

    def _reset_buttons(self):
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
