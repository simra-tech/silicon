#!/usr/bin/env python3
"""Recompute the published stage-two replay waveform facts from raw files."""

from pathlib import Path
import bisect
import hashlib
import math
import re
import struct


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-WAVEFORM-ANALYSIS-V1"
HEADER = "arm\tsignal\tkind\tordinal\tdirection\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross"
WINDOW = (2.0e-9, 4.0e-9)
RAWS = {
    "UNLOADED": (
        ROOT / "runtime/pair-v1/UNLOADED-RUN/raw_tb_p1_cml_div2_front_unloaded_replay_tran_v2.raw",
        "456aa04dafc1b8a3023552e31cc1ba1c16fd8c55e04b5171934a7f0670489881",
    ),
    "LOADED": (
        ROOT / "runtime/pair-v1/LOADED-RUN/raw_tb_p1_cml_div2_front_loaded_replay_tran_v2.raw",
        "2f2010d24096030bb0317bf1c774fa16bcb82a61c09eb6f3badca402da357c26",
    ),
}
SIGNALS = (("IN", "v(div2_p_1)", "v(div2_n_1)"), ("OUT", "v(div4_p)", "v(div4_n)"))


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def load_raw(path):
    data = path.read_bytes()
    marker = b"Binary:\n"
    offset = data.index(marker)
    header = data[:offset].decode("ascii", "replace")
    payload = data[offset + len(marker):]
    variables = int(re.search(r"No\. Variables:\s*(\d+)", header).group(1))
    points = int(re.search(r"No\. Points:\s*(\d+)", header).group(1))
    assert len(payload) == variables * points * 8
    names = {}
    for line in header.splitlines():
        match = re.match(r"^\s*(\d+)\s+(\S+)\s+\S+\s*$", line)
        if match:
            names[match.group(2)] = int(match.group(1))

    def column(name):
        index = names[name]
        return [struct.unpack_from("<d", payload, (point * variables + index) * 8)[0]
                for point in range(points)]

    return points, column


def crossing_row(arm, signal, ordinal, i, times, values):
    j = i + 1
    vi, vj = values[i], values[j]
    crossing = times[i] + (times[j] - times[i]) * vi / (vi - vj)
    direction = "POS" if vi < 0.0 else "NEG"
    return "\t".join((arm, signal, "CROSS", str(ordinal), direction, str(i), str(j),
                       repr(times[i]), repr(times[j]), repr(vi), repr(vj), repr(crossing)))


def zero_row(arm, signal, ordinal, i, times, values):
    return "\t".join((arm, signal, "ZERO", str(ordinal), "NA", str(i), "NA",
                       repr(times[i]), "NA", repr(values[i]), "NA", "NA"))


facts = (HERE / f"{PREFIX}-FACTS.tsv").read_text(encoding="utf-8").splitlines()
assert facts and facts[0] == HEADER
expected = []
summaries = []
for arm, (raw_path, raw_sha) in RAWS.items():
    assert digest(raw_path) == raw_sha
    points, column = load_raw(raw_path)
    times = column("time")
    assert len(times) == points
    assert all(math.isfinite(value) for value in times)
    assert all(left < right for left, right in zip(times, times[1:]))
    first = bisect.bisect_left(times, WINDOW[0])
    last = bisect.bisect_right(times, WINDOW[1]) - 1
    for signal, plus_name, minus_name in SIGNALS:
        values = [plus - minus for plus, minus in zip(column(plus_name), column(minus_name))]
        crossings = []
        zeros = []
        for i in range(first, last + 1):
            if values[i] == 0.0:
                zeros.append(zero_row(arm, signal, len(zeros) + 1, i, times, values))
            if i < last and ((values[i] < 0.0 < values[i + 1]) or
                             (values[i] > 0.0 > values[i + 1])):
                crossings.append(crossing_row(arm, signal, len(crossings) + 1, i, times, values))
        expected.extend(crossings)
        expected.extend(zeros)
        window_values = values[first:last + 1]
        summaries.append((arm, signal, len(window_values), len(crossings), len(zeros),
                          min(window_values), max(window_values), max(window_values) - min(window_values)))

assert facts[1:] == expected
assert len(expected) == 55
for summary in summaries:
    print("\t".join(map(str, summary)))
print("PASS public raw recount: 55 fact rows byte-exact")
