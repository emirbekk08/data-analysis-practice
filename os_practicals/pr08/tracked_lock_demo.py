#!/usr/bin/env python3
"""Teaching wrapper for lock-order cycle detection."""
import threading

class LockOrderTracker:
    def __init__(self):
        self.graph = {}
        self.held = {}
        self.guard = threading.Lock()

    def before_acquire(self, thread_id, lock_name):
        with self.guard:
            self.graph.setdefault(lock_name, set())
            for held_name in self.held.get(thread_id, []):
                self.graph.setdefault(held_name, set()).add(lock_name)
            cycle = self.find_cycle()
            if cycle:
                # Remove newest dependency to avoid leaving a false edge.
                for held_name in self.held.get(thread_id, []):
                    self.graph.get(held_name, set()).discard(lock_name)
                raise RuntimeError("Potential lock-order deadlock: " + " -> ".join(cycle))

    def acquired(self, thread_id, lock_name):
        with self.guard:
            self.held.setdefault(thread_id, []).append(lock_name)

    def released(self, thread_id, lock_name):
        with self.guard:
            held = self.held.get(thread_id, [])
            if lock_name in held:
                held.remove(lock_name)

    def find_cycle(self):
        color = {}
        parent = {}
        def dfs(u):
            color[u] = 1
            for v in self.graph.get(u, set()):
                if color.get(v, 0) == 1:
                    return [v, u, v]
                if color.get(v, 0) == 0:
                    parent[v] = u
                    result = dfs(v)
                    if result:
                        return result
            color[u] = 2
            return None
        for node in self.graph:
            if color.get(node, 0) == 0:
                result = dfs(node)
                if result:
                    return result
        return None

class TrackedLock:
    def __init__(self, name, tracker):
        self.name = name
        self.tracker = tracker
        self.lock = threading.Lock()

    def acquire(self):
        tid = threading.get_ident()
        self.tracker.before_acquire(tid, self.name)
        self.lock.acquire()
        self.tracker.acquired(tid, self.name)

    def release(self):
        tid = threading.get_ident()
        self.lock.release()
        self.tracker.released(tid, self.name)

def main():
    tracker = LockOrderTracker()
    lock_a = TrackedLock("A", tracker)
    lock_b = TrackedLock("B", tracker)

    # Sequentially demonstrate inverted lock ordering without hanging.
    lock_a.acquire()
    lock_a.release()
    lock_b.acquire()
    lock_b.release()

    # Add observed dependency B -> A; next A -> B creates a cycle.
    tracker.graph.setdefault("B", set()).add("A")
    try:
        lock_a.acquire()
        lock_a.release()
        lock_b.acquire()
        lock_b.release()
        # Thread holds A, so request B adds A -> B; with B -> A it detects cycle.
        lock_a.acquire()
        try:
            lock_b.acquire()
        finally:
            lock_a.release()
    except RuntimeError as exc:
        print("Detected:", exc)
    print("Dependency graph:", {k: sorted(v) for k, v in tracker.graph.items()})

if __name__ == "__main__":
    main()
