#!/usr/bin/env python3
"""Reconstruct the public normalized source and 2-4 ns waveform fact table."""

from pathlib import Path
import bisect
import hashlib
import math
import re
import struct


HERE = Path(__file__).resolve().parent
CONTROL = HERE.parent / "custom-cml-div4-stage2-waveform-replay-v1"
RAW = HERE / "runtime/raw_tb_p1_cml_div2_front_loaded_normalized_replay_tran_v1.raw"
FACTS = HERE / "analysis/NORMALIZED-WAVEFORM-FACTS.tsv"
UNLOADED = CONTROL / "source-deck/v2-filesource/replay_unloaded_tpn.data"
LOADED = CONTROL / "source-deck/v2-filesource/replay_loaded_tpn.data"
NORMALIZED = HERE / "source-deck/replay_loaded_normalized_tpn.data"
SOURCE_DECK = HERE / "source-deck/tb_p1_cml_div2_front_loaded_normalized_replay_tran_v1.cir"
RUNTIME_DECK = HERE / "runtime/tb_p1_cml_div2_front_loaded_normalized_replay_tran_v1.cir"
CONTROL_DECK = CONTROL / "source-deck/v2-filesource/tb_p1_cml_div2_front_loaded_replay_tran_v2.cir"
WINDOW = (2.0e-9, 4.0e-9)
NA = "NA"
HEADER = ("kind\tsignal\tordinal\tdirection\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross\t"
          "cm_in_at\tcm_out_at\tn_samples\tmin\tmax\tp2p")


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def read_tpn(path):
    text = path.read_text(encoding="utf-8").splitlines()
    fields = [line.split("\t") for line in text if line]
    assert all(len(row) == 3 for row in fields)
    return text, [(float(t), float(p), float(n)) for t, p, n in fields]


assert digest(UNLOADED) == "d4d7fa0a48d78d5ff8dfa05cdfb3caea6894e75446f1178018e29b8823848f83"
assert digest(LOADED) == "af179591af0e612b366152e4d0a9678e93db39e83dfd9fcd95db4bb2cd4f70e8"
assert digest(NORMALIZED) == "c162fdaf60d98895538720f58208483d1c09dba4fa85c9b782ca3d50f1c3136f"
u_text, unloaded = read_tpn(UNLOADED)
l_text, loaded = read_tpn(LOADED)
n_text, normalized = read_tpn(NORMALIZED)
assert len(unloaded) == len(loaded) == len(normalized) == 2284
assert all(a[0] < b[0] for rows in (unloaded, loaded, normalized)
           for a, b in zip(rows, rows[1:]))


def p2p(rows):
    values = [p - n for t, p, n in rows if WINDOW[0] <= t <= WINDOW[1]]
    return max(values) - min(values)


u_p2p = p2p(unloaded)
l_p2p = p2p(loaded)
scale = u_p2p / l_p2p
expected = []
for source_line, (t, p, n) in zip(l_text, loaded):
    cm = (p + n) / 2.0
    diff = scale * (p - n)
    expected.append("%.17g\t%.17g\t%.17g" % (t, cm + diff / 2.0, cm - diff / 2.0))
assert expected == n_text
assert [line.split("\t")[0] for line in l_text] == [line.split("\t")[0] for line in n_text]
assert u_p2p == 1.3101500928117433
assert l_p2p == 1.1537113306058147
assert scale == 1.1355961045505054
assert p2p(normalized) == 1.3101500928117433
assert max(abs((pn + nn) / 2.0 - (pl + nl) / 2.0)
           for (t, pl, nl), (_, pn, nn) in zip(loaded, normalized)
           if WINDOW[0] <= t <= WINDOW[1]) == 0.0

assert SOURCE_DECK.read_bytes() == RUNTIME_DECK.read_bytes()
assert digest(SOURCE_DECK) == "a9642791e2513bac7d34733812ca70e3c5f81e7bce603f3a826432523f96db5e"
assert digest(HERE / "source-deck/p1_cml_div2_front_integrated_sinks.spice") == \
       "689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7"
base_deck = CONTROL_DECK.read_text(encoding="utf-8").splitlines()
norm_deck = SOURCE_DECK.read_text(encoding="utf-8").splitlines()
assert len(base_deck) == len(norm_deck) == 42
assert [i + 1 for i, (left, right) in enumerate(zip(base_deck, norm_deck)) if left != right] == [1, 2, 23, 38]
private_roots = tuple("/" + stem + "/" for stem in ("foss", "volume", "home"))
assert all(not any(root in line for root in private_roots) for line in norm_deck)


