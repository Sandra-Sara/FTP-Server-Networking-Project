from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont


class ConfigWindow(QWidget):
    config_complete = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("LockBox FTP Server - Configuration")
        self.setGeometry(300, 100, 800, 600)

        # ---------------- GLOBAL STYLES ----------------
        self.setStyleSheet("""
            QWidget {
                background-color: #e8f0fe;
            }
            QFrame#cardFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #dce3f0;
            }
            QLineEdit {
                border: 2px solid #d0d7de;
                border-radius: 6px;
                padding-left: 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #409EFF;
            }
            QPushButton {
                background-color: #409EFF;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px 0;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # ---------------- Card Layout ----------------
        frame = QFrame()
        frame.setObjectName("cardFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(60, 40, 60, 40)
        frame_layout.setSpacing(20)

        # Title
        title = QLabel("🔐 LockBox FTP Server")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 22, QFont.Bold))
        frame_layout.addWidget(title)

        subtitle = QLabel("Server Configuration")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 14))
        frame_layout.addWidget(subtitle)

        # Server IP
        self.ip_row, self.ip_input = self.create_input_row(
            "🌐 Server IP:", "Enter Server IP (e.g., 127.0.0.1)"
        )
        frame_layout.addLayout(self.ip_row)

        # Port
        self.port_row, self.port_input = self.create_input_row(
            "🔌 Port:", "Enter Port (e.g., 2121)"
        )
        frame_layout.addLayout(self.port_row)

        # Username
        self.username_row, self.username_input = self.create_input_row(
            "👤 Username:", "Enter Login Username"
        )
        frame_layout.addLayout(self.username_row)

        # Password
        self.pass_row, self.pass_input = self.create_input_row(
            "🔑 Password:", "Enter Password", True
        )
        frame_layout.addLayout(self.pass_row)

        # Save button
        self.save_button = QPushButton("💾 Save & Continue")
        self.save_button.clicked.connect(self.save_config)
        frame_layout.addWidget(self.save_button, alignment=Qt.AlignCenter)

        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

    # -----------------------------------------------------
    # Create Input Row
    # -----------------------------------------------------
    def create_input_row(self, label_text, placeholder, is_password=False):
        layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12, QFont.Bold))
        label.setFixedWidth(130)
        label.setStyleSheet("color: #2f3640;")

        layout.addWidget(label)

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(40)
        input_field.setMinimumWidth(400)
        input_field.setFont(QFont("Arial", 11))

        if is_password:
            input_field.setEchoMode(QLineEdit.Password)

        layout.addWidget(input_field)

        return layout, input_field

    # -----------------------------------------------------
    # Save Configuration
    # -----------------------------------------------------
    def save_config(self):
        host = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        username = self.username_input.text().strip()
        password = self.pass_input.text().strip()

        if not host or not port or not username or not password:
            QMessageBox.warning(self, "Missing Information",
                                "Please fill in all fields before continuing.")
            return

        config = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
        }

        QMessageBox.information(self, "Saved", "Configuration saved successfully!")

        # Emit to main.py
        self.config_complete.emit(config)
