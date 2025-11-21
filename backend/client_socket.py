import socket


class ClientSocket:
    def __init__(self, host="127.0.0.1", port=9000, timeout=10.0, logger=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket = None
        self.logger = logger   # ← NEW: shared logger instance

    # ----------------------------------------------------
    def log(self, text: str):
        """Send message to logger if available"""
        if self.logger:
            self.logger.append_log(f"[Client] {text}")
        print(text)

    # ----------------------------------------------------
    # SET HOST + PORT (from config window)
    # ----------------------------------------------------
    def set_server(self, host: str, port: int):
        self.host = host
        self.port = port
        self.log(f"Server set to {host}:{port}")

    # ----------------------------------------------------
    # CONNECT
    # ----------------------------------------------------
    def connect(self) -> bool:
        try:
            self.sock = socket.create_connection(
                (self.host, self.port),
                timeout=self.timeout
            )

            banner = self.receive()  # read welcome banner
            self.log(f"Connected to server at {self.host}:{self.port}")
            self.log(f"Server banner: {banner}")

            return True

        except Exception as e:
            self.log(f"Connection failed: {e}")
            return False

    # ----------------------------------------------------
    # SEND TEXT COMMAND
    # ----------------------------------------------------
    def send(self, msg: str):
        if not self.sock:
            raise Exception("Socket is not connected.")

        full_msg = msg + "\r\n"
        self.sock.sendall(full_msg.encode())
        self.log(f"Sent: {msg}")

    # ----------------------------------------------------
    # RECEIVE ONE LINE
    # ----------------------------------------------------
    def receive(self) -> str:
        if not self.sock:
            raise Exception("Socket is not connected.")

        buffer = b""
        while True:
            ch = self.sock.recv(1)
            if not ch:
                break
            buffer += ch
            if buffer.endswith(b"\r\n"):
                break

        text = buffer.decode().strip()
        self.log(f"Received: {text}")
        return text

    # ----------------------------------------------------
    # MULTILINE FOR LIST
    # ----------------------------------------------------
    def receive_multiline(self) -> str:
        lines = []

        while True:
            line = self.receive()
            lines.append(line)

            # LIST format ends with "226 Transfer complete"
            if line.startswith("226") or line.startswith("500"):
                break

        result = "\n".join(lines)
        self.log("Received multiline LIST response.")
        return result

    # ----------------------------------------------------
    # BYTES SEND (UPLOAD)
    # ----------------------------------------------------
    def send_bytes(self, data: bytes):
        if not self.sock:
            raise Exception("Socket is not connected.")

        self.sock.sendall(data)
        self.log(f"Sent {len(data)} bytes.")

    # ----------------------------------------------------
    # BYTES RECEIVE (DOWNLOAD)
    # ----------------------------------------------------
    def receive_bytes(self, size: int = None) -> bytes:
        if not self.sock:
            raise Exception("Socket is not connected.")

        if size is None:
            # receive until end
            chunks = []
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
            data = b"".join(chunks)
            self.log(f"Received {len(data)} bytes (unknown size).")
            return data

        # receive fixed size
        data = b""
        remaining = size

        while remaining > 0:
            chunk = self.sock.recv(min(4096, remaining))
            if not chunk:
                break
            data += chunk
            remaining -= len(chunk)

        self.log(f"Received {len(data)} / {size} bytes.")
        return data

    # ----------------------------------------------------
    # CLOSE CONNECTION
    # ----------------------------------------------------
    def close(self):
        if self.sock:
            try:
                self.sock.close()
                self.log("Connection closed.")
            except Exception as e:
                self.log(f"Error closing socket: {e}")

            self.sock = None
