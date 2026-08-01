#!/usr/bin/env python3
"""Recompute the published stage-two crossing topology from raw files."""

from pathlib import Path
import bisect
import hashlib
import math
import re
import struct


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = "NGSPICE46-P1-CML-DIV2-CML-DIV4-READ-ONLY-STAGE2-REPLAY-CROSSING-TOPOLOGY-V1"
HEADER = ("arm\tkind\tordinal\tinterval_id\ti\tj\tt_i\tt_j\tv_i\tv_j\tt_cross\t"
          "in_from\tin_to\tnearest_in\tdelta_t\tcm_in_cross\tcm_out_cross\t"
          "n_samples\tn_out_cross\tcm_in_min\tcm_in_max\tcm_in_p2p\t"
          "cm_out_min\tcm_out_max\tcm_out_p2p")
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

    return column


def crossings(values, times, first, last):
    result = []
    for i in range(first, last):
        left, right = values[i], values[i + 1]
        if (left < 0.0 < right) or (left > 0.0 > right):
            time = times[i] + (times[i + 1] - times[i]) * left / (left - right)
            result.append((len(result) + 1, i, i + 1, times[i], times[i + 1],
                           left, right, time, "POS" if left < 0.0 else "NEG"))
    return result


facts = (HERE / f"{PREFIX}-TOPOLOGY.tsv").read_text(encoding="utf-8").splitlines()
assert facts and facts[0] == HEADER
expected = []
for arm, (raw_path, raw_sha) in RAWS.items():
    assert digest(raw_path) == raw_sha
    column = load_raw(raw_path)
    times = column("time")
    assert all(left < right for left, right in zip(times, times[1:]))
    p2, n2 = column("v(div2_p_1)"), column("v(div2_n_1)")
    p4, n4 = column("v(div4_p)"), column("v(div4_n)")
    input_diff = [p - n for p, n in zip(p2, n2)]
    output_diff = [p - n for p, n in zip(p4, n4)]
    input_cm = [(p + n) / 2.0 for p, n in zip(p2, n2)]
    output_cm = [(p + n) / 2.0 for p, n in zip(p4, n4)]
    assert all(math.isfinite(value) for values in (input_diff, output_diff, input_cm, output_cm)
               for value in values)
    first = bisect.bisect_left(times, 2.0e-9)
    last = bisect.bisect_right(times, 4.0e-9) - 1
    input_crossings = crossings(input_diff, times, first, last)
    output_crossings = crossings(output_diff, times, first, last)
    input_times = [item[7] for item in input_crossings]
    brackets = [item[1] for item in input_crossings]
    fragments = [(0, first, brackets[0], "NA", "1")]
    fragments.extend((ordinal, brackets[ordinal - 1] + 1, brackets[ordinal],
                      str(ordinal), str(ordinal + 1))
                     for ordinal in range(1, len(input_crossings)))
    fragments.append((len(input_crossings), brackets[-1] + 1, last,
                      str(len(input_crossings)), "NA"))
    mapped = []
    for crossing in output_crossings:
        crossing_time = crossing[7]
        interval = bisect.bisect_right(input_times, crossing_time)
        nearest_index = min(range(len(input_times)),
                            key=lambda index: (abs(crossing_time - input_times[index]), index))
        i, j = crossing[1], crossing[2]
        weight = (crossing_time - times[i]) / (times[j] - times[i])
        cm_in = input_cm[i] + (input_cm[j] - input_cm[i]) * weight
        cm_out = output_cm[i] + (output_cm[j] - output_cm[i]) * weight
        mapped.append((crossing, interval, nearest_index + 1,
                       crossing_time - input_times[nearest_index], cm_in, cm_out))
    counts = {fragment[0]: sum(item[1] == fragment[0] for item in mapped)
              for fragment in fragments}
    for interval, start, stop, input_from, input_to in fragments:
        cm_in_values = input_cm[start:stop + 1]
        cm_out_values = output_cm[start:stop + 1]
        row = (arm, "INTERVAL", interval, interval, start, stop, repr(times[start]),
               repr(times[stop]), "NA", "NA", "NA", input_from, input_to, "NA", "NA",
               "NA", "NA", stop - start + 1, counts[interval], repr(min(cm_in_values)),
               repr(max(cm_in_values)), repr(max(cm_in_values) - min(cm_in_values)),
               repr(min(cm_out_values)), repr(max(cm_out_values)),
               repr(max(cm_out_values) - min(cm_out_values)))
        expected.append("\t".join(map(str, row)))
    for crossing, interval, nearest, delta, cm_in, cm_out in mapped:
        row = (arm, "CROSS", crossing[0], interval, crossing[1], crossing[2],
               repr(crossing[3]), repr(crossing[4]), repr(crossing[5]), repr(crossing[6]),
               repr(crossing[7]), "NA", "NA", nearest, repr(delta), repr(cm_in), repr(cm_out),
               "NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA")
        expected.append("\t".join(map(str, row)))

assert facts[1:] == expected
assert len(expected) == 57
assert sum("\tINTERVAL\t" in row for row in expected) == 22
assert sum("\tCROSS\t" in row for row in expected) == 35
print("PASS public topology recount: 57 rows byte-exact")
