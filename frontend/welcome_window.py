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
        self.setGeometry(350, 100,900,700)

        # ---------------- GLOBAL STYLE ----------------
        self.setStyleSheet("""
            QWidget {
                background-color: #eef3fc;
            }
            QFrame#cardFrame {
                background-color: white;
                border-radius: 14px;
                border: 2px solid #dce3f0;
            }
            QLineEdit {
                border: 2px solid #ccd6e4;
                border-radius: 6px;
                padding-left: 10px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4b8df9;
            }
            QPushButton {
                background-color: #4b8df9;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 12px 0;
            }
            QPushButton:hover {
                background-color: #76aaff;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # ---------------- Card Container ----------------
        frame = QFrame()
        frame.setObjectName("cardFrame")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(50, 40, 50, 40)
        frame_layout.setSpacing(22)

        # Title
        title = QLabel("🔐 LockBox FTP Server")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 24, QFont.Bold))
        frame_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Secure • Fast • Encrypted File Transfer")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #444;")
        frame_layout.addWidget(subtitle)

        # Intro Section
        intro = QLabel(
            "LockBox ensures secure and private file transfers with powerful encryption\n"
            "and dedicated authentication handled directly by the server.\n\n"
            "Configure your connection settings below to get started."
        )
        intro.setAlignment(Qt.AlignCenter)
        intro.setFont(QFont("Arial", 10))
        intro.setStyleSheet("color: #333;")
        frame_layout.addWidget(intro)

        # -------------- INPUT FIELDS -----------------

        # IP Address
        self.ip_row, self.ip_input = self.create_input_row(
            "🌐 Server IP:", "Enter Server IP (e.g., 127.0.0.1)"
        )
        frame_layout.addLayout(self.ip_row)

        # Port
        self.port_row, self.port_input = self.create_input_row(
            "🔌 Port:", "Enter Port (e.g., 2121)"
        )
        frame_layout.addLayout(self.port_row)

        # -------------- BUTTON -----------------
        self.save_button = QPushButton("🚀 Start & Connect")
        self.save_button.clicked.connect(self.save_config)
        frame_layout.addWidget(self.save_button, alignment=Qt.AlignCenter)

        main_layout.addWidget(frame, alignment=Qt.AlignCenter)

    # -----------------------------------------------------
    def create_input_row(self, label_text, placeholder):
        layout = QHBoxLayout()

        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12, QFont.Bold))
        label.setFixedWidth(150)
        label.setStyleSheet("color: #2f3640;")
        layout.addWidget(label)

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(42)
        input_field.setMinimumWidth(400)
        input_field.setFont(QFont("Arial", 11))

        layout.addWidget(input_field)
        return layout, input_field

    # -----------------------------------------------------
    def save_config(self):
        host = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        # Validate empty
        if not host or not port:
            QMessageBox.warning(self, "Missing Information",
                                "Please fill in all fields before continuing.")
            return

        # Validate numeric port
        if not port.isdigit():
            QMessageBox.warning(self, "Invalid Port",
                                "Port must be a number.")
            return

        port = int(port)

        config = {
            "host": host,
            "port": port
        }

        QMessageBox.information(self, "Success", "Configuration saved successfully!")
        self.config_complete.emit(config)
