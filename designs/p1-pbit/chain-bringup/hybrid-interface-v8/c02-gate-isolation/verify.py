#!/usr/bin/env python3
"""Fail-closed verifier for the published C02 gate-isolation evidence."""

import csv
import difflib
import hashlib
import math
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RAW = HERE / "raw_tb_p1_cml2lv_hybrid_tran_2p5g_v8.raw"
BASE_RAW = PARENT / "raw_tb_p1_cml2lv_hybrid_tran_2p5g_v8.raw"
DECK = HERE / "C02-V3-TRAN-2P5G.cir"
BASE_DECK = PARENT / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-TRAN-2P5G.cir"
INTERFACE = HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-V2.spice"
BASE_INTERFACE = PARENT / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE.spice"
LOG = HERE / "C02-V3-NGSPICE.log"
FACTS = HERE / "C02-FACTS.tsv"

EXPECTED = {
    RAW: "df0416abf199d942aa4dc7875c9605fce774dc698c124a3d7975693e0d1d4ff2",
    BASE_RAW: "dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c",
    DECK: "ae6516d5e60270604c20605fa1be2a3ffe632e49232f9b441d64073c44b223de",
    BASE_DECK: "37e05841b0f11a0eafa1a54144f3a4a0084c5c09f9f0f12b6fb66678f8794c7a",
    INTERFACE: "9e08d45cd8c7c827623c9de619da00bdd72b8b89edfe7832fc358481c8146756",
    BASE_INTERFACE: "68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2",
    LOG: "3d25df4a4fcfae4c4286139a4abaa37313ebcbd0b75b26b3b4d5498fe0dc0964",
}

EXTRA = {
    "i(e.xu1.egn_buf)",
    "i(e.xu1.egp_buf)",
    "v(xu1.gbuf_n)",
    "v(xu1.gbuf_p)",
}

EXPECTED_INTERFACE_DIFF = [
    "+EGP_BUF gbuf_p VSS GP VSS 1",
    "+EGN_BUF gbuf_n VSS GN VSS 1",
    "-XM1 CM_N GP E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
    "-XM2 CM_P GN E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
    "+XM1 CM_N gbuf_p E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
    "+XM2 CM_P gbuf_n E_CM VSS sg13_lv_nmos w=6.0u l=0.13u ng=1 m=1 mm_ok=1",
]

EXPECTED_DECK_DIFF = [
    "-.include NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE.spice",
    "+.include NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE-V2.spice",
]


def require(ok, message):
    if not ok:
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
    return [
        line
        for line in lines
        if line[:1] in "+-" and line[:3] not in ("+++", "---")
    ]


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
        raise ValueError("binary marker lacks line ending")
    body = data[pos:]
    require(len(names) == nvar, f"{path.name} has {nvar} variable records")
    require(len(body) == nvar * npts * 8, f"{path.name} payload length is exact")
    values = struct.unpack(f"<{nvar * npts}d", body)
    require(all(math.isfinite(value) for value in values), f"{path.name} values are finite")
    return names, nvar, npts, values


def column(names, nvar, values, name):
    index = names.index(name)
    return values[index::nvar]


def crossings(values, threshold=0.0):
    shifted = [value - threshold for value in values]
    return sum(
        1
        for left, right in zip(shifted, shifted[1:])
        if left == 0 or right == 0 or left * right < 0
    )


def format_value(value):
    if isinstance(value, int):
        return str(value)
    return format(value, ".17g")


def main():
    for path, expected in EXPECTED.items():
        require(sha(path) == expected, f"{path.name} hash matches bound evidence")

    require(source_diff(BASE_INTERFACE, INTERFACE) == EXPECTED_INTERFACE_DIFF,
            "C02 interface has exactly two VSS-referenced sources and two gate rewires")
    require(source_diff(BASE_DECK, DECK) == EXPECTED_DECK_DIFF,
            "portable C02 deck differs from portable V8 deck only at its interface include")

    base_names, bn, bp, base_values = parse_raw(BASE_RAW)
    names, cn, cp, values = parse_raw(RAW)
    require((bn, bp) == (78, 1065), "baseline raw shape is 78x1065")
    require((cn, cp) == (82, 1065), "C02 raw shape is 82x1065")
    require(set(names) - set(base_names) == EXTRA, "C02 has exactly four declared extra vectors")
    require(set(base_names) <= set(names), "C02 retains every baseline vector name")

    time = column(names, cn, values, "time")
    base_time = column(base_names, bn, base_values, "time")
    require(all(left < right for left, right in zip(time, time[1:])),
            "C02 time is strictly increasing")
    require(all(struct.pack("<d", left) == struct.pack("<d", right)
                for left, right in zip(time, base_time)),
            "C02 time is bit-identical to baseline")

    gp = column(names, cn, values, "v(xu1.gp)")
    gn = column(names, cn, values, "v(xu1.gn)")
    gbuf_p = column(names, cn, values, "v(xu1.gbuf_p)")
    gbuf_n = column(names, cn, values, "v(xu1.gbuf_n)")
    require(all(struct.pack("<d", left) == struct.pack("<d", right)
                for left, right in zip(gbuf_p, gp)), "gbuf_p is bit-identical to GP")
    require(all(struct.pack("<d", left) == struct.pack("<d", right)
                for left, right in zip(gbuf_n, gn)), "gbuf_n is bit-identical to GN")

    in_p = column(names, cn, values, "v(in_p)")
    in_n = column(names, cn, values, "v(in_n)")
    diff = [left - right for left, right in zip(in_p, in_n)]
    out_p = column(names, cn, values, "v(cmos_out_p)")
    out_n = column(names, cn, values, "v(cmos_out_n)")
    require(crossings(diff) == 10, "differential input has ten sign-changing crossings")
    require(crossings(out_p, 0.6) == 0, "CMOS output P has zero 0.6 V crossings")
    require(crossings(out_n, 0.6) == 0, "CMOS output N has zero 0.6 V crossings")

    measured = {
        "raw_variables": (cn, "count"),
        "raw_points": (cp, "count"),
        "time_start": (time[0], "s"),
        "time_stop": (time[-1], "s"),
        "input_diff_crossings": (crossings(diff), "count"),
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
    with FACTS.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    require(len(rows) == len(measured), "facts table has exact metric coverage")
    require([row["metric"] for row in rows] == list(measured), "facts metrics are ordered and unique")
    for row in rows:
        value, unit = measured[row["metric"]]
        require(row["value"] == format_value(value) and row["unit"] == unit,
                f"{row['metric']} matches native raw")

    log = LOG.read_text(errors="replace")
    require("No. of Data Rows : 1065" in log and "ngspice-46 done" in log,
            "native log records 1065 rows and ngspice completion")
    require(not any(token in log.lower() for token in
                    ("warning", "error", "fatal", "singular", "timestep too small", "nan")),
            "native log retains no warning or error token")

    forbidden = tuple(b"/" + stem for stem in (b"home/", b"volume/", b"foss/", b"tmp/"))
    text_members = [DECK, INTERFACE, LOG, FACTS, HERE / "README.md",
                    HERE / "parent_bindings.txt", HERE / "verify.py"]
    for path in text_members:
        data = path.read_bytes()
        require(not any(token in data for token in forbidden), f"{path.name} has no private absolute path")

    print("PASS C02 public evidence derivative verified; specification and signoff not claimed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AttributeError) as error:
        print("FAIL " + str(error), file=sys.stderr)
        sys.exit(1)
