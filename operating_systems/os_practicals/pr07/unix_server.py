#!/usr/bin/env python3
"""Concurrent arithmetic server over a Unix domain stream socket."""
import ast
import operator
import os
import signal
import socket
import threading

SOCKET_PATH = "/tmp/os_pr7.sock"
OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.UAdd: operator.pos, ast.USub: operator.neg,
}

def safe_eval(expression):
    tree = ast.parse(expression, mode="eval")
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            a, b = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(b) > 100:
                raise ValueError("Exponent too large")
            result = OPS[type(node.op)](a, b)
            if abs(result) > 1e100:
                raise ValueError("Result too large")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](visit(node.operand))
        raise ValueError("Unsupported expression")
    return visit(tree)

def handle_client(conn, address):
    with conn:
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if len(data) > 65536:
                conn.sendall(b"ERROR\tRequest too large\n")
                return
        expression = data.decode("utf-8", errors="replace").strip()
        try:
            result = safe_eval(expression)
            response = f"OK\t{result}\n"
        except Exception as exc:
            response = f"ERROR\t{type(exc).__name__}: {exc}\n"
        conn.sendall(response.encode("utf-8"))

def main():
    try:
        os.unlink(SOCKET_PATH)
    except FileNotFoundError:
        pass
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o600)
    server.listen(20)
    server.settimeout(1.0)
    print(f"Unix socket server ready: {SOCKET_PATH}", flush=True)
    print("Ctrl+C to stop.", flush=True)
    try:
        while True:
            try:
                conn, address = server.accept()
            except socket.timeout:
                continue
            threading.Thread(
                target=handle_client, args=(conn, address), daemon=True
            ).start()
    except KeyboardInterrupt:
        print("\nStopping server.", flush=True)
    finally:
        server.close()
        try:
            os.unlink(SOCKET_PATH)
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    main()
