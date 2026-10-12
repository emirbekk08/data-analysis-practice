import sys


if len(sys.argv) != 2:
    print("Usage: python3 hello.py <file>", file=sys.stderr)
    sys.exit(1)

file_path = sys.argv[1]

try:
    with open(file_path, "rb") as file:
        data = file.read()
except FileNotFoundError:
    print(f"File not found: {file_path}", file=sys.stderr)
    sys.exit(1)
print(len(data))
