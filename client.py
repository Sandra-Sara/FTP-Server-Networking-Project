#!/usr/bin/env python3
import socket
import sys
from pathlib import Path

def recv_line(sock):
    data = b""
    while True:
        ch = sock.recv(1)
        if not ch:
            return None
        data += ch
        if data.endswith(b"\r\n"):
            return data[:-2].decode("utf-8")


def recv_multiline_until(sock, end_prefix):
    """Receive multiple FTP lines until a line starting with specific prefix arrives."""
    lines = []
    while True:
        line = recv_line(sock)
        if line is None:
            break
        print(line)
        lines.append(line)
        if line.startswith(end_prefix):
            break
    return lines


def interactive(host="127.0.0.1", port=2121):
    sock = socket.create_connection((host, port))
    print(recv_line(sock))  # banner

    def send_line(line):
        sock.sendall((line + "\r\n").encode("utf-8"))
        resp = recv_line(sock)
        return resp

    # ------------------
    # LOGIN
    # ------------------
    username = input("USER: ")
    print(send_line(f"USER {username}"))
    password = input("PASS: ")
    print(send_line(f"PASS {password}"))

    # ------------------
    # COMMAND LOOP
    # ------------------
    while True:
        cmd = input("ftp> ").strip()
        if not cmd:
            continue

        parts = cmd.split()
        verb = parts[0].upper()

        # ----------------------------------------------------
        # LIST command (FIXED — SHOW ALL AT ONCE)
        # ----------------------------------------------------
        if verb == "LIST":
            sock.sendall(b"LIST\r\n")

            # read until 226 Done
            recv_multiline_until(sock, "226")
            continue

        # ----------------------------------------------------
        # STOR upload
        # ----------------------------------------------------
        elif verb == "STOR":
            if len(parts) != 2:
                print("Usage: STOR <local_path>")
                continue

            local = Path(parts[1])
            if not local.exists() or not local.is_file():
                print("Local file not found")
                continue

            size = local.stat().st_size
            remote_name = local.name

            sock.sendall((f"STOR {remote_name} {size}\r\n").encode("utf-8"))
            resp = recv_line(sock)
            print(resp)

            if not resp.startswith("150"):
                continue

            with open(local, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sock.sendall(chunk)

            # read final status
            recv_multiline_until(sock, "226")
            continue

        # ----------------------------------------------------
        # RETR download
        # ----------------------------------------------------
        elif verb == "RETR":
            if len(parts) != 2:
                print("Usage: RETR <remote_filename>")
                continue

            remote = parts[1]
            sock.sendall((f"RETR {remote}\r\n").encode("utf-8"))

            resp = recv_line(sock)
            print(resp)
            if not resp.startswith("150"):
                continue

            try:
                _, size_s = resp.split(None, 1)
                size = int(size_s.strip())
            except:
                print("Invalid size from server")
                continue

            data = b""
            remaining = size
            while remaining > 0:
                chunk = sock.recv(min(8192, remaining))
                if not chunk:
                    print("Connection lost during file transfer")
                    return
                data += chunk
                remaining -= len(chunk)

            # read "226 Transfer complete"
            finish = recv_line(sock)
            print(finish)

            # save file locally
            localname = Path(remote).name
            with open(localname, "wb") as f:
                f.write(data)

            print(f"Saved as {localname}")
            continue

        # ----------------------------------------------------
        # Generic single-response commands
        # ----------------------------------------------------
        else:
            sock.sendall((cmd + "\r\n").encode("utf-8"))
            resp = recv_line(sock)
            print(resp)
            continue


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) >= 2 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else 2121
    interactive(host, port)
