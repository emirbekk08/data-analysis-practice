#!/usr/bin/env python3
"""Compare passing 10^7 int64 values using shared memory and multiprocessing Pipe."""
import multiprocessing as mp
from multiprocessing import shared_memory
import time
import numpy as np

N = 10_000_000
DTYPE = np.int64

def shared_memory_receiver(name, shape, dtype_str, conn):
    shm = shared_memory.SharedMemory(name=name)
    try:
        array = np.ndarray(shape, dtype=np.dtype(dtype_str), buffer=shm.buf)
        # Touch the received array to ensure access occurred.
        checksum = int(array[0]) + int(array[-1])
        conn.send(checksum)
    finally:
        shm.close()
        conn.close()

def pipe_receiver(conn):
    array = conn.recv()
    conn.send((len(array), int(array[0]) + int(array[-1])))
    conn.close()

def main():
    print(f"Array: {N:,} elements, dtype={DTYPE}, payload={N * np.dtype(DTYPE).itemsize / 1e6:.1f} MB")
    source = np.arange(N, dtype=DTYPE)

    # Shared memory: copy into shared region, then send only metadata to child.
    shm = shared_memory.SharedMemory(create=True, size=source.nbytes)
    parent_conn, child_conn = mp.Pipe(duplex=True)
    proc = mp.Process(
        target=shared_memory_receiver,
        args=(shm.name, source.shape, source.dtype.str, child_conn)
    )
    start = time.perf_counter()
    try:
        target = np.ndarray(source.shape, dtype=source.dtype, buffer=shm.buf)
        target[:] = source
        proc.start()
        child_conn.close()
        checksum = parent_conn.recv()
        proc.join()
        shared_elapsed = time.perf_counter() - start
        print(f"Shared memory elapsed: {shared_elapsed:.4f} s; checksum={checksum}; effective copy throughput={source.nbytes / shared_elapsed / 1e6:.1f} MB/s")
    finally:
        parent_conn.close()
        if proc.is_alive():
            proc.terminate()
            proc.join()
        shm.close()
        shm.unlink()

    # Pipe: pickle and transfer the full array to child.
    parent_conn, child_conn = mp.Pipe(duplex=True)
    proc = mp.Process(target=pipe_receiver, args=(child_conn,))
    start = time.perf_counter()
    try:
        proc.start()
        child_conn.close()
        parent_conn.send(source)
        received_len, checksum = parent_conn.recv()
        proc.join()
        pipe_elapsed = time.perf_counter() - start
        print(f"Pipe elapsed: {pipe_elapsed:.4f} s; received={received_len:,}; checksum={checksum}; effective throughput={source.nbytes / pipe_elapsed / 1e6:.1f} MB/s")
    finally:
        parent_conn.close()
        if proc.is_alive():
            proc.terminate()
            proc.join()

    print("\nNote: timings include process startup and serialization. Run several times for a more stable comparison.")

if __name__ == "__main__":
    mp.freeze_support()
    main()
