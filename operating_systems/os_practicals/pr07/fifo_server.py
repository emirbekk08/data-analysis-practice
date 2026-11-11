#!/usr/bin/env python3
"""FIFO arithmetic server. One request per line; response FIFO is per-client."""
import ast
import operator
import os
import signal
from pathlib import Path

REQUEST_FIFO = "/tmp/os_pr7_request.fifo"
RESPONSE_FIFO = "/tmp/os_pr7_response.fifo"
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
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent too large")
            value = OPS[type(node.op)](left, right)
            if abs(value) > 1e100:
                raise ValueError("Result too large")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](visit(node.operand))
        raise ValueError("Unsupported expression")
    return visit(tree)

def main():
    for path in (REQUEST_FIFO, RESPONSE_FIFO):
        try:
            os.mkfifo(path, 0o600)
        except FileExistsError:
            if not Path(path).is_fifo():
                raise RuntimeError(f"{path} exists and is not a FIFO")
    print(f"FIFO server ready. Request FIFO: {REQUEST_FIFO}", flush=True)
    print("Run fifo_client.py from another terminal. Ctrl+C to stop.", flush=True)
    try:
        while True:
            # Opening FIFO read-only blocks until a writer opens it.
            with open(REQUEST_FIFO, "r", encoding="utf-8") as req:
                for line in req:
                    line = line.strip()
                    if not line:
                        continue
                    # Protocol: expression<TAB>reply_fifo
                    try:
                        expression, reply_fifo = line.split("\t", 1)
                        result = safe_eval(expression)
                        response = f"OK\t{result}\n"
                    except Exception as exc:
                        try:
                            reply_fifo
                        except UnboundLocalError:
                            continue
                        response = f"ERROR\t{type(exc).__name__}: {exc}\n"
                    try:
                        with open(reply_fifo, "w", encoding="utf-8") as out:
                            out.write(response)
                    except OSError as exc:
                        print(f"Could not reply: {exc}", flush=True)
    except KeyboardInterrupt:
        print("\nStopping FIFO server.", flush=True)
    finally:
        for path in (REQUEST_FIFO, RESPONSE_FIFO):
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    main()
