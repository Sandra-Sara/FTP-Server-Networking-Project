# frontend/log_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from backend.logger import Logger
import datetime

class LogWindow(QWidget):
    """
    Live-updating log window. Subscribe to a Logger's new_log signal.
    Open as non-blocking window from Dashboard.
    """

    def __init__(self, logger: Logger = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LockBox — Activity Log")
        self.setGeometry(300, 120, 900, 600)
        self._build_ui()

        # Use provided logger or default singleton
        self.logger = logger or Logger.instance()

        # connect signal
        self.logger.new_log.connect(self.append_line)

        # populate existing logs
        for line in self.logger.get_all():
            self._append_text(line)

    def _build_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)

        header = QLabel("📜 Activity Log")
        header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(header)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setFont(QFont("Consolas", 11))
        self.layout.addWidget(self.text)

        controls = QHBoxLayout()
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.clicked.connect(self.save_logs)
        self.btn_clear = QPushButton("🧹 Clear")
        self.btn_clear.clicked.connect(self.clear_logs)
        self.btn_copy = QPushButton("📋 Copy All")
        self.btn_copy.clicked.connect(self.copy_all)

        controls.addWidget(self.btn_save)
        controls.addWidget(self.btn_clear)
        controls.addWidget(self.btn_copy)
        controls.addStretch()

        self.layout.addLayout(controls)

    def append_line(self, line: str):
        """Slot connected to Logger.new_log signal. Called in Qt main thread."""
        self._append_text(line)

    def _append_text(self, line: str):
        # append and auto-scroll
        cursor = self.text.textCursor()
        cursor.movePosition(cursor.End)
        self.text.setTextCursor(cursor)
        self.text.append(line)
        # auto-scroll: ensure bottom visible
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())

    def save_logs(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save logs to file",
            f"lockbox-log-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            self.logger.save_to_file(path)
            QMessageBox.information(self, "Saved", f"Logs saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save logs:\n{e}")

    def clear_logs(self):
        confirm = QMessageBox.question(self, "Confirm", "Clear all logs?")
        if confirm == QMessageBox.Yes:
            self.logger.clear()
            self.text.clear()

    def copy_all(self):
        clipboard = self.text.clipboard()
        clipboard.setText(self.text.toPlainText())
        QMessageBox.information(self, "Copied", "All logs copied to clipboard.")
