#!/usr/bin/env python3
"""Reference check for r1_tapidx: the r1_safe formula in exact integer arithmetic
(blocks/r1_safe/README.md, "DAC per comparator"):
    nP = 4c + ceil(d/2),  nN = 4(63 - c) - floor(d/2),  d = k - 32,  both clipped to 0..252.
The log of tb_tapidx.v lists lane, type (0 OC / 1 NEG), c, k, nP, nN for all 4096 (c, k) pairs on each lane.
Usage: tapidx_ref.py check <rtl-log> <result.json>
SPDX-License-Identifier: Apache-2.0"""
import json
import math
import sys


def taps(c, k):
    d = k - 32
    p = 4 * c + math.ceil(d / 2)
    n = 4 * (63 - c) - math.floor(d / 2)
    return min(max(p, 0), 252), min(max(n, 0), 252)


def main():
    log, out = sys.argv[2], sys.argv[3]
    seen = {0: set(), 1: set()}
    bad = []
    clipped = {0: 0, 1: 0}
    n = 0
    for line in open(log):
        lane, typ, c, k, p, nn = (int(x) for x in line.split())
        n += 1
        exp = taps(c, k)
        d = k - 32
        if not (0 <= 4 * c + math.ceil(d / 2) <= 252 and 0 <= 4 * (63 - c) - math.floor(d / 2) <= 252):
            clipped[typ] += 1
        if (p, nn) != exp:
            bad.append(dict(lane=lane, type=typ, c=c, k=k, rtl=(p, nn), expected=exp))
        seen[typ].add((c, k))
    # independent identity: unclipped nP - nN = 4 (2c - 63) + (k - 32), the threshold of the contract
    ident_bad = 0
    for typ in (0, 1):
        for c in range(64):
            for k in range(64):
                d = k - 32
                p0 = 4 * c + math.ceil(d / 2)
                n0 = 4 * (63 - c) - math.floor(d / 2)
                if p0 - n0 != 4 * (2 * c - 63) + d:
                    ident_bad += 1
    res = dict(
        samples=n, oc_pairs=len(seen[0]), neg_pairs=len(seen[1]),
        mismatches=len(bad), first_mismatches=bad[:5],
        clipped_samples_oc=clipped[0], clipped_samples_neg=clipped[1], identity_failures=ident_bad,
        disposition=("passed" if (not bad and len(seen[0]) == 4096 and len(seen[1]) == 4096 and n == 4 * 4096 and ident_bad == 0)
                     else "FAILED"))
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res))
    sys.exit(0 if res["disposition"] == "passed" else 1)


if __name__ == "__main__":
    main()
