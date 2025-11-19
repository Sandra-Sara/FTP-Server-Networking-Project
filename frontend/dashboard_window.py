from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QHBoxLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os


class DashboardWindow(QWidget):
    def __init__(self, username, config):
        super().__init__()

        self.username = username
        self.config = config

        self.setWindowTitle("LockBox FTP Server - Dashboard")
        self.setGeometry(250, 80, 900, 600)

        # --------------------- GLOBAL UI STYLE ---------------------
        self.setStyleSheet("""
            QWidget {
                background-color: #e8f0fe;
            }
            QFrame#card {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #dce3f0;
            }
            QPushButton {
                background-color: #409EFF;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #66b1ff;
            }
            QListWidget {
                background-color: white;
                border: 2px solid #d0d7de;
                border-radius: 6px;
                font-size: 14px;
            }
        """)

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignTop)

        # --------------------- TITLE CARD ---------------------
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 20, 30, 20)

        title = QLabel("📁 LockBox FTP Dashboard")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        # server info
        info = QLabel(
            f"🔗 Connected as: <b>{username}</b><br>"
            f"🌐 Server: {config['host']}:{config['port']}"
        )
        info.setFont(QFont("Arial", 12))
        info.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(info)

        main.addWidget(card)

        # --------------------- FILE LIST AREA ---------------------
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(250)
        main.addWidget(self.file_list)

        # --------------------- BUTTONS ---------------------
        btn_row = QHBoxLayout()

        self.btn_list = QPushButton("📂 List Files")
        self.btn_list.clicked.connect(self.list_files)
        btn_row.addWidget(self.btn_list)

        self.btn_upload = QPushButton("⬆ Upload File")
        self.btn_upload.clicked.connect(self.upload_file)
        btn_row.addWidget(self.btn_upload)

        self.btn_download = QPushButton("⬇ Download File")
        self.btn_download.clicked.connect(self.download_file)
        btn_row.addWidget(self.btn_download)

        self.btn_delete = QPushButton("🗑 Delete File")
        self.btn_delete.clicked.connect(self.delete_file)
        btn_row.addWidget(self.btn_delete)

        main.addLayout(btn_row)

        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.close)
        main.addWidget(logout_btn)

    # ----------------------------------------------------
    # FUNCTION: LIST FILES (Dummy – real FTP later)
    # ----------------------------------------------------
    def list_files(self):
        """Mock file list — will connect to your real FTP server later."""
        self.file_list.clear()
        fake_files = ["hello.txt", "notes.pdf", "image.png", "report.docx"]
        self.file_list.addItems(fake_files)

    # ----------------------------------------------------
    # UPLOAD FILE
    # ----------------------------------------------------
    def upload_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose File to Upload")

        if not path:
            return

        QMessageBox.information(self, "Upload", f"Selected file:\n{path}")

        # TODO: integrate with client.py
        # send STOR command from here

    # ----------------------------------------------------
    # DOWNLOAD FILE
    # ----------------------------------------------------
    def download_file(self):
        selected = self.file_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Select File", "Please select a file first.")
            return

        filename = selected.text()
        QMessageBox.information(self, "Download", f"Downloading: {filename}")

        # TODO: integrate RETR command

    # ----------------------------------------------------
    # DELETE FILE
    # ----------------------------------------------------
    def delete_file(self):
        selected = self.file_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Select File", "Please select a file to delete.")
            return

        filename = selected.text()

        confirm = QMessageBox.question(
            self,
            "Delete File",
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.Yes:
            QMessageBox.information(self, "Deleted", f"Deleted: {filename}")

            # TODO: integrate DELE command
