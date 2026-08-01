#!/usr/bin/env python3
"""Reproduce timestamp-grid alignment facts from published replay sources."""

from bisect import bisect_left
from hashlib import sha256
from math import sqrt
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTROL = HERE.parent / "custom-cml-div4-stage2-waveform-replay-v1"
UNLOADED = CONTROL / "source-deck/v2-filesource/replay_unloaded_tpn.data"
LOADED = CONTROL / "source-deck/v2-filesource/replay_loaded_tpn.data"
NORMALIZED = HERE / "source-deck/replay_loaded_normalized_tpn.data"
FACTS = HERE / "analysis/GRID-ALIGNMENT.tsv"
HEADER = ("pair\tdirection\trows_a\trows_b\tindex_exact\tindex_mismatch\t"
          "index_max_abs_dt_s\tindex_rms_dt_s\tnearest_max_abs_dt_s\t"
          "nearest_gt_1fs\tnearest_gt_10fs\tnearest_gt_100fs\tnearest_gt_1ps\t"
          "interpretation")
THRESHOLDS = (1e-15, 1e-14, 1e-13, 1e-12)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def timestamps(path):
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines()
            if line]
    assert rows and all(len(row) == 3 for row in rows)
    values = [float(row[0]) for row in rows]
    assert all(left < right for left, right in zip(values, values[1:]))
    return values


assert digest(UNLOADED) == "d4d7fa0a48d78d5ff8dfa05cdfb3caea6894e75446f1178018e29b8823848f83"
assert digest(LOADED) == "af179591af0e612b366152e4d0a9678e93db39e83dfd9fcd95db4bb2cd4f70e8"
assert digest(NORMALIZED) == "c162fdaf60d98895538720f58208483d1c09dba4fa85c9b782ca3d50f1c3136f"
unloaded = timestamps(UNLOADED)
loaded = timestamps(LOADED)
normalized = timestamps(NORMALIZED)
assert len(unloaded) == len(loaded) == len(normalized) == 2284


def nearest_distances(source, target):
    distances = []
    for value in source:
        index = bisect_left(target, value)
        candidates = []
        if index < len(target):
            candidates.append(abs(value - target[index]))
        if index:
            candidates.append(abs(value - target[index - 1]))
        assert candidates
        distances.append(min(candidates))
    return distances


def pair_rows(pair, name_a, values_a, name_b, values_b, interpretation):
    assert len(values_a) == len(values_b)
    index_delta = [abs(a - b) for a, b in zip(values_a, values_b)]
    exact = sum(a == b for a, b in zip(values_a, values_b))
    shared = (str(len(values_a)), str(len(values_b)), str(exact),
              str(len(values_a) - exact), repr(max(index_delta)),
              repr(sqrt(sum(value * value for value in index_delta) / len(index_delta))))
    rows = []
    for source_name, source, target_name, target in (
            (name_a, values_a, name_b, values_b),
            (name_b, values_b, name_a, values_a)):
        nearest = nearest_distances(source, target)
        counts = tuple(str(sum(value > threshold for value in nearest))
                       for threshold in THRESHOLDS)
        rows.append("\t".join((pair, source_name + "_to_" + target_name) + shared +
                              (repr(max(nearest)),) + counts + (interpretation,)))
    return rows


rows = []
rows.extend(pair_rows("loaded-normalized", "loaded", loaded, "normalized", normalized,
                      "same_native_grid"))
rows.extend(pair_rows("unloaded-loaded", "unloaded", unloaded, "loaded", loaded,
                      "interpolation_required_for_common_mode_substitution"))
rows.extend(pair_rows("unloaded-normalized", "unloaded", unloaded, "normalized", normalized,
                      "interpolation_required_for_common_mode_substitution"))

facts = FACTS.read_text(encoding="utf-8").splitlines()
assert facts[0] == HEADER
assert facts[1:] == rows
assert len(rows) == 6

print("PASS loaded-normalized: 2284/2284 index-exact, nearest thresholds all zero")
print("PASS unloaded comparisons: 409 exact, 1875 mismatched, index max 1.253053637602494e-13 s")
print("PASS bidirectional nearest counts: >1fs 982, >10fs 48, >100fs 46, >1ps 0")
print("PASS boundary: loaded-normalized permits indexwise comparison; unloaded requires interpolation")
