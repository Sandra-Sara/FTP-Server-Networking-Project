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

def interactive(host="127.0.0.1", port=2121):
    sock = socket.create_connection((host, port))
    print(recv_line(sock))  # banner

    def send_line(line):
        sock.sendall((line + "\r\n").encode("utf-8"))
        resp = recv_line(sock)
        return resp

    # simple login flow
    username = input("USER: ")
    print(send_line(f"USER {username}"))
    password = input("PASS: ")
    print(send_line(f"PASS {password}"))

    while True:
        cmd = input("ftp> ").strip()
        if not cmd:
            continue
        parts = cmd.split()
        verb = parts[0].upper()
        if verb == "STOR":
            if len(parts) != 2:
                print("Usage: STOR <local_path>")
                continue
            local = Path(parts[1])
            if not local.exists() or not local.is_file():
                print("Local file not found")
                continue
            size = local.stat().st_size
            remote_name = local.name
            print(send_line(f"STOR {remote_name} {size}"))
            # send file bytes
            with open(local, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sock.sendall(chunk)
            # read final replies (may be multiple)
            while True:
                r = recv_line(sock)
                if r is None:
                    print("Connection closed")
                    return
                print(r)
                if r.startswith("226") or r.startswith("426"):
                    break

        elif verb == "RETR":
            if len(parts) != 2:
                print("Usage: RETR <remote_filename>")
                continue
            remote = parts[1]
            sock.sendall((f"RETR {remote}\r\n").encode("utf-8"))
            resp = recv_line(sock)
            print(resp)
            if resp is None:
                return
            if not resp.startswith("150"):
                continue
            # parse size
            try:
                _, size_s = resp.split(None, 1)
                size = int(size_s.strip())
            except Exception:
                print("Invalid server response")
                continue
            remaining = size
            out = b""
            while remaining > 0:
                chunk = sock.recv(min(8192, remaining))
                if not chunk:
                    print("Connection closed during transfer")
                    return
                out += chunk
                remaining -= len(chunk)
            # next textual lines
            end = recv_line(sock)
            finish = recv_line(sock)
            print(end)
            print(finish)
            # write to file
            localname = Path(remote).name
            with open(localname, "wb") as f:
                f.write(out)
            print(f"Saved as {localname}")

        else:
            # generic
            sock.sendall((cmd + "\r\n").encode("utf-8"))
            while True:
                r = recv_line(sock)
                if r is None:
                    return
                print(r)
                # break after one reply for simple commands
                break

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) >= 2 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) >= 3 else 2121
    interactive(host, port)
