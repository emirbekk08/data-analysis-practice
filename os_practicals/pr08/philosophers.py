#!/usr/bin/env python3
"""Dining philosophers: naive deadlock, ordered locks, and waiter semaphore."""
import argparse
import multiprocessing as mp
import threading
import time
from multiprocessing import Event, Process, Queue, Semaphore

N = 5

def worker(i, forks, mode, stop, stats, waiter=None):
    meals = 0
    max_wait = 0.0
    left, right = forks[i], forks[(i + 1) % N]
    while not stop.is_set():
        start = time.perf_counter()
        if mode == "deadlock":
            left.acquire()
            # Synchronize all philosophers after taking the left fork to reproduce deadlock.
            if not hasattr(worker, "_barrier"):
                pass
            right.acquire()
        elif mode == "ordered":
            first, second = (left, right) if i < (i + 1) % N else (right, left)
            first.acquire()
            second.acquire()
        elif mode == "waiter":
            waiter.acquire()
            left.acquire()
            right.acquire()
        waited = time.perf_counter() - start
        max_wait = max(max_wait, waited)
        time.sleep(0.002)
        meals += 1
        if mode == "deadlock":
            # If it reaches here, release normally; otherwise intentionally remains blocked.
            right.release()
            left.release()
        else:
            right.release()
            left.release()
            if mode == "waiter":
                waiter.release()
        time.sleep(0.001)
    stats.put((i, meals, max_wait))

def run_deadlock(seconds):
    # Separate processes let parent terminate a deliberately deadlocked demonstration safely.
    forks = [mp.Lock() for _ in range(N)]
    stop = mp.Event()
    stats = mp.Queue()
    ready = mp.Barrier(N)
    def deadlock_worker(i):
        left, right = forks[i], forks[(i + 1) % N]
        left.acquire()
        try:
            ready.wait(timeout=2)
        except Exception:
            pass
        right.acquire()
        left.release()
        right.release()
    processes = [mp.Process(target=deadlock_worker, args=(i,)) for i in range(N)]
    for p in processes:
        p.start()
    time.sleep(seconds)
    alive = [i for i, p in enumerate(processes) if p.is_alive()]
    print(f"Naive mode ran for {seconds:.1f}s.")
    print("Processes still blocked (evidence of deadlock):", alive)
    for p in processes:
        if p.is_alive():
            p.terminate()
        p.join()
    print("Demo processes terminated safely.")

def run_correct(mode, seconds):
    forks = [threading.Lock() for _ in range(N)]
    stop = threading.Event()
    waiter = threading.Semaphore(N - 1) if mode == "waiter" else None
    results = [None] * N
    def philosopher(i):
        meals = 0
        max_wait = 0.0
        left, right = forks[i], forks[(i + 1) % N]
        while not stop.is_set():
            start = time.perf_counter()
            if mode == "ordered":
                first, second = (left, right) if i < (i + 1) % N else (right, left)
                first.acquire()
                second.acquire()
            else:
                waiter.acquire()
                left.acquire()
                right.acquire()
            max_wait = max(max_wait, time.perf_counter() - start)
            time.sleep(0.002)
            meals += 1
            right.release()
            left.release()
            if mode == "waiter":
                waiter.release()
            time.sleep(0.001)
        results[i] = (meals, max_wait)
    threads = [threading.Thread(target=philosopher, args=(i,), daemon=True) for i in range(N)]
    for t in threads:
        t.start()
    time.sleep(seconds)
    stop.set()
    for t in threads:
        t.join(timeout=2)
    print(f"Mode: {mode}; duration: {seconds:.1f}s")
    for i, result in enumerate(results):
        print(f"P{i}: meals={result[0] if result else 0}, max_wait={result[1] if result else 0:.6f}s")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["deadlock", "ordered", "waiter"], default="ordered")
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if args.mode == "deadlock":
        run_deadlock(args.seconds)
    else:
        run_correct(args.mode, args.seconds)

if __name__ == "__main__":
    mp.freeze_support()
    main()
