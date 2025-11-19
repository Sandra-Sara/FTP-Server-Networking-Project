import sys
from PyQt5.QtWidgets import QApplication

# Import UI windows
from frontend.welcome_window import ConfigWindow
from frontend.login_window import LoginWindow
from frontend.dashboard_window import DashboardWindow


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Step 1: Start with Welcome/Configuration window
        self.config_window = ConfigWindow()
        self.config_window.config_complete.connect(self.open_login)

        self.config_window.show()

    # Step 2: After config saved → open Login window
    def open_login(self, config_data):
        self.config = config_data
        print("Loaded config:", self.config)

        # Extract login credentials from welcome_window input
        saved_username = self.config.get("username")
        saved_password = self.config.get("password")

        # Pass credentials to LoginWindow
        self.login_window = LoginWindow(saved_username, saved_password)
        self.login_window.login_success.connect(self.open_dashboard)

        self.config_window.close()
        self.login_window.show()

    # Step 3: After successful login → open Dashboard
    def open_dashboard(self, username):
        print("Logged in as:", username)

        self.dashboard = DashboardWindow(username=username, config=self.config)

        self.login_window.close()
        self.dashboard.show()

    # Run app loop
    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = MainApp()
    app.run()
