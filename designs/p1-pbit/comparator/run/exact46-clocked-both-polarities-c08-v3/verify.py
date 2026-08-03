#!/usr/bin/env python3
"""Fail-closed verifier for the published C08 V3 native evidence."""

import csv
import difflib
import hashlib
import math
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
SCHEMATIC = HERE / "p1_comparator.sch"
SOURCE = HERE / "p1_comparator.spice"
FACTS = HERE / "C08-V3-FACTS.tsv"
BINDINGS = HERE / "parent_bindings.txt"

RUNS = {
    "PLUS": (
        HERE / "C08-V3-PLUS10MV.cir",
        HERE / "C08-V3-PLUS10MV.log",
        HERE / "C08-V3-PLUS10MV.raw",
    ),
    "MINUS": (
        HERE / "C08-V3-MINUS10MV.cir",
        HERE / "C08-V3-MINUS10MV.log",
        HERE / "C08-V3-MINUS10MV.raw",
    ),
}

EXPECTED_HASHES = {
    SCHEMATIC: "69da165fef2705b04dae8a7b5ad5c8d1cbc71046ec3c6d9aad4402efbd9e6abc",
    SOURCE: "d692c50ac62ab7ebfdd2c9bf79b40c64d7470cd49467a68b8fd2d925101287bc",
    RUNS["PLUS"][0]: "29990ec9c40e20f4b5ab9b78a718126dd5d3b9004975238ef9e91642ae3bda7a",
    RUNS["PLUS"][1]: "257a5a15f13fc3a0d43072b0dc79f09e75b5dabb2cbaeaf4760ec6758b98c90e",
    RUNS["PLUS"][2]: "dcd9d92748df6434c4b352efa3c6f437a01f013e69309b8fd84dfec87508307e",
    RUNS["MINUS"][0]: "6fe71951af6dc5c576724c6cdf2f7457a547c5641b3473273c6dc173db1bb063",
    RUNS["MINUS"][1]: "d2d9e5f929606b22296a317e4a576dba7405e42c35ceefa423c06f377d322962",
    RUNS["MINUS"][2]: "8b8698bc01a65959b7646e0f04e23958ae38a2c54b57da9aadbc87007815577f",
}

EXPECTED_BINDINGS = {
    "native_schematic_sha256": "69da165fef2705b04dae8a7b5ad5c8d1cbc71046ec3c6d9aad4402efbd9e6abc",
    "native_generated_source_sha256": "4a021355cb631f961235e190f103505c4a9aa8a41d4fee4bbdc9c6826deb1966",
    "portable_generated_source_sha256": "d692c50ac62ab7ebfdd2c9bf79b40c64d7470cd49467a68b8fd2d925101287bc",
    "native_plus_deck_sha256": "15803a0083da32f666b10b255f7fdbd061fdbab3af3ad2ac386eb47fd8f96ff2",
    "portable_plus_deck_sha256": "29990ec9c40e20f4b5ab9b78a718126dd5d3b9004975238ef9e91642ae3bda7a",
    "native_minus_deck_sha256": "cfc40e019da32caeb71cb36c19282a3681a5cb18abb5db06e8e8cdf9f1a01a88",
    "portable_minus_deck_sha256": "6fe71951af6dc5c576724c6cdf2f7457a547c5641b3473273c6dc173db1bb063",
    "plus_log_sha256": "257a5a15f13fc3a0d43072b0dc79f09e75b5dabb2cbaeaf4760ec6758b98c90e",
    "plus_raw_sha256": "dcd9d92748df6434c4b352efa3c6f437a01f013e69309b8fd84dfec87508307e",
    "minus_log_sha256": "d2d9e5f929606b22296a317e4a576dba7405e42c35ceefa423c06f377d322962",
    "minus_raw_sha256": "8b8698bc01a65959b7646e0f04e23958ae38a2c54b57da9aadbc87007815577f",
}

