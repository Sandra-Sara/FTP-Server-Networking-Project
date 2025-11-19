import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QMessageBox, QHBoxLayout, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class LoginWindow(QWidget):
    login_success = pyqtSignal(str)

    def __init__(self, expected_username, expected_password):
        super().__init__()

        self.expected_username = expected_username
        self.expected_password = expected_password

        self.setWindowTitle("Login")
        self.setGeometry(400, 120, 900, 600)
        self.setup_ui()
        self.apply_theme()

    # -----------------------------------------------------
    # UI SETUP
    # -----------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # White Card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 16px;
            }
        """)
        card.setFixedSize(500, 330)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(18)
        card_layout.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel("User Login")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: black;")

        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter Username")
        self.username_input.setFixedHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding-left: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
            }
        """)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setFixedHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cccccc;
                border-radius: 10px;
                padding-left: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #4a90e2;
            }
        """)

        # Login button
        login_button = QPushButton("Login")
        login_button.setFixedHeight(45)
        login_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3b78c9;
            }
        """)
        login_button.clicked.connect(self.validate_login)

        # Add widgets into the card
        card_layout.addWidget(title)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_button)

        card.setLayout(card_layout)
        layout.addWidget(card)

        self.setLayout(layout)

    # -----------------------------------------------------
    # BACKGROUND THEME
    # -----------------------------------------------------
    def apply_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(240, 242, 245))  # same as dashboard bg
        self.setPalette(palette)

    # -----------------------------------------------------
    # LOGIN VALIDATION
    # -----------------------------------------------------
    def validate_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text().strip()

        if user == self.expected_username and pwd == self.expected_password:
            self.login_success.emit(user)
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password!")
