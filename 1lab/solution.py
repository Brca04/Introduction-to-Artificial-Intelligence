# Uvod u umjetnu inteligenciju – Laboratorijska vjezba 1
# Bruno Cavor

import argparse
from collections import deque
import heapq


def load_state_space(path): # Ucitavanje prostora stanja
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


def load_heuristic(path): # Ucitavanje vrijednosti heuristike
    h = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(':')
                h[parts[0].strip()] = float(parts[1].strip())
    return h


def bfs(s0, goals, succ): # Pretrazivanje u sirinu (BFS)
    waiting = deque([(s0, [s0], 0.0)]) # open ← [ initial(s0) ]
    closed = set()

    while waiting: # while open ̸= [ ] do    
        state, path, cost = waiting.popleft() # n ← removeHead(open)
        
        if state in closed: # Sprecavanje ponovnog posjecivanja vec posjecenih stanja
            continue
        closed.add(state)

        if state in goals: # if goal(state(n)) then return n
            return True, len(closed), path, cost
        
        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]): # for m ∈ expand(n,succ) do
            if nxt not in closed:
                waiting.append((nxt, path + [nxt], cost + c)) # insertBack(m, open)

    return False, len(closed), [], 0.0 # return fail


def ucs(s0, goals, succ): # Pretrazivanje s jednolikom cijenom (UCS)
    cnt = 0
    heap = [(0.0, cnt, s0, [s0])] # open ← [ initial(s0) ]
    closed = set()

    while heap: # while open ̸= [ ] do
        cost, cnt, state, path = heapq.heappop(heap) # n ← removeHead(open)

        if state in closed: # Sprecavanje ponovnog posjecivanja vec posjecenih stanja
            continue
        closed.add(state)

        if state in goals: # if goal(state(n)) then return n
            return True, len(closed), path, cost
        
        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]): # for m ∈ expand(n,succ) do
            if nxt not in closed:
                cnt += 1
                heapq.heappush(heap, (cost + c, cnt, nxt, path + [nxt])) # insertBack(m, open)

    return False, len(closed), [], 0.0 # return fail


def astar(s0, goals, succ, h): # Algoritam A*
    cnt = 0
    heap = [(h[s0], s0, cnt, [s0], 0.0)]  # open ← [ initial(s0) ]
    closed = {}  # closed ← ∅

    while heap: # while open != [ ] do
        f_value, state, _, path, cost = heapq.heappop(heap)  # n ← removeHead(open)

        if state in goals: # if goal(state(n)) then return n
            return True, len(closed), path, cost

        closed[state] = cost # closed ← closed ∪ { n }

        for nxt, c in sorted(succ.get(state, []), key=lambda x: x[0]): # for m ∈ expand(n,succ) do
            if nxt in closed: # if ∃m0 ∈ closed ∪ open such that state(m0) = state(m) then
                if cost + c < closed[nxt]: # if g(m0) < g(m) then continue
                    del closed[nxt] # else remove(m0, closed ∪ open)
                else:
                    continue
            cnt += 1
            heapq.heappush(heap, (cost + c + h[nxt], nxt, cnt, path + [nxt], cost + c)) # insertSortedBy(f, m, open)

    return False, len(closed), [], 0.0 # return fail


def check_optimistic(goals, succ, h, h_path): # Provjera optimisticnosti heuristike
    print("# HEURISTIC-OPTIMISTIC {}".format(h_path))

    rev = {} # Izgradnja obrnutog grafa za racunanje h* vrijednosti
    for state, neighbors in succ.items():
        for nxt, c in neighbors:
            rev.setdefault(nxt, []).append((state, c))

    
    hstar_value = {}
    heap = []
    for g in goals:
        heapq.heappush(heap, (0.0, g))

    while heap: # Dijkstrin algoritam za racunanje h* vrijednosti
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

        # Provjeravamo optimisticnost heuristike, tj. vrijedi li h(n) <= h*(n)
        if hval <= hstar:
            print("[CONDITION]: [OK] h({}) <= h*: {:.1f} <= {:.1f}".format(state, hval, hstar))
        else:
            print("[CONDITION]: [ERR] h({}) <= h*: {:.1f} <= {:.1f}".format(state, hval, hstar))
            optimistic = False

    if optimistic:
        print("[CONCLUSION]: Heuristic is optimistic.")
    else:
        print("[CONCLUSION]: Heuristic is not optimistic.")


def check_consistent(succ, h, h_path): # Provjera konzistentnosti heuristike
    print("# HEURISTIC-CONSISTENT {}".format(h_path))
    consistent = True

    for state in sorted(succ.keys()):
        for nxt, c in sorted(succ[state], key=lambda x: x[0]):
            hs = h.get(state, 0.0)
            ht = h.get(nxt, 0.0)

            # Provjeravamo monotonost heuristike, tj. vrijedi li h(n) <= h(m) + c
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


def print_result(alg, found, visited, path, cost, h_path=None): # Ispis rezultata
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


if __name__ == '__main__': # Glavna funkcija
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
