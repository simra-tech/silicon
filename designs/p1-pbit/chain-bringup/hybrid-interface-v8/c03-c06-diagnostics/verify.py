#!/usr/bin/env python3
"""Fail-closed verifier for the published C03-C06 native evidence."""

import csv
import difflib
import hashlib
import math
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "c02-gate-isolation"
FACTS = HERE / "C03-C06-FACTS.tsv"
V2 = HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-V2.spice"
W24 = HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-C06-W24.spice"
C02_DECK = PARENT / "C02-V3-TRAN-2P5G.cir"
C02_RAW = PARENT / "raw_tb_p1_cml2lv_hybrid_tran_2p5g_v8.raw"

RUNS = {
    "C03": (HERE / "C03-TRAN-250M.cir", HERE / "C03-NGSPICE.log", HERE / "raw_c03_250m.raw", 82, 10065),
    "C04": (HERE / "C04-TRAN-250M-100N.cir", HERE / "C04-NGSPICE.log", HERE / "raw_c04_250m_100n.raw", 82, 50305),
    "C05": (HERE / "C05-TRAN-2P5G-VCMHI.cir", HERE / "C05-NGSPICE.log", HERE / "raw_c05_2p5g_vcmhi.raw", 82, 1065),
    "C06": (HERE / "C06-TRAN-2P5G-W24.cir", HERE / "C06-NGSPICE.log", HERE / "raw_c06_2p5g_w24.raw", 82, 1065),
}