def load_raw(path):
    data = path.read_bytes()
    marker = b"Binary:\n"
    offset = data.index(marker)
    header = data[:offset].decode("ascii", "replace")
    vectors = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    points = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    payload = data[offset + len(marker):]
    assert len(payload) == vectors * points * 8
    names = {}
    for line in header.splitlines():
        match = re.match(r"^\s*(\d+)\s+(\S+)\s+\S+\s*$", line)
        if match:
            names[match.group(2)] = int(match.group(1))

    def column(name):
        index = names[name]
        return [struct.unpack_from("<d", payload, (point * vectors + index) * 8)[0]
                for point in range(points)]

    return vectors, points, payload, column


assert digest(RAW) == "bc36f6cb1abb3646297b42483fdde1bdd9a1bd0d55877bd4622ac13b3a320b20"
vectors, points, payload, column = load_raw(RAW)
assert (vectors, points) == (429, 2011)
stored = struct.iter_unpack("<d", payload)
assert all(math.isfinite(item[0]) for item in stored)
times = column("time")
assert times[0] == 0.0 and times[-1] == 4.0e-9
assert all(left < right for left, right in zip(times, times[1:]))
vp2, vn2 = column("v(div2_p_1)"), column("v(div2_n_1)")
vp4, vn4 = column("v(div4_p)"), column("v(div4_n)")
vin = [p - n for p, n in zip(vp2, vn2)]
vout = [p - n for p, n in zip(vp4, vn4)]
cm_in = [(p + n) / 2.0 for p, n in zip(vp2, vn2)]
cm_out = [(p + n) / 2.0 for p, n in zip(vp4, vn4)]
lo = bisect.bisect_left(times, WINDOW[0])
hi = bisect.bisect_right(times, WINDOW[1]) - 1
n_samples = hi - lo + 1


def cross_row(label, ordinal, i, values):
    j = i + 1
    vi, vj = values[i], values[j]
    tc = times[i] + (times[j] - times[i]) * vi / (vi - vj)
    weight = (tc - times[i]) / (times[j] - times[i])
    cmi = cm_in[i] + (cm_in[j] - cm_in[i]) * weight
    cmo = cm_out[i] + (cm_out[j] - cm_out[i]) * weight
    direction = "POS" if vi < 0.0 else "NEG"
    return "\t".join(("CROSS", label, str(ordinal), direction, str(i), str(j),
                       repr(times[i]), repr(times[j]), repr(vi), repr(vj), repr(tc),
                       repr(cmi), repr(cmo), NA, NA, NA, NA))


rows = []
counts = {}
for label, values in (("IN", vin), ("OUT", vout)):
    ordinal = 0
    for i in range(lo, hi):
        if values[i] * values[i + 1] < 0.0:
            ordinal += 1
            rows.append(cross_row(label, ordinal, i, values))
    zeros = [i for i in range(lo, hi + 1) if values[i] == 0.0]
    assert not zeros
    counts[label] = ordinal
for label, values in (("IN", vin), ("OUT", vout), ("CM_IN", cm_in), ("CM_OUT", cm_out)):
    window = values[lo:hi + 1]
    minimum, maximum = min(window), max(window)
    rows.append("\t".join(("STAT", label, NA, NA, NA, NA, NA, NA, NA, NA, NA,
                            NA, NA, str(n_samples), repr(minimum), repr(maximum),
                            repr(maximum - minimum))))

facts = FACTS.read_text(encoding="utf-8").splitlines()
assert facts[0] == HEADER
assert facts[1:] == rows
assert len(rows) == 49 and counts == {"IN": 10, "OUT": 35}

control_facts = (CONTROL / "analysis/read-only-waveform-v1/"
                 "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1-FACTS.tsv")
control_counts = {}
for line in control_facts.read_text(encoding="utf-8").splitlines()[1:]:
    arm, signal, kind, *_ = line.split("\t")
    if kind == "CROSS":
        control_counts[(arm, signal)] = control_counts.get((arm, signal), 0) + 1
assert control_counts == {("UNLOADED", "IN"): 10, ("UNLOADED", "OUT"): 5,
                          ("LOADED", "IN"): 10, ("LOADED", "OUT"): 30}

print("PASS normalized source: 2284 rows, K=1.1355961045505054, common mode unchanged")
print("PASS portable deck: only lines 1, 2, 23, and 38 differ from the published loaded control")
print("PASS normalized raw: 429 vectors x 2011 points, finite monotonic 0..4 ns")
print("PASS normalized facts: 49 rows byte-exact, IN/OUT crossings 10/35")
print("PASS control comparison: unloaded/loaded/normalized OUT crossings 5/30/35")
