#!/usr/bin/env python3
"""Weight-free passive-graph resistance bounds; no physical current allocation."""
import collections
from fractions import Fraction
import heapq
import math


def exact(value):
    return value if isinstance(value, Fraction) else Fraction(value)


def graph_bounds(nodes, edges):
    """Rayleigh spanning-tree diameter upper bound and bridge-cut lower bound.

    The computational root is not a model/current injection or equipotential
    footprint. All sums used for reported bounds are exact rational values of
    input resistances. Float Dijkstra only chooses a valid spanning tree.
    """
    nodes = set(nodes); assert nodes and edges
    grouped = collections.defaultdict(list)
    for a, b, resistance in edges:
        assert a in nodes and b in nodes and a != b
        r = exact(resistance); assert r > 0 and math.isfinite(float(r))
        grouped[tuple(sorted((a,b)))].append(r)
    adjacency = collections.defaultdict(list)
    for (a,b), values in sorted(grouped.items()):
        r = min(values)  # Select an actual edge; do not invent a parallel resistor.
        adjacency[a].append((b,r)); adjacency[b].append((a,r))
    root = min(nodes); distance={root:0.0}; parent={}; queue=[(0.0,root)]
    while queue:
        cost,a = heapq.heappop(queue)
        if cost != distance[a]:continue
        for b,r in adjacency[a]:
            candidate=cost+float(r)
            if b not in distance or candidate < distance[b]:
                distance[b]=candidate;parent[b]=(a,r);heapq.heappush(queue,(candidate,b))
    assert set(distance)==nodes, 'Disconnected graph cannot share one resistance bound'
    assert root not in parent and len(parent)==len(nodes)-1
    tree=collections.defaultdict(list)
    for b,(a,r) in parent.items():tree[a].append((b,r));tree[b].append((a,r))
    def farthest(start):
        distances={start:Fraction(0)}; stack=[start]
        while stack:
            a=stack.pop()
            for b,r in tree[a]:
                if b in distances:continue
                distances[b]=distances[a]+r;stack.append(b)
        assert set(distances)==nodes
        endpoint=max(distances,key=lambda n:(distances[n],n))
        return endpoint,distances[endpoint]
    end_a,_=farthest(root);end_b,diameter=farthest(end_a)
    # Iterative bridge enumeration on the simple adjacency. Parallel-edge
    # conductance is handled exactly only when reporting a bridge cut.
    discovery={root:0};low={root:0};ancestor={root:None};clock=1;bridges=[]
    stack=[(root,iter(adjacency[root]))]
    while stack:
        a,iterator=stack[-1]
        try:b,_=next(iterator)
        except StopIteration:
            stack.pop();p=ancestor[a]
            if p is not None:
                low[p]=min(low[p],low[a])
                if low[a]>discovery[p]:bridges.append((tuple(sorted((a,p))),discovery[a],clock-1))
            continue
        if b==ancestor[a]:continue
        if b not in discovery:
            discovery[b]=low[b]=clock;clock+=1;ancestor[b]=a;stack.append((b,iter(adjacency[b])))
        else:low[a]=min(low[a],discovery[b])
    bridge_values=[dict(nodes=pair,parallel_edges=len(grouped[pair]),descendant_discovery_interval=[first,last],
                        resistance=1/sum((1/r for r in grouped[pair]),Fraction(0))) for pair,first,last in bridges]
    lower=max((row['resistance'] for row in bridge_values),default=Fraction(0))
    assert lower <= diameter
    return dict(tree_diameter_upper_ohm=diameter,bridge_diameter_lower_ohm=lower,
                tree_endpoint_pair=(end_a,end_b),tree_edges=[(a,b,r) for b,(a,r) in parent.items()],
                bridges=bridge_values,nodes=len(nodes),native_edges=len(edges),computational_root=root,
                node_discovery=discovery)


def balanced_positive_budget(currents):
    """Synthetic proof helper: accepts the complete balanced injection vector."""
    values=[exact(i) for i in currents]
    assert sum(values,Fraction(0))==0, 'Must include all external and internal currents'
    return sum((i for i in values if i>0),Fraction(0))