EXPECTED = {
    V2: "9e08d45cd8c7c827623c9de619da00bdd72b8b89edfe7832fc358481c8146756",
    W24: "669f49e9ad838516589399a499530845a9bd08ebc97cb1bd509cd0764872d7f4",
    C02_DECK: "ae6516d5e60270604c20605fa1be2a3ffe632e49232f9b441d64073c44b223de",
    C02_RAW: "df0416abf199d942aa4dc7875c9605fce774dc698c124a3d7975693e0d1d4ff2",
    RUNS["C03"][0]: "092866aff2a2daeffa98c9fd43a40e0952de75a450fb9719771c482fff4d13d3",
    RUNS["C03"][1]: "5ff3182732b1af7148ce1393b2f9b2e82fae5d4ad72bb87339b92f603ac89057",
    RUNS["C03"][2]: "2909ca8d8b152b398fd8f0e738c3ef7b0ebb79a247fc8609135d6544567cfa00",
    RUNS["C04"][0]: "47625dee5ad51bf71f988b1441e22cee98483de5d1dab8706b09f5869a1b1f4e",
    RUNS["C04"][1]: "beff042c79ef5cf58c80970c4a5793516dade111e2238713b38075c16d6e49de",
    RUNS["C04"][2]: "f422fb186d83bdd3bc7cf796a4097b5d44ab160994209198b870188f6c7dee56",
    RUNS["C05"][0]: "1567b3018691e19dd958418dbeac7c0cc42095ce7c23425d7a98ebe9a4344fec",
    RUNS["C05"][1]: "96bdd81f5325cd4ac5b719c84a8ab9dcc0f0e2cbd17d6756416552ef2a409920",
    RUNS["C05"][2]: "00552d340050527d6bd98680f917f6c4583b5a74247c331f89fbf305ff8843d1",
    RUNS["C06"][0]: "54c383d1e10bc9faae18faec95c285001a4788e3ee2383b09d2cc9faaa780d66",
    RUNS["C06"][1]: "76b12eaa7664183ba8ab54fb15458688fd3bbe8ea4d976410e26a7ada8596b48",
    RUNS["C06"][2]: "c772ade2a995d2f7161a6c325bb789d75b1a3ff298559d766da8e488c667f551",
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


def crossings(values, threshold=0.0):
    shifted = [value - threshold for value in values]
    return sum(1 for left, right in zip(shifted, shifted[1:])
               if left == 0 or right == 0 or left * right < 0)


def format_value(value):
    return str(value) if isinstance(value, int) else format(value, ".17g")


def measurements(names, nvar, npts, values, cycle_metrics=False):
    time = column(names, nvar, values, "time")
    in_p = column(names, nvar, values, "v(in_p)")
    in_n = column(names, nvar, values, "v(in_n)")
    cm_p = column(names, nvar, values, "v(xu1.cm_p)")
    out_p = column(names, nvar, values, "v(cmos_out_p)")
    out_n = column(names, nvar, values, "v(cmos_out_n)")
    gp = column(names, nvar, values, "v(xu1.gp)")
    gn = column(names, nvar, values, "v(xu1.gn)")
    gbuf_p = column(names, nvar, values, "v(xu1.gbuf_p)")
    gbuf_n = column(names, nvar, values, "v(xu1.gbuf_n)")
    diff = [left - right for left, right in zip(in_p, in_n)]
    result = {
        "raw_variables": (nvar, "count"),
        "raw_points": (npts, "count"),
        "time_start": (time[0], "s"),
        "time_stop": (time[-1], "s"),
        "input_diff_crossings": (crossings(diff), "count"),
        "cm_p_min": (min(cm_p), "V"),
        "cm_p_max": (max(cm_p), "V"),
        "cm_p_p2p": (max(cm_p) - min(cm_p), "V"),
        "cmos_out_p_min": (min(out_p), "V"),
        "cmos_out_p_max": (max(out_p), "V"),
        "cmos_out_p_p2p": (max(out_p) - min(out_p), "V"),
        "cmos_out_p_crossings_0p6": (crossings(out_p, 0.6), "count"),
        "cmos_out_n_min": (min(out_n), "V"),
        "cmos_out_n_max": (max(out_n), "V"),
        "cmos_out_n_p2p": (max(out_n) - min(out_n), "V"),
        "cmos_out_n_crossings_0p6": (crossings(out_n, 0.6), "count"),
        "gbuf_p_minus_gp_max_abs": (max(abs(a - b) for a, b in zip(gbuf_p, gp)), "V"),
        "gbuf_n_minus_gn_max_abs": (max(abs(a - b) for a, b in zip(gbuf_n, gn)), "V"),
    }
    if cycle_metrics:
        period = 4e-9
        first = [value for t, value in zip(time, out_n) if t < period]
        last = [value for t, value in zip(time, out_n) if t >= time[-1] - period]
        result["first_cycle_out_n_p2p"] = (max(first) - min(first), "V")
        result["last_cycle_out_n_p2p"] = (max(last) - min(last), "V")
    return result


def main():
    for path, expected in EXPECTED.items():
        require(sha(path) == expected, f"{path.name} hash matches bound evidence")

    require(source_diff(V2, W24) == [
        "-XM1 CM_N gbuf_p E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
        "-XM2 CM_P gbuf_n E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
        "+XM1 CM_N gbuf_p E_CM VSS sg13_lv_nmos w=24.0u l=0.13u ng=1 m=1 mm_ok=1",
        "+XM2 CM_P gbuf_n E_CM VSS sg13_lv_nmos w=24.0u l=0.13u ng=1 m=1 mm_ok=1",
    ], "C06 interface changes only XM1/XM2 width from 6 um to 24 um")

    expected_deck_counts = {"C03": 15, "C04": 8, "C05": 7, "C06": 5}
    comparisons = {
        "C03": (C02_DECK, RUNS["C03"][0]),
        "C04": (RUNS["C03"][0], RUNS["C04"][0]),
        "C05": (C02_DECK, RUNS["C05"][0]),
        "C06": (C02_DECK, RUNS["C06"][0]),
    }
    for run, (left, right) in comparisons.items():
        diff = source_diff(left, right)
        require(len(diff) == expected_deck_counts[run], f"{run} deck has exact scoped diff record count")
    require("-.param vcm = 1.42" in source_diff(C02_DECK, RUNS["C05"][0]) and
            "+.param vcm = 1.549836259081225" in source_diff(C02_DECK, RUNS["C05"][0]),
            "C05 sole electrical deck change is declared common mode")
    require("-.param period = 400p" in source_diff(C02_DECK, RUNS["C03"][0]) and
            "+.param period = 4n" in source_diff(C02_DECK, RUNS["C03"][0]),
            "C03 cadence change is declared")
    require("-  tran 2p 20n" in source_diff(RUNS["C03"][0], RUNS["C04"][0]) and
            "+  tran 2p 100n" in source_diff(RUNS["C03"][0], RUNS["C04"][0]),
            "C04 sole analysis change is longer stop time")
    require("-.include NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-V2.spice" in source_diff(C02_DECK, RUNS["C06"][0]) and
            "+.include NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-C06-W24.spice" in source_diff(C02_DECK, RUNS["C06"][0]),
            "C06 deck binds only the declared width derivative")

    parsed = {}
    for run, (_, log_path, raw_path, expected_nvar, expected_npts) in RUNS.items():
        names, nvar, npts, values = parse_raw(raw_path)
        require((nvar, npts) == (expected_nvar, expected_npts), f"{run} raw shape is {expected_nvar}x{expected_npts}")
        time = column(names, nvar, values, "time")
        require(all(left < right for left, right in zip(time, time[1:])), f"{run} time is strictly increasing")
        for threshold in (0.56029, 0.59383, 0.6, 0.65602):
            require(crossings(column(names, nvar, values, "v(cmos_out_p)"), threshold) == 0 and
                    crossings(column(names, nvar, values, "v(cmos_out_n)"), threshold) == 0,
                    f"{run} outputs have zero crossings at {threshold:.5f} V")
        require(column(names, nvar, values, "v(xu1.gbuf_p)") == column(names, nvar, values, "v(xu1.gp)"),
                f"{run} gbuf_p is bit-identical to GP")
        require(column(names, nvar, values, "v(xu1.gbuf_n)") == column(names, nvar, values, "v(xu1.gn)"),
                f"{run} gbuf_n is bit-identical to GN")
        log = log_path.read_text(errors="replace")
        require(f"No. of Data Rows : {expected_npts}" in log and "ngspice-46 done" in log,
                f"{run} native log records rows and ngspice completion")
        require(not any(token in log.lower() for token in
                        ("warning", "error", "fatal", "singular", "timestep too small", "nan")),
                f"{run} native log retains no warning or error token")
        parsed[run] = (names, nvar, npts, values)

    c03 = parsed["C03"]
    c04 = parsed["C04"]
    require(c03[0] == c04[0] and c04[3][:len(c03[3])] == c03[3],
            "C04 first 10065 points and all 82 vectors are bit-identical to C03")
    c02_names, c02_nvar, _, c02_values = parse_raw(C02_RAW)
    c02_time = column(c02_names, c02_nvar, c02_values, "time")
    for run in ("C05", "C06"):
        names, nvar, _, values = parsed[run]
        require(column(names, nvar, values, "time") == c02_time,
                f"{run} time is bit-identical to C02")

    measured = {run: measurements(*parsed[run], cycle_metrics=run in ("C03", "C04")) for run in RUNS}
    with FACTS.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    expected_rows = [(run, metric) for run in RUNS for metric in measured[run]]
    require([(row["run"], row["metric"]) for row in rows] == expected_rows,
            "facts table has exact ordered metric coverage")
    for row in rows:
        value, unit = measured[row["run"]][row["metric"]]
        require(row["value"] == format_value(value) and row["unit"] == unit,
                f"{row['run']} {row['metric']} matches native raw")

    forbidden = tuple(b"/" + stem for stem in (b"home/", b"volume/", b"foss/", b"tmp/"))
    text_members = [path for run in RUNS.values() for path in run[:2]]
    text_members += [V2, W24, FACTS, HERE / "README.md", HERE / "parent_bindings.txt", HERE / "verify.py"]
    for path in text_members:
        data = path.read_bytes()
        require(not any(token in data for token in forbidden), f"{path.name} has no private absolute path")

    print("PASS C03-C06 native evidence verified; specification and signoff not claimed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AttributeError) as error:
        print("FAIL " + str(error), file=sys.stderr)
        sys.exit(1)
