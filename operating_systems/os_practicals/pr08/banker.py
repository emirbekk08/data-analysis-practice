#!/usr/bin/env python3
"""Banker's algorithm with safe-state check and rollback for requests."""
import json
import sys
from copy import deepcopy

def calculate_need(maximum, allocation):
    return [
        [maximum[i][j] - allocation[i][j] for j in range(len(maximum[i]))]
        for i in range(len(maximum))
    ]

def safety(available, allocation, maximum):
    need = calculate_need(maximum, allocation)
    work = available[:]
    finished = [False] * len(allocation)
    sequence = []
    changed = True
    while changed:
        changed = False
        for i in range(len(allocation)):
            if not finished[i] and all(need[i][j] <= work[j] for j in range(len(work))):
                work = [work[j] + allocation[i][j] for j in range(len(work))]
                finished[i] = True
                sequence.append(i)
                changed = True
    return all(finished), sequence

def request_resources(pid, request, available, allocation, maximum):
    n = len(allocation)
    if pid < 0 or pid >= n:
        return False, "Invalid process id"
    need = calculate_need(maximum, allocation)
    if any(x < 0 for x in request):
        return False, "Request cannot contain negative values"
    if any(request[j] > need[pid][j] for j in range(len(request))):
        return False, "Request exceeds process Need"
    if any(request[j] > available[j] for j in range(len(request))):
        return False, "Request exceeds Available resources"

    old_available = available[:]
    old_alloc = deepcopy(allocation)
    for j in range(len(request)):
        available[j] -= request[j]
        allocation[pid][j] += request[j]

    safe, sequence = safety(available, allocation, maximum)
    if safe:
        return True, "Granted; safe sequence: " + " -> ".join(f"P{i}" for i in sequence)

    available[:] = old_available
    allocation[:] = old_alloc
    return False, "Denied; state would be unsafe (changes rolled back)"

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 pr08/banker.py pr08/bank1.json")
        raise SystemExit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        state = json.load(f)
    available = state["available"]
    allocation = state["allocation"]
    maximum = state["max"]
    safe, sequence = safety(available, allocation, maximum)
    print("Available:", available)
    print("Need:")
    for i, row in enumerate(calculate_need(maximum, allocation)):
        print(f"P{i}: {row}")
    if safe:
        print("SAFE:", " -> ".join(f"P{i}" for i in sequence))
    else:
        print("UNSAFE")

    print("\nEnter request as: P1 1 0 2 (or 'quit')")
    while True:
        try:
            line = input("request> ").strip()
        except EOFError:
            break
        if line.lower() in {"quit", "exit", "q"}:
            break
        parts = line.split()
        if len(parts) != len(available) + 1 or not parts[0].upper().startswith("P"):
            print("Invalid format. Example: P1 1 0 2")
            continue
        try:
            pid = int(parts[0][1:])
            request = [int(x) for x in parts[1:]]
        except ValueError:
            print("Invalid process or resource number")
            continue
        granted, message = request_resources(
            pid, request, available, allocation, maximum
        )
        print(("GRANTED: " if granted else "DENIED: ") + message)
        print("Available now:", available)

if __name__ == "__main__":
    main()
