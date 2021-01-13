#!/usr/bin/env python3

from pprint import pprint
from itertools import count

matrix = [line.split() for line in '* 8 - 1|4 * 11 *|+ 4 - 18|22 - 9 *'.split('|')]
get = lambda c: matrix[int(c.imag)][int(c.real)]

nodes = [1+0j, 3+0j, 0+1j, 2+1j, 1+2j, 3+2j, 0+3j, 2+3j]
edges = {n: {(s1, s2, get(n+s1)+get(n+s1+s2), n+s1+s2)
             for s1 in [-1j, 1+0j, 1j, -1+0j] if 0 <= (n+s1).real < 4 and 0 <= (n+s1).imag < 4
             for s2 in [-1j, 1+0j, 1j, -1+0j] if 0 <= (n+s1+s2).real < 4 and 0 <= (n+s1+s2).imag < 4
             if n != 3+0j and n+s1+s2 != 0+3j}
         for n in nodes}

pprint(edges)

def IDDFS(root, score):
    for depth in count():
        print('depth', depth)
        result = DLS(root, score, [], depth)
        if result:
            return result

def DLS(node, score, route, depth):
    if depth == 0 and node == 3+0j and score == 30:
        return route
    if depth > 0:
        for (s1, s2, cost, child) in edges[node]:
            result = DLS(child, eval(str(score) + cost), route + [s1, s2], depth-1)
            if result:
                return result

compass = {0-1j: 'north', 1+0j: 'east', 0+1j: 'south', -1+0j: 'west'}

for step in IDDFS(0+3j, 22):
    print(compass[step])
