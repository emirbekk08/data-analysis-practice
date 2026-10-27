import sys
import argparse
from collections import deque
import copy

class Process:
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.remaining_burst = burst
        self.start_time = -1
        self.finish_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = -1

def load_processes(filename):
    processes = []
    with open(filename, 'r') as f:
        for line in f:
            if not line.strip(): continue
            parts = line.split()
            pid = parts[0]
            arrival = int(parts[1])
            burst = int(parts[2])
            priority = int(parts[3]) if len(parts) > 3 else 0
            processes.append(Process(pid, arrival, burst, priority))
    return processes

def simulate(processes, algorithm, **params):
    procs = [copy.deepcopy(p) for p in processes]
    procs.sort(key=lambda x: x.arrival)
    intervals = []
    current_time = 0
    completed = 0
    n = len(procs)
    
    if algorithm == 'FCFS':
        for p in procs:
            if current_time < p.arrival: current_time = p.arrival
            p.start_time = current_time
            p.response_time = current_time - p.arrival
            current_time += p.burst
            p.finish_time = current_time
            p.turnaround_time = p.finish_time - p.arrival
            p.waiting_time = p.turnaround_time - p.burst
            intervals.append((p.pid, p.start_time, p.finish_time))
            
    elif algorithm == 'SRTF':
        prev_p = None
        start_step = 0
        while completed < n:
            ready = [p for p in procs if p.arrival <= current_time and p.remaining_burst > 0]
            if not ready:
                if prev_p:
                    intervals.append((prev_p.pid, start_step, current_time))
                    prev_p = None
                current_time = min(p.arrival for p in procs if p.remaining_burst > 0)
                continue
            p = min(ready, key=lambda x: x.remaining_burst)
            if prev_p and prev_p.pid != p.pid:
                intervals.append((prev_p.pid, start_step, current_time))
                prev_p = None
            if p.response_time == -1:
                p.response_time = current_time - p.arrival
            if not prev_p:
                prev_p = p
                start_step = current_time
            p.remaining_burst -= 1
            current_time += 1
            if p.remaining_burst == 0:
                intervals.append((p.pid, start_step, current_time))
                p.finish_time = current_time
                p.turnaround_time = p.finish_time - p.arrival
                p.waiting_time = p.turnaround_time - p.burst
                completed += 1
                prev_p = None

    elif algorithm == 'RR':
        quantum = params.get('quantum', 3)
        queue = deque()
        idx = 0
        if idx < len(procs) and current_time < procs[idx].arrival:
            current_time = procs[idx].arrival
        
        while completed < n:
            while idx < len(procs) and procs[idx].arrival <= current_time:
                queue.append(procs[idx])
                idx += 1
            if not queue:
                current_time = procs[idx].arrival
                continue
            p = queue.popleft()
            if p.response_time == -1:
                p.response_time = current_time - p.arrival
            exec_time = min(p.remaining_burst, quantum)
            intervals.append((p.pid, current_time, current_time + exec_time))
            current_time += exec_time
            p.remaining_burst -= exec_time
            
            while idx < len(procs) and procs[idx].arrival <= current_time:
                queue.append(procs[idx])
                idx += 1
            if p.remaining_burst > 0:
                queue.append(p)
            else:
                p.finish_time = current_time
                p.turnaround_time = p.finish_time - p.arrival
                p.waiting_time = p.turnaround_time - p.burst
                completed += 1

    elif algorithm == 'MLFQ':
        q0, q1, q2 = deque(), deque(), deque()
        p_level = {p.pid: 0 for p in procs}
        idx = 0
        while completed < n:
            while idx < len(procs) and procs[idx].arrival <= current_time:
                q0.append(procs[idx])
                idx += 1
            if not q0 and not q1 and not q2:
                current_time = procs[idx].arrival
                continue
            
            if q0: q, quantum, level = q0, 2, 0
            elif q1: q, quantum, level = q1, 4, 1
            else: q, quantum, level = q2, 999, 2
                
            p = q.popleft()
            if p.response_time == -1: p.response_time = current_time - p.arrival
            exec_time = min(p.remaining_burst, quantum)
            intervals.append((p.pid, current_time, current_time + exec_time))
            current_time += exec_time
            p.remaining_burst -= exec_time
            
            while idx < len(procs) and procs[idx].arrival <= current_time:
                q0.append(procs[idx])
                idx += 1
                
            if p.remaining_burst > 0:
                next_level = min(level + 1, 2)
                p_level[p.pid] = next_level
                if next_level == 1: q1.append(p)
                else: q2.append(p)
            else:
                p.finish_time = current_time
                p.turnaround_time = p.finish_time - p.arrival
                p.waiting_time = p.turnaround_time - p.burst
                completed += 1

    avg_waiting = sum(p.waiting_time for p in procs) / n
    avg_turnaround = sum(p.turnaround_time for p in procs) / n
    return avg_waiting, avg_turnaround, intervals

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--algo', type=str, required=True)
    parser.add_argument('--quantum', type=int, default=3)
    parser.add_argument('file', type=str)
    args = parser.parse_args()
    
    procs = load_processes(args.file)
    w, t, chart = simulate(procs, args.algo.upper(), quantum=args.quantum)
    print(f"Алгоритм: {args.algo.upper()}")
    print(f"Среднее ожидание: {w:.2f}")
    print(f"Средний оборот: {t:.2f}")
