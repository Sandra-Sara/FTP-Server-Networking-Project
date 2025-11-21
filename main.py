import sys
from PyQt5.QtWidgets import QApplication

# UI windows
from frontend.welcome_window import ConfigWindow
from frontend.login_window import LoginWindow
from frontend.dashboard_window import DashboardWindow

# Backend
from backend.client_socket import ClientSocket
from backend.logger import Logger  # ✅ import logger


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Shared client socket for entire session
        self.client = ClientSocket()

        # Shared logger for entire session
        self.logger = Logger.instance()  # ✅ singleton logger

        # STEP 1 — Open configuration window
        self.config_window = ConfigWindow()
        self.config_window.config_complete.connect(self.open_login)
        self.config_window.show()

    # -----------------------------------------------------------------------
    # STEP 2 — Configure server → Connect → Open Login Window
    # -----------------------------------------------------------------------
    def open_login(self, config_data):
        host = config_data["host"]
        port = config_data["port"]

        print(f"Connecting to FTP server at {host}:{port}")

        # Save host + port in ClientSocket
        self.client.set_server(host, port)

        # Connect using internal host/port (no args)
        if not self.client.connect():
            print("❌ Connection failed. Check server.")
            return

        print("✅ Connected successfully to server.")

        self.config_window.close()

        # Create login window (pass the connected ClientSocket)
        self.login_window = LoginWindow(self.client)

        # When login succeeds → open dashboard
        self.login_window.login_success.connect(self.open_dashboard)

        self.login_window.show()

    # -----------------------------------------------------------------------
    # STEP 3 — Login Success → Open Dashboard
    # -----------------------------------------------------------------------
    def open_dashboard(self, login_data):
        username = login_data["username"]
        permissions = login_data["permissions"]

        print(f"👤 User logged in: {username}")
        print("🔐 Permissions:", permissions)

        self.login_window.close()

        # Dashboard expects client_socket, username, permissions, logger
        self.dashboard = DashboardWindow(
            client_socket=self.client,
            username=username,
            permissions=permissions,
            logger=self.logger  # ✅ pass logger here
        )

        self.dashboard.show()

    # -----------------------------------------------------------------------
    # RUN APP
    # -----------------------------------------------------------------------
    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = MainApp()
    app.run()
