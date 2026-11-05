# OS Practicals 7–8 — Variant B

Python 3.10+; Linux/Ubuntu/WSL recommended. No third-party packages required.

## Layout
- `pr07/fifo_server.py`, `pr07/fifo_client.py`: client/server using two named FIFOs.
- `pr07/unix_server.py`, `pr07/unix_client.py`: Unix-domain socket service; concurrent clients via threads.
- `pr07/benchmark.py`: compares sending 10^7 int64 values through shared memory versus multiprocessing Pipe.
- `pr08/banker.py`: Banker's safety algorithm, reads JSON state and accepts requests from stdin.
- `pr08/bank1.json`, `pr08/bank2.json`: safe and unsafe states.
- `pr08/wait_graph.py`: DFS cycle detection for acquire/release/wait event logs.
- `pr08/tracked_lock_demo.py`: lock wrapper detects simple lock-order cycles before blocking.
- `pr08/philosophers.py`: deadlock demo and two corrected variants with meal counts.

## Run PR-7 FIFO client/server (two terminals)
Terminal 1:
```bash
python3 pr07/fifo_server.py
```
Terminal 2:
```bash
python3 pr07/fifo_client.py "12 * (3 + 4)"
```
Repeat the client command as needed. Server handles one request at a time. Stop server with Ctrl+C; FIFOs are removed on shutdown.

Supported arithmetic: numbers, parentheses, + - * / // % **. No arbitrary Python code is evaluated.

## Run PR-7 Unix socket server/client
Terminal 1:
```bash
python3 pr07/unix_server.py
```
Terminal 2:
```bash
python3 pr07/unix_client.py "12 * (3 + 4)"
```
Concurrent clients:
```bash
for x in "2+2" "10/2" "7**2"; do python3 pr07/unix_client.py "$x" & done
wait
```
Stop server with Ctrl+C. Socket file is removed on shutdown.

## Run PR-7 benchmark
```bash
python3 pr07/benchmark.py
```
This sends an array of 10,000,000 int64 values. It reports wall time and approximate throughput. Runtime and memory use depend on machine. Pipe version serializes the array and is expected to be slower/more memory intensive than shared memory. Results are measurements, not hard-coded claims.

## Run PR-8 Banker's algorithm
```bash
python3 pr08/banker.py pr08/bank1.json
python3 pr08/banker.py pr08/bank2.json
```
Then enter a request such as:
```text
P1 1 0 2
```
Enter `quit` to exit. The request is tentatively applied and rolled back if it exceeds Need/Available or makes the state unsafe.

Expected initial state:
- bank1: safe sequence `P1 P3 P4 P2 P0`
- bank2: `UNSAFE`

## Run wait-graph detector
```bash
python3 pr08/wait_graph.py pr08/events_deadlock.json
python3 pr08/wait_graph.py pr08/events_safe.json
```
The event log uses single-instance resources. A cycle in the wait-for graph indicates deadlock.

## Run TrackedLock demo
```bash
python3 pr08/tracked_lock_demo.py
```
The program demonstrates that lock-order inversion can be detected by the wrapper. This is a teaching detector; it detects cycles in observed lock-order dependencies and is not a general-purpose replacement for OS/thread debugging tools.

## Run dining philosophers
```bash
python3 pr08/philosophers.py --mode deadlock --seconds 3
python3 pr08/philosophers.py --mode ordered --seconds 10
python3 pr08/philosophers.py --mode waiter --seconds 10
```
The naive mode intentionally can deadlock; it runs in child processes and is forcibly cleaned up after the time limit. Corrected modes report meal counts and maximum observed wait.

## Clean up
Servers remove their own FIFO/socket resources on normal Ctrl+C. To inspect leftovers:
```bash
ls -l /tmp/os_pr7_*.fifo /tmp/os_pr7_*.sock 2>/dev/null
```
Remove stale demo resources if needed:
```bash
rm -f /tmp/os_pr7_request.fifo /tmp/os_pr7_response.fifo /tmp/os_pr7.sock
```

## Suggested evidence for submission
Run each command above and copy terminal output into `results.txt` or screenshots. Include actual benchmark values from your computer; do not invent them.
