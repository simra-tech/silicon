#!/usr/bin/env python3
"""Compare two xschem SPICE netlists of one cell: text, flattened names, flattened connectivity.

usage: check_equivalence.py BEFORE.spice AFTER.spice TOP [--json OUT]

1. text: the netlists after removing the '** sch_path:' / '** sym_path:' comment lines
   (they carry the directory the netlister ran in) are compared byte for byte.
2. named / multiset: both netlists are flattened from TOP (subcircuit calls expanded, instance paths
   joined with '/', internal nets prefixed by the instance path, top-level ports kept).
   Every primitive device is compared by path, model, ordered terminal nets and sorted
   parameters ('named'); 'multiset' compares the same records without instance names
   (for sheets that draw parallel units as xschem instance arrays).
3. connectivity: the flattened circuits become bipartite graphs (device vertices labelled
   by model and parameters, net vertices labelled by top-level port name or 'internal',
   edges labelled by terminal position; the two rppd/rhigh ends are interchangeable).
   Graph isomorphism (networkx) decides equality independent of net and instance names.
   Skipped (recorded) above 4000 devices when the named comparison is already identical.
Result 'identical' needs named and connectivity to agree; 'equivalent (instance names differ)'
needs multiset and connectivity to agree.
"""
import hashlib
import json
import sys

SYMMETRIC = {"rppd", "rhigh", "rsil"}


def logical_lines(text):
    out = []
    for raw in text.splitlines():
        if raw.startswith("+") and out:
            out[-1] += " " + raw[1:].strip()
        else:
            out.append(raw)
    return out


def parse(path):
    cells, cur, order = {}, None, []
    for line in logical_lines(open(path).read()):
        t = line.split()
        if not t or t[0].startswith("*"):
            continue
        k = t[0].lower()
        if k == ".subckt":
            cur = {"pins": [p for p in t[2:] if "=" not in p], "inst": []}
            cells[t[1]] = cur
            order.append(t[1])
        elif k.startswith(".ends"):
            cur = None
        elif k.startswith("."):
            continue
        elif cur is not None:
            params = tuple(sorted(v for v in t[1:] if "=" in v))
            toks = [v for v in t[1:] if "=" not in v]
            cur["inst"].append((t[0], toks[:-1], toks[-1], params))
    return cells


def flatten(cells, top):
    devs = {}
    ports = cells[top]["pins"]

    def walk(cell, prefix, mapping):
        for name, nets, model, params in cells[cell]["inst"]:
            ns = [mapping[n] if n in mapping else prefix + n for n in nets]
            if model in cells:
                sub = cells[model]
                if len(sub["pins"]) != len(ns):
                    raise ValueError("pin count mismatch %s%s -> %s" % (prefix, name, model))
                walk(model, prefix + name + "/", dict(zip(sub["pins"], ns)))
            else:
                devs[prefix + name] = (model, tuple(ns), params)
    walk(top, "", {p: p for p in ports})
    return ports, devs


def graph(ports, devs):
    import networkx as nx
    g = nx.Graph()
    pset = set(ports)
    for name, (model, nets, params) in devs.items():
        g.add_node(("d", name), tag=("dev", model, params))
        for i, n in enumerate(nets):
            if ("n", n) not in g:
                g.add_node(("n", n), tag=("net", n if n in pset else "internal"))
            role = "R" if model in SYMMETRIC and i < 2 else i
            if g.has_edge(("d", name), ("n", n)):
                g.edges[("d", name), ("n", n)]["role"] = tuple(sorted(set(g.edges[("d", name), ("n", n)]["role"]) | {role}, key=str))
            else:
                g.add_edge(("d", name), ("n", n), role=(role,))
    return g


def normalized(path):
    keep = [l for l in open(path).read().splitlines(True)
            if not l.startswith("** sch_path:") and not l.startswith("** sym_path:")]
    return "".join(keep)


def compare(before, after, top):
    res = {"top": top,
           "before_sha256": hashlib.sha256(open(before, "rb").read()).hexdigest(),
           "after_sha256": hashlib.sha256(open(after, "rb").read()).hexdigest()}
    nb, na = normalized(before), normalized(after)
    res["before_normalized_sha256"] = hashlib.sha256(nb.encode()).hexdigest()
    res["after_normalized_sha256"] = hashlib.sha256(na.encode()).hexdigest()
    res["text_identical"] = nb == na
    pb, db = flatten(parse(before), top)
    pa, da = flatten(parse(after), top)
    res["ports_before"], res["ports_after"] = pb, pa
    res["devices"] = [len(db), len(da)]
    diffs = []
    if pb != pa:
        diffs.append("port list differs")
    for k in sorted(set(db) | set(da)):
        if db.get(k) != da.get(k):
            diffs.append("%s: %s -> %s" % (k, db.get(k), da.get(k)))
    import collections
    mb = collections.Counter(db.values())
    ma = collections.Counter(da.values())
    res["multiset_identical"] = mb == ma
    res["multiset_differences"] = ["%s x%d -> x%d" % (k, mb.get(k, 0), ma.get(k, 0)) for k in sorted(set(mb) | set(ma), key=str)
                                   if mb.get(k, 0) != ma.get(k, 0)][:50]
    res["named_identical"] = not diffs
    res["named_differences"] = diffs[:50]
    res["named_difference_count"] = len(diffs)
    if len(da) > 4000 and not diffs:
        res["connectivity"] = "not run (%d devices; named comparison identical)" % len(da)
        iso = True
    else:
        import networkx as nx
        from networkx.algorithms import isomorphism as iso_mod
        ga, gb = graph(pa, da), graph(pb, db)
        gm = iso_mod.GraphMatcher(gb, ga, node_match=lambda x, y: x["tag"] == y["tag"],
                                  edge_match=lambda x, y: x["role"] == y["role"])
        iso = gm.is_isomorphic()
        res["connectivity"] = "isomorphic" if iso else "NOT isomorphic"
        res["graph_vertices"] = [gb.number_of_nodes(), ga.number_of_nodes()]
        res["networkx"] = nx.__version__
    if not diffs and iso:
        res["result"] = "identical"
    elif iso and res["multiset_identical"]:
        res["result"] = "equivalent (instance names differ)"
    else:
        res["result"] = "DIFFERENT"
    return res


if __name__ == "__main__":
    r = compare(sys.argv[1], sys.argv[2], sys.argv[3])
    if "--json" in sys.argv:
        json.dump(r, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    print("%-16s %-9s text=%s named=%s multiset=%s conn=%s devices=%s" % (r["top"], r["result"], r["text_identical"],
          r["named_identical"], r["multiset_identical"], r["connectivity"], r["devices"]))
    sys.exit(0 if r["result"] != "DIFFERENT" else 1)