MANIFEST_MEMBERS = {
    "C08-V3-FACTS.tsv",
    "C08-V3-MINUS10MV.cir",
    "C08-V3-MINUS10MV.log",
    "C08-V3-MINUS10MV.raw",
    "C08-V3-PLUS10MV.cir",
    "C08-V3-PLUS10MV.log",
    "C08-V3-PLUS10MV.raw",
    "README.md",
    "p1_comparator.sch",
    "p1_comparator.spice",
    "parent_bindings.txt",
    "verify.py",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)
    print("PASS " + message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_diff(left, right):
    lines = difflib.unified_diff(
        left.read_text().splitlines(), right.read_text().splitlines(), lineterm=""
    )
    return [line for line in lines if line[:1] in "+-" and line[:3] not in ("+++", "---")]


def parse_raw(path):
    data = path.read_bytes()
    text = data.decode("latin-1")
    nvar = int(re.search(r"No\. Variables:\s*(\d+)", text).group(1))
    npts = int(re.search(r"No\. Points:\s*(\d+)", text).group(1))
    section = re.search(r"(?m)^Variables:\s*\n", text)
    require(section is not None, f"{path.name} has Variables section")
    marker = re.search(r"\n\s*Binary:", text[section.end():])
    require(marker is not None, f"{path.name} has binary payload marker")
    lines = text[section.end():section.end() + marker.start()].splitlines()
    names = [line.split()[1].lower() for line in lines if line.strip()]
    pos = section.end() + marker.start() + marker.group(0).index("Binary:") + len("Binary:")
    if data[pos:pos + 2] == b"\r\n":
        pos += 2
    elif data[pos:pos + 1] == b"\n":
        pos += 1
    else:
        raise ValueError(f"{path.name} binary marker lacks line ending")
    body = data[pos:]
    require(len(names) == nvar, f"{path.name} has {nvar} variable records")
    require(len(body) == nvar * npts * 8, f"{path.name} payload length is exact")
    values = struct.unpack(f"<{nvar * npts}d", body)
    require(all(math.isfinite(value) for value in values), f"{path.name} values are finite")
    return names, nvar, npts, values


def column(names, nvar, values, name):
    return values[names.index(name)::nvar]


def crossings(values, threshold):
    shifted = [value - threshold for value in values]
    return sum(1 for left, right in zip(shifted, shifted[1:])
               if left == 0 or right == 0 or left * right < 0)


def exact_sample(time, values, target):
    index = min(range(len(time)), key=lambda item: abs(time[item] - target))
    require(time[index] == target, f"raw contains exact {target:g} s sample")
    return values[index]


def format_value(value):
    return str(value) if isinstance(value, int) else format(value, ".17g")


def measurements(names, nvar, npts, values):
    time = column(names, nvar, values, "time")
    raw = column(names, nvar, values, "v(pbit_raw)")
    out = column(names, nvar, values, "v(pbit_out)")
    window = [index for index, point in enumerate(time) if 600e-12 <= point <= 1000e-12]
    raw_min = min(window, key=lambda index: raw[index])
    raw_max = max(window, key=lambda index: raw[index])
    out_min = min(window, key=lambda index: out[index])
    out_max = max(window, key=lambda index: out[index])
    return {
        "raw_variables": (nvar, "count"),
        "raw_points": (npts, "count"),
        "time_start": (time[0], "s"),
        "time_stop": (time[-1], "s"),
        "pbit_raw_at_900ps": (exact_sample(time, raw, 900e-12), "V"),
        "pbit_out_at_900ps": (exact_sample(time, out, 900e-12), "V"),
        "pbit_raw_at_1000ps": (exact_sample(time, raw, 1000e-12), "V"),
        "pbit_out_at_1000ps": (exact_sample(time, out, 1000e-12), "V"),
        "raw_window_min": (raw[raw_min], "V"),
        "raw_window_min_time": (time[raw_min], "s"),
        "raw_window_max": (raw[raw_max], "V"),
        "raw_window_max_time": (time[raw_max], "s"),
        "out_window_min": (out[out_min], "V"),
        "out_window_min_time": (time[out_min], "s"),
        "out_window_max": (out[out_max], "V"),
        "out_window_max_time": (time[out_max], "s"),
        "out_crossings_0p6": (crossings(out, 0.6), "count"),
    }


def parse_bindings():
    rows = {}
    for line in BINDINGS.read_text().splitlines():
        if line and not line.startswith("#"):
            key, value = line.split(maxsplit=1)
            if key.endswith("_sha256"):
                rows[key] = value
    return rows


def check_log(run, log, measured):
    text = log.read_text(errors="replace")
    lower = text.lower()
    require("No. of Data Rows : 677" in text and
            "Simulation executed from .control section" in text,
            f"{run} log records rows and control-section execution")
    require(lower.count("temperature limiting function received nan") == 1,
            f"{run} log preserves one aggregate HBT NaN warning")
    require(not any(token in lower for token in
                    ("error", "fatal", "singular matrix", "timestep too small", "convergence failure")),
            f"{run} log retains no error or convergence-failure token")
    mapping = {
        "raw_latch_end": "pbit_raw_at_900ps",
        "out_latch_end": "pbit_out_at_900ps",
        "raw_track_end": "pbit_raw_at_1000ps",
        "out_track_end": "pbit_out_at_1000ps",
        "out_max": "out_window_max",
        "out_min": "out_window_min",
        "raw_max": "raw_window_max",
        "raw_min": "raw_window_min",
    }
    time_mapping = {
        "out_max": "out_window_max_time",
        "out_min": "out_window_min_time",
        "raw_max": "raw_window_max_time",
        "raw_min": "raw_window_min_time",
    }
    for log_name, metric in mapping.items():
        rows = re.findall(rf"(?m)^{log_name}\s+=\s+([^\s]+)(?:\s+at=\s+([^\s]+))?", text)
        require(len(rows) == 2, f"{run} log prints {log_name} twice")
        require(math.isclose(float(rows[0][0]), measured[metric][0], rel_tol=5e-6, abs_tol=5e-12),
                f"{run} {log_name} matches native raw")
        if log_name in time_mapping:
            require(math.isclose(float(rows[0][1]), measured[time_mapping[log_name]][0],
                                 rel_tol=5e-6, abs_tol=5e-16),
                    f"{run} {log_name} time matches native raw")


def main():
    for path, expected in EXPECTED_HASHES.items():
        require(sha(path) == expected, f"{path.name} hash matches bound evidence")

    manifest = {}
    for line in (HERE / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        manifest[name] = digest
    require(set(manifest) == MANIFEST_MEMBERS, "manifest has exact package-member coverage")
    for name, digest in manifest.items():
        require(sha(HERE / name) == digest, f"manifest hash matches {name}")

    require(parse_bindings() == EXPECTED_BINDINGS, "native and portable parent bindings are exact")
    source_lines = SOURCE.read_text().splitlines()
    require(source_lines[0] == "** sch_path: p1_comparator.sch", "generated source has local schematic binding")
    require(source_lines[1].split() == [
        ".subckt", "p1_comparator", "PBIT_OUT", "PBIT_RAW", "CLK_OUT_DIV", "IN_P", "IN_N",
        "CLK_P", "CLK_N", "TRIM_P", "TRIM_N", "VCC_HBT", "VDD", "VSS",
    ], "generated source has exact ordered 12-port interface")
    require(sum(line.startswith("X") for line in source_lines) == 46,
            "generated source contains 46 X-instances")
    require("XRFB raw_inv cml_out_p sub! rppd w=1.0u l=18.05u m=1 b=0 mm_ok=1" in source_lines,
            "executed generated source binds XRFB length 18.05 um")
    schematic_text = SCHEMATIC.read_text()
    require("name=RFB" not in schematic_text and "name=XRFB" not in schematic_text,
            "adjacent retained schematic lacks XRFB and is not treated as source parent")

    plus, minus = RUNS["PLUS"][0], RUNS["MINUS"][0]
    require(source_diff(plus, minus) == [
        "-* C08-V3-PLUS10MV : EXACT46 p1_comparator, +10 mV differential input, 5.0 GS/s clock, SOURCE ONLY UNRUN",
        "+* C08-V3-MINUS10MV : EXACT46 p1_comparator, -10 mV differential input, 5.0 GS/s clock, SOURCE ONLY UNRUN",
        "-VAMP_P raw_amp_p 0 DC 1.445",
        "-VAMP_N raw_amp_n 0 DC 1.435",
        "+VAMP_P raw_amp_p 0 DC 1.435",
        "+VAMP_N raw_amp_n 0 DC 1.445",
        "-write C08-V3-PLUS10MV.raw all",
        "+write C08-V3-MINUS10MV.raw all",
    ], "plus/minus decks differ only by identity, input polarity, and raw basename")

    for run, (deck, _, _) in RUNS.items():
        text = deck.read_text()
        lines = text.splitlines()
        require(text.count(".lib $PDK_ROOT/") == 6 and text.count("pre_osdi $PDK_ROOT/") == 2,
                f"{run} deck has portable model and OSDI bindings")
        require(text.count(".include p1_comparator.spice") == 1,
                f"{run} deck includes the local retained simulation-copy source once")
        require("tran 2p 1.2n 0" in lines and
                f"write C08-V3-{run}10MV.raw all" in lines,
                f"{run} deck has exact transient and raw write")
        require(sum(line.startswith("meas tran ") for line in lines) == 8,
                f"{run} deck has exactly eight transient measures")
        load_lines = [line for line in lines if line[:1] in "RCL" and
                      any(node in line.split()[1:3] for node in ("PBIT_OUT", "PBIT_RAW", "CLK_OUT_DIV"))]
        require(not load_lines, f"{run} deck declares no output load")

    parsed = {}
    for run, (_, log, raw) in RUNS.items():
        names, nvar, npts, values = parse_raw(raw)
        require((nvar, npts) == (223, 677), f"{run} raw shape is 223x677")
        time = column(names, nvar, values, "time")
        require(time[0] == 0 and time[-1] == 1.2e-9,
                f"{run} raw spans 0 to 1.2 ns")
        require(all(left < right for left, right in zip(time, time[1:])),
                f"{run} time is strictly increasing")
        measured = measurements(names, nvar, npts, values)
        check_log(run, log, measured)
        parsed[run] = measured

    with FACTS.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected_rows = [(run, metric) for run in RUNS for metric in parsed[run]]
    require([(row["run"], row["metric"]) for row in rows] == expected_rows,
            "facts table has exact ordered metric coverage")
    for row in rows:
        value, unit = parsed[row["run"]][row["metric"]]
        require(row["value"] == format_value(value) and row["unit"] == unit,
                f"{row['run']} {row['metric']} matches native raw")

    require(parsed["PLUS"]["pbit_out_at_900ps"][0] < 0.01 and
            parsed["PLUS"]["pbit_out_at_1000ps"][0] < 0.01 and
            parsed["MINUS"]["pbit_out_at_900ps"][0] > 1.19 and
            parsed["MINUS"]["pbit_out_at_1000ps"][0] > 1.19,
            "both polarities retain opposite unloaded states at both sample instants")

    forbidden = tuple(b"/" + stem for stem in (b"home/", b"volume/", b"foss/", b"tmp/"))
    text_members = [path for run in RUNS.values() for path in run[:2]]
    text_members += [SCHEMATIC, SOURCE, FACTS, BINDINGS, HERE / "README.md", HERE / "verify.py"]
    for path in text_members:
        data = path.read_bytes()
        require(not any(token in data for token in forbidden), f"{path.name} has no private absolute path")

    print("PASS C08 V3 unloaded polarity evidence verified; loaded behavior and signoff not claimed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL " + str(exc), file=sys.stderr)
        raise SystemExit(1)
