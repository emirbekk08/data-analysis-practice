#!/usr/bin/env python3
"""FIFO client: python3 fifo_client.py '2 + 2'"""
import os
import sys
import uuid

REQUEST_FIFO = "/tmp/os_pr7_request.fifo"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pr07/fifo_client.py '12 * (3 + 4)'")
        raise SystemExit(2)
    expression = " ".join(sys.argv[1:])
    reply_fifo = f"/tmp/os_pr7_reply_{os.getpid()}_{uuid.uuid4().hex[:8]}.fifo"
    os.mkfifo(reply_fifo, 0o600)
    try:
        with open(REQUEST_FIFO, "w", encoding="utf-8") as req:
            req.write(f"{expression}\t{reply_fifo}\n")
        with open(reply_fifo, "r", encoding="utf-8") as response:
            print(response.read().strip())
    finally:
        try:
            os.unlink(reply_fifo)
        except FileNotFoundError:
            pass

if __name__ == "__main__":
    main()
