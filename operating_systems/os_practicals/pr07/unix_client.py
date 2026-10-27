#!/usr/bin/env python3
"""Usage: python3 pr07/unix_client.py '3 * (4 + 2)'"""
import socket
import sys

SOCKET_PATH = "/tmp/os_pr7.sock"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pr07/unix_client.py '12 * (3 + 4)'")
        raise SystemExit(2)
    expression = " ".join(sys.argv[1:]) + "\n"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(SOCKET_PATH)
        client.sendall(expression.encode("utf-8"))
        response = b""
        while not response.endswith(b"\n"):
            chunk = client.recv(4096)
            if not chunk:
                break
            response += chunk
    print(response.decode("utf-8", errors="replace").strip())

if __name__ == "__main__":
    main()
