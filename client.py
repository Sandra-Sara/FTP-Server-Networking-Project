#!/usr/bin/env python3
import socket
import sys
import json
from pathlib import Path


def recv_line(sock):
    data = b""
    while True:
        ch = sock.recv(1)
        if not ch:
            return None
        data += ch
        if data.endswith(b"\n"):
            return data.decode().strip()


def recv_multiline(sock):
    """Receives lines until server sends END."""
    lines = []
    while True:
        line = recv_line(sock)
        if line is None:
            break

        if line == "END":
            break

        print(line)
        lines.append(line)

    return lines


def interactive(host="127.0.0.1", port=2121):
    sock = socket.create_connection((host, port))
    print(recv_line(sock))  # banner

    # --------------- AUTH -----------------
    username = input("Username: ")
    password = input("Password: ")

    sock.sendall(f"AUTH {username} {password}\n".encode())

    auth_response = recv_line(sock)
    print(auth_response)

    try:
        auth_data = json.loads(auth_response)
    except:
        print("Invalid authentication response from server.")
        return

    if auth_data.get("status") != "success":
        print("Login failed.")
        return

    print("Login OK. Permissions:", auth_data["permissions"])

    # --------------- COMMAND LOOP -----------------
    while True:
        cmd = input("ftp> ").strip()
        if not cmd:
            continue

        parts = cmd.split()
        verb = parts[0].upper()

        # -------- LIST --------
        if verb == "LIST":
            sock.sendall(b"LIST\n")
            recv_multiline(sock)
            continue

        # -------- UPLOAD --------
        elif verb == "UPLOAD":
            if len(parts) != 2:
                print("Usage: UPLOAD <local_path>")
                continue

            local = Path(parts[1])
            if not local.exists():
                print("File not found")
                continue

            size = local.stat().st_size
            name = local.name

            sock.sendall(f"UPLOAD {name} {size}\n".encode())

            resp = recv_line(sock)
            print(resp)

            if not resp.startswith("OK"):
                continue

            with open(local, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sock.sendall(chunk)

            print(recv_line(sock))
            continue

        # -------- DOWNLOAD --------
        elif verb == "DOWNLOAD":
            if len(parts) != 2:
                print("Usage: DOWNLOAD <remote_file>")
                continue

            remote = parts[1]
            sock.sendall(f"DOWNLOAD {remote}\n".encode())

            resp = recv_line(sock)
            print(resp)

            if not resp.startswith("OK"):
                continue

            _, size_s = resp.split()
            size = int(size_s)

            data = b""
            remain = size
            while remain > 0:
                chunk = sock.recv(8192)
                if not chunk:
                    print("Connection lost")
                    return
                data += chunk
                remain -= len(chunk)

            finish = recv_line(sock)
            print(finish)

            with open(remote, "wb") as f:
                f.write(data)

            print(f"Saved: {remote}")
            continue

        # -------- DELETE --------
        elif verb == "DELETE":
            if len(parts) != 2:
                print("Usage: DELETE <file>")
                continue

            sock.sendall(f"DELETE {parts[1]}\n".encode())
            print(recv_line(sock))
            continue

        # -------- RAW COMMANDS (PWD, CWD, QUIT) --------
        else:
            sock.sendall((cmd + "\n").encode())
            print(recv_line(sock))
            continue


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) >= 2 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else 2121
    interactive(host, port)
