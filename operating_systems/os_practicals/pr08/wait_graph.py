#!/usr/bin/env python3
"""Build a wait-for graph from single-instance acquire/release/wait events and detect cycles."""
import json
import sys

def build_graph(events):
    owner = {}          # resource -> process
    graph = {}          # process -> set of processes it waits for
    waiting = {}        # process -> resource
    for e in events:
        kind, p = e["event"], e["process"]
        graph.setdefault(p, set())
        r = e["resource"]
        if kind == "acquire":
            if r not in owner:
                owner[r] = p
                waiting.pop(p, None)
            elif owner[r] != p:
                waiting[p] = r
                graph[p].add(owner[r])
        elif kind == "wait":
            waiting[p] = r
            if r in owner and owner[r] != p:
                graph[p].add(owner[r])
        elif kind == "release":
            if owner.get(r) == p:
                del owner[r]
                # A real scheduler would grant to a waiting process; this log
                # detector expects subsequent acquire events to record that grant.
                for waiter, resource in list(waiting.items()):
                    if resource == r:
                        graph[waiter].discard(p)
                        waiting.pop(waiter, None)
    return graph

def find_cycle(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    parent = {}
    def dfs(u):
        color[u] = GRAY
        for v in graph.get(u, set()):
            if v not in color:
                color[v] = WHITE
            if color[v] == GRAY:
                cycle = [v, u]
                while cycle[-1] != v:
                    prev = parent.get(cycle[-1])
                    if prev is None:
                        break
                    cycle.append(prev)
                cycle.reverse()
                return cycle
            if color[v] == WHITE:
                parent[v] = u
                result = dfs(v)
                if result:
                    return result
        color[u] = BLACK
        return None
    for node in list(color):
        if color[node] == WHITE:
            result = dfs(node)
            if result:
                return result
    return None

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "pr08/events_deadlock.json"
    with open(path, encoding="utf-8") as f:
        events = json.load(f)
    graph = build_graph(events)
    print("Wait-for graph:")
    for process, waits_for in graph.items():
        print(f"  {process} -> {sorted(waits_for)}")
    cycle = find_cycle(graph)
    if cycle:
        print("DEADLOCK CYCLE:", " -> ".join(cycle))
        print("Participants:", sorted(set(cycle)))
    else:
        print("No cycle detected.")

if __name__ == "__main__":
    main()
