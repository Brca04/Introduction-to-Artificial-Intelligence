import argparse
from collections import deque
import heapq


def load_state_space(path):
    lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)

    s0 = lines[0]
    goals = set(lines[1].split())
    succ = {}

    for line in lines[2:]:
        parts = line.split(':')
        state = parts[0].strip()
        neighbors = []
        rest = parts[1].strip()
        if rest:
            for item in rest.split():
                i = item.rfind(',')
                neighbors.append((item[:i], float(item[i+1:])))
        succ[state] = neighbors

    return s0, goals, succ


def load_heuristic(path):
    h = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(':')
                h[parts[0].strip()] = float(parts[1].strip())
    return h


def bfs(s0, goals, succ):
    waiting = deque([(s0, [s0], 0.0)])  # (state, path, cost)
    closed = set()

    while waiting:
        state, path, cost = waiting.popleft()
        
        if state in closed:
            continue
        closed.add(state)

        if state in goals:
            return True, len(closed), path, cost
        
        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]):
            if nxt not in closed:
                waiting.append((nxt, path + [nxt], cost + c))

    return False, len(closed), [], 0.0


def ucs(s0, goals, succ):
    cnt = 0
    heap = [(0.0, cnt, s0, [s0])]  # (state, path, cnt, cost)
    closed = set()

    while heap:
        cost, cnt, state, path = heap[0]
        heapq.heappop(heap)

        if state in closed:
            continue
        closed.add(state)

        if state in goals:
            return True, len(closed), path, cost
        
        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]):
            if nxt not in closed:
                cnt += 1
                heapq.heappush(heap, (cost + c, cnt, nxt, path + [nxt]))

    return False, len(closed), [], 0.0


def astar(s0, goals, succ, h):
    waiting = [(s0, [s0], 0.0, h[s0])]  # open ← [ initial(s0) ]
    closed = {}  # closed ← ∅ 

    while waiting: # while open != [ ] do
        state, path, cost, f_value = waiting[0]  # n ← removeHead(open)
        waiting = waiting[1:]

        if state in goals: # if goal(state(n)) then return n
            return True, len(closed), path, cost

        closed[state] = cost # closed ← closed ∪ { n }

        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]):
            if nxt in closed:
                if cost + c < closed[nxt]: # if g(m0) < g(m) then continue
                    del closed[nxt] # remove(m0, closed ∪ open)

            # insertSortedBy(f, m, open)
            waiting.append((nxt, path + [nxt], cost + c, cost + c + h[nxt])) # open ← open ∪ { m }
            waiting.sort(key=lambda x: (x[3], x[0]))  # sort by f_value, then by state name

    return False, len(closed), [], 0.0
    pass


def check_optimistic(goals, succ, h, h_path):
    print("# HEURISTIC-OPTIMISTIC {}".format(h_path))

    # Build reverse graph
    rev = {}
    for state, neighbors in succ.items():
        for nxt, c in neighbors:
            rev.setdefault(nxt, []).append((state, c))

    # Multi-source Dijkstra from all goals on reverse graph
    hstar_value = {}
    heap = []
    for g in goals:
        heapq.heappush(heap, (0.0, g))

    while heap:
        cost, state = heapq.heappop(heap)
        if state in hstar_value:
            continue
        hstar_value[state] = cost
        for pred, c in rev.get(state, []):
            if pred not in hstar_value:
                heapq.heappush(heap, (cost + c, pred))

    optimistic = True
    for state in sorted(h.keys()):
        hval = h[state]
        hstar = hstar_value.get(state, float('inf'))

        if hval <= hstar:
            print("[CONDITION]: [OK] h({}) <= h*: {:.1f} <= {:.1f}".format(state, hval, hstar))
        else:
            print("[CONDITION]: [ERR] h({}) <= h*: {:.1f} <= {:.1f}".format(state, hval, hstar))
            optimistic = False

    if optimistic:
        print("[CONCLUSION]: Heuristic is optimistic.")
    else:
        print("[CONCLUSION]: Heuristic is not optimistic.")


def check_consistent(succ, h, h_path):
    print("# HEURISTIC-CONSISTENT {}".format(h_path))
    consistent = True

    for state in sorted(succ.keys()):
        for nxt, c in sorted(succ[state], key=lambda x: x[0]):
            hs = h.get(state, 0.0)
            ht = h.get(nxt, 0.0)

            if hs <= ht + c:
                print("[CONDITION]: [OK] h({}) <= h({}) + c: {:.1f} <= {:.1f} + {:.1f}".format(
                    state, nxt, hs, ht, c))
            else:
                print("[CONDITION]: [ERR] h({}) <= h({}) + c: {:.1f} <= {:.1f} + {:.1f}".format(
                    state, nxt, hs, ht, c))
                consistent = False

    if consistent:
        print("[CONCLUSION]: Heuristic is consistent.")
    else:
        print("[CONCLUSION]: Heuristic is not consistent.")


def print_result(alg, found, visited, path, cost, h_path=None):
    if h_path:
        print("# {} {}".format(alg, h_path))
    else:
        print("# {}".format(alg))

    if found:
        print("[FOUND_SOLUTION]: yes")
        print("[STATES_VISITED]: {}".format(visited))
        print("[PATH_LENGTH]: {}".format(len(path)))
        print("[TOTAL_COST]: {:.1f}".format(cost))
        print("[PATH]: {}".format(" => ".join(path)))
    else:
        print("[FOUND_SOLUTION]: no")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--alg', type=str)
    parser.add_argument('--ss', type=str)
    parser.add_argument('--h', type=str)
    parser.add_argument('--check-optimistic', action='store_true')
    parser.add_argument('--check-consistent', action='store_true')
    args = parser.parse_args()

    s0, goals, succ = load_state_space(args.ss)

    h = None
    if args.h:
        h = load_heuristic(args.h)

    if args.alg == 'bfs':
        found, vis, path, cost = bfs(s0, goals, succ)
        print_result('BFS', found, vis, path, cost)
    elif args.alg == 'ucs':
        found, vis, path, cost = ucs(s0, goals, succ)
        print_result('UCS', found, vis, path, cost)
    elif args.alg == 'astar':
        found, vis, path, cost = astar(s0, goals, succ, h)
        print_result('A-STAR', found, vis, path, cost, args.h)

    if args.check_optimistic:
        check_optimistic(goals, succ, h, args.h)
    if args.check_consistent:
        check_consistent(succ, h, args.h)