import sys
from PyQt5.QtWidgets import QApplication

# Import UI windows
from frontend.welcome_window import ConfigWindow
from frontend.login_window import LoginWindow
from frontend.dashboard_window import DashboardWindow

# Backend Client Socket
from backend.client_socket import ClientSocket


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Create the client socket instance (kept for whole session)
        self.client = ClientSocket()

        # Step 1 — Open config window
        self.config_window = ConfigWindow()
        self.config_window.config_complete.connect(self.open_login)
        self.config_window.show()

    # -------------------------------------------------------------------
    # Step 2 — After configuration saved: connect to server → open login
    # -------------------------------------------------------------------
    def open_login(self, config_data):
        host = config_data["host"]
        port = config_data["port"]

        print(f"Connecting to FTP server at {host}:{port}")

        # Set server details
        self.client.set_server(host, port)

        # Connect WITHOUT host/port arguments
        if not self.client.connect():
            print("Connection failed.")
            return

        print("Connected successfully to server.")

        self.config_window.close()

        # Open login window (pass the connected client)
        self.login_window = LoginWindow(self.client)
        self.login_window.login_success.connect(self.open_dashboard)
        self.login_window.show()

    # -------------------------------------------------------------------
    # Step 3 — After login, open dashboard with permissions
    # -------------------------------------------------------------------
    def open_dashboard(self, login_data):

        username = login_data["username"]
        permissions = login_data["permissions"]

        print(f"User logged in: {username}")
        print("Permissions:", permissions)

        self.login_window.close()

        # DashboardWindow expects: (client_socket, username, permissions)
        self.dashboard = DashboardWindow(
            client_socket=self.client,
            username=username,
            permissions=permissions
        )

        self.dashboard.show()

    # -------------------------------------------------------------------
    # Start app loop
    # -------------------------------------------------------------------
    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = MainApp()
    app.run()
