from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QListWidget, QHBoxLayout, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import os


class DashboardWindow(QWidget):
    def __init__(self, client_socket, username, permissions):
        super().__init__()

        self.client = client_socket
        self.username = username
        self.permissions = permissions

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

        main.addLayout(btn_row)

        # LOGOUT
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.close)
        main.addWidget(logout_btn)

    # -----------------------------------------------------
    # LIST FILES
    # -----------------------------------------------------
    def list_files(self):
        self.file_list.clear()
        try:
            self.client.send("LIST")
            lines = self.client.receive_multiline().split("\n")

            for line in lines:
                if line.startswith("FILE") or line.startswith("DIR"):
                    # Format: "FILE 123 myfile.txt"
                    parts = line.split(" ", 2)
                    if len(parts) == 3:
                        _, _, name = parts
                        self.file_list.addItem(name)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # -----------------------------------------------------
    # UPLOAD FILE
    # -----------------------------------------------------
    def upload_file(self):
        if not self.permissions["write"]:
            QMessageBox.warning(self, "Denied", "You do not have write permissions.")
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
                QMessageBox.warning(self, "Error", response)
                return

            # Send file bytes
            with open(path, "rb") as f:
                self.client.send_bytes(f.read())

            done = self.client.receive()
            QMessageBox.information(self, "Upload Complete", done)

            self.list_files()

        except Exception as e:
            QMessageBox.critical(self, "Upload Error", str(e))

    # -----------------------------------------------------
    # DOWNLOAD FILE
    # -----------------------------------------------------
    def download_file(self):
        if not self.permissions["read"]:
            QMessageBox.warning(self, "Denied", "You do not have read permissions.")
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
                QMessageBox.warning(self, "Error", response)
                return

            # Parse size
            size = int(response.split()[1])

            save_path, _ = QFileDialog.getSaveFileName(self, "Save File As", filename)
            if not save_path:
                return

            data = self.client.receive_bytes(size)

            with open(save_path, "wb") as f:
                f.write(data)

            done = self.client.receive()
            QMessageBox.information(self, "Download Complete", done)

        except Exception as e:
            QMessageBox.critical(self, "Download Error", str(e))

    # -----------------------------------------------------
    # DELETE FILE
    # -----------------------------------------------------
    def delete_file(self):
        if not self.permissions["delete"]:
            QMessageBox.warning(self, "Denied", "You do not have delete permissions.")
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
            self.list_files()

        except Exception as e:
            QMessageBox.critical(self, "Delete Error", str(e))
