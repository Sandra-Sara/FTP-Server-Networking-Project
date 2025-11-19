LockBox FTP — Secure FTP Client & Server (Python + PyQt5)
A modern, fully customizable FTP Server and GUI-based FTP Client built with Python, PyQt5, and Sockets.
LockBox FTP provides a clean, professional interface with user authentication, file operations, and server-side permission control.
Features:

FTP Server (Python Sockets)
Custom FTP-like command system
USER, PASS, LIST, STOR, RETR, DELE implemented
User accounts stored in accounts.json
Per-user permissions (read, write, delete)
Supports multiple clients
Clean threaded implementation
Safe directory isolation (each user has its own folder)

FTP Client (PyQt5)
Fully interactive graphical client
Beautiful modern UI (Windows 11 style)
Auto-connect through config screen
User login with server verification
File manager dashboard:
List files
Upload files
download files
Delete files
Logout

Project Structure:
LockBox-FTP/
│
├── backend/
│   ├── client_socket.py       # FTP client socket handler
│
├── frontend/
│   ├── welcome_window.py      # Host + port configuration screen
│   ├── login_window.py        # User login UI
│   ├── dashboard_window.py    # Main file manager UI
│
├── Server/
│   ├── server.py              # FTP server implementation
│   ├── accounts.json          # User credentials and permissions
│   ├── storage/               # User files are stored here
│
├── main.py                    # Entry point for client GUI
└── README.md

Installation
Install Python
Make sure you have Python 3.10 or newer installed.
Install Dependencies
pip install PyQt5

Running the FTP Server
Go to the Server folder and run:
python server.py
You should see:
Server running on 0.0.0.0:2121
Users are managed in:
FTP Server/ftp_users.db
For account insertion before running server.py run server.py --init for the first time,that's how in ftp_users.db the users are created.Then run server.py as usual.

Running the FTP Client (GUI)
From your main project directory:
python main.py

Application flow:
Welcome Window → Enter server host & port
Login Window → Enter username/password
Dashboard → Manage files

Supported FTP Commands
Client ➜ Server
Command	Description
USER <name>	Send username
PASS <password>	Send password
LIST	List files
STOR <filename>	Upload file
RETR <filename>	Download file
DELE <filename>	Delete file
Server ➜ Client
Response	Meaning
220	Server ready
230	Login success
430	Invalid credentials
550	No permission or file not found
150	File action OK
226	File transfer complete

Testing
To test file upload/download:
Start server
Login using GUI
Upload a file
Check folder:
Server/storage/<username>/


