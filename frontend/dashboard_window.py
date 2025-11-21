# frontend/dashboard_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QHBoxLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os

from frontend.log_window import LogWindow   # ✅ Log window
from backend.logger import Logger            # ✅ Logger

class DashboardWindow(QWidget):
    def __init__(self, client_socket, username, permissions, logger):
        super().__init__()

        self.client = client_socket
        self.username = username
        self.permissions = permissions
        self.logger = logger   # ✅ store logger instance

        self.setWindowTitle("LockBox FTP Dashboard")
        self.setGeometry(250, 80, 950, 620)

        # ---------------- GLOBAL UI THEME ----------------
        self.setStyleSheet("""
            QWidget {
                background-color: #eef3fd;
                font-family: Segoe UI;
            }
            QFrame#card {
                background-color: white;
                border-radius: 14px;
                border: 2px solid #d3dcec;
            }
            QPushButton {
                background-color: #4a8cff;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #6aa6ff;
            }
            QListWidget {
                background-color: white;
                border: 2px solid #c9d4e7;
                border-radius: 10px;
                font-size: 14px;
            }
        """)

        main = QVBoxLayout(self)
        main.setAlignment(Qt.AlignTop)

        # ---------------- HEADER CARD ----------------
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 20, 30, 20)

        title = QLabel("📁 LockBox FTP Dashboard")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        perm_str = (
            f"Read: {'✔' if permissions['read'] else '✖'}  |  "
            f"Write: {'✔' if permissions['write'] else '✖'}  |  "
            f"Delete: {'✔' if permissions['delete'] else '✖'}"
        )

        info = QLabel(
            f"<b>User:</b> {username}<br>"
            f"<b>Permissions:</b> {perm_str}"
        )
        info.setFont(QFont("Segoe UI", 12))
        info.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(info)

        main.addWidget(card)

        # ---------------- FILE LIST ----------------
        self.file_list = QListWidget()
        self.file_list.setFixedHeight(300)
        main.addWidget(self.file_list)

        # ---------------- BUTTON ROW ----------------
        btn_row = QHBoxLayout()

        self.btn_list = QPushButton("📂 List Files")
        self.btn_list.clicked.connect(self.list_files)
        btn_row.addWidget(self.btn_list)

        self.btn_upload = QPushButton("⬆ Upload")
        self.btn_upload.clicked.connect(self.upload_file)
        btn_row.addWidget(self.btn_upload)

        self.btn_download = QPushButton("⬇ Download")
        self.btn_download.clicked.connect(self.download_file)
        btn_row.addWidget(self.btn_download)

        self.btn_delete = QPushButton("🗑 Delete")
        self.btn_delete.clicked.connect(self.delete_file)
        btn_row.addWidget(self.btn_delete)

        self.btn_logs = QPushButton("📜 View Logs")
        self.btn_logs.clicked.connect(self.open_logs)
        btn_row.addWidget(self.btn_logs)

        main.addLayout(btn_row)

        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.logout)
        main.addWidget(logout_btn)

        self.log("Logged in successfully.")  # ✅ fixed logger usage

    # -----------------------------------------------------
    def log(self, text):
        """Send log to shared logger"""
        self.logger.log(f"[User: {self.username}] {text}")  # ✅ use .log()

    # -----------------------------------------------------
    def open_logs(self):
        self.log("Opened Logs Window.")
        # ✅ Pass logger to LogWindow
        self.log_window = LogWindow(logger=self.logger)
        self.log_window.show()

    # -----------------------------------------------------
    def logout(self):
        self.log("User logged out.")
        self.close()

    # -----------------------------------------------------
    # LIST FILES
    # -----------------------------------------------------
    def list_files(self):
        self.file_list.clear()
        try:
            self.client.send("LIST")
            lines = self.client.receive_multiline().split("\n")

            count = 0
            for line in lines:
                if line.startswith("FILE") or line.startswith("DIR"):
                    parts = line.split(" ", 2)
                    if len(parts) == 3:
                        _, _, name = parts
                        self.file_list.addItem(name)
                        count += 1

            self.log(f"Listed files ({count} items).")

        except Exception as e:
            self.log(f"Error listing files: {str(e)}")
            QMessageBox.critical(self, "Error", str(e))

    # -----------------------------------------------------
    # UPLOAD FILE
    # -----------------------------------------------------
    def upload_file(self):
        if not self.permissions["write"]:
            QMessageBox.warning(self, "Denied", "You do not have write permissions.")
            self.log("Upload blocked (no permission).")
            return

        path, _ = QFileDialog.getOpenFileName(self, "Select a file to upload")
        if not path:
            return

        filename = os.path.basename(path)
        size = os.path.getsize(path)

        try:
            self.client.send(f"STOR {filename} {size}")
            response = self.client.receive()

            if not response.startswith("150"):
                self.log(f"Upload failed: {response}")
                QMessageBox.warning(self, "Error", response)
                return

            with open(path, "rb") as f:
                self.client.send_bytes(f.read())

            done = self.client.receive()
            QMessageBox.information(self, "Upload Complete", done)
            self.log(f"Uploaded file: {filename} ({size} bytes)")
            self.list_files()

        except Exception as e:
            self.log(f"Upload Error: {str(e)}")
            QMessageBox.critical(self, "Upload Error", str(e))

    # -----------------------------------------------------
    # DOWNLOAD FILE
    # -----------------------------------------------------
    def download_file(self):
        if not self.permissions["read"]:
            QMessageBox.warning(self, "Denied", "You do not have read permissions.")
            self.log("Download blocked (no permission).")
            return

        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Select a File", "Select a file to download.")
            return

        filename = item.text()

        try:
            self.client.send(f"RETR {filename}")
            response = self.client.receive()

            if not response.startswith("150"):
                self.log(f"Download failed: {response}")
                QMessageBox.warning(self, "Error", response)
                return

            size = int(response.split()[1])
            save_path, _ = QFileDialog.getSaveFileName(self, "Save File As", filename)
            if not save_path:
                return

            data = self.client.receive_bytes(size)

            with open(save_path, "wb") as f:
                f.write(data)

            done = self.client.receive()
            QMessageBox.information(self, "Download Complete", done)
            self.log(f"Downloaded file: {filename} ({size} bytes)")

        except Exception as e:
            self.log(f"Download Error: {str(e)}")
            QMessageBox.critical(self, "Download Error", str(e))

    # -----------------------------------------------------
    # DELETE FILE
    # -----------------------------------------------------
    def delete_file(self):
        if not self.permissions["delete"]:
            QMessageBox.warning(self, "Denied", "You do not have delete permissions.")
            self.log("Delete blocked (no permission).")
            return

        item = self.file_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Select a File", "Select a file to delete.")
            return

        filename = item.text()

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.client.send(f"DELE {filename}")
            response = self.client.receive()
            QMessageBox.information(self, "Deleted", response)

            self.log(f"Deleted file: {filename}")
            self.list_files()

        except Exception as e:
            self.log(f"Delete Error: {str(e)}")
            QMessageBox.critical(self, "Delete Error", str(e))
