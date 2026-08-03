#!/usr/bin/env python3
"""Fail-closed verifier for the published C01 observability evidence."""

import csv
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
TABLE = HERE / "C01-CROSSING-TABLE.tsv"
DECK = HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-TRAN-2P5G-C01.cir"
BASE_DECK = PARENT / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-TRAN-2P5G.cir"

EXPECTED = {
    RAW: "5ebd09ff96dc6aabe3b20fda571f6bb0baa2db38573c712d7344a0575e9ce176",
    BASE_RAW: "dbab1bd80ddaed8c3bee8f0c5ca816ac192fb687a7c31e841c1de46a7f68906c",
    HERE / "C01-CROSSING-TABLE.tsv": "76212f8efa3c111cfd3400e9d60c03304cfc9aa6e2b597740538212d5dc05d2b",
    HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-SOURCE-DECK-V8-INTERFACE.spice": "68b1bc654f4449e63958f7dd0e82154aa54f8d3fd39725ec1dc74834876053b2",
    HERE / "NGSPICE46-P1-CML-DIV2-CML-DIV4-HYBRID-INTERFACE-TRANSIENT-C01-RUN.log": "683c9bc73ce5be5cfe022616e9422481cf4172f44e0f18c5308b2d3cbb589fc9",
    HERE / "C01-CORRECTION.md": "1fe1452e0a30a5bba2f3f1dddc72aa76062971c9d80a04b90f721b4927a606b2",
}

EXTRA = {
    "i(@n.xu1.xm1.nsg13_lv_nmos[ids])",
    "i(@n.xu1.xm2.nsg13_lv_nmos[ids])",
    "i(@n.xu1.xm3.nsg13_lv_pmos[ids])",
    "i(@n.xu1.xm4.nsg13_lv_pmos[ids])",
    "i(@n.xu1.xmtail.nsg13_lv_nmos[ids])",
    "i(@q.xu1.xqef_n.qnpn13g2[ib])",
    "i(@q.xu1.xqef_n.qnpn13g2[ic])",
    "i(@q.xu1.xqef_n.qnpn13g2[ie])",
    "i(@q.xu1.xqef_p.qnpn13g2[ib])",
    "i(@q.xu1.xqef_p.qnpn13g2[ic])",
    "i(@q.xu1.xqef_p.qnpn13g2[ie])",
}

SAVE_LINES = [
    "  save v(xu1.ef_p) v(xu1.ef_n) v(xu1.gp) v(xu1.gn) v(xu1.cm_p) v(xu1.cm_n) v(xu1.e_cm) v(cmos_out_n) v(cmos_out_p)",
    "  save i(v_vcc_hbt) i(v_vdd) i(v_vss)",
    "  save @q.xu1.xqef_p.qnpn13g2[ic] @q.xu1.xqef_p.qnpn13g2[ib] @q.xu1.xqef_p.qnpn13g2[ie]",
    "  save @q.xu1.xqef_n.qnpn13g2[ic] @q.xu1.xqef_n.qnpn13g2[ib] @q.xu1.xqef_n.qnpn13g2[ie]",
    "  save @n.xu1.xm1.nsg13_lv_nmos[ids] @n.xu1.xm2.nsg13_lv_nmos[ids] @n.xu1.xmtail.nsg13_lv_nmos[ids]",
    "  save @n.xu1.xm3.nsg13_lv_pmos[ids] @n.xu1.xm4.nsg13_lv_pmos[ids]",
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
    names = [line.split()[1] for line in lines if line.strip()]
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


def column(names, nvar, npts, values, name):
    index = names.index(name)
    return [values[row * nvar + index] for row in range(npts)]


def crossings(values, threshold=0.0):
    shifted = [value - threshold for value in values]
    return sum(1 for left, right in zip(shifted, shifted[1:]) if left == 0 or right == 0 or left * right < 0)


def main():
    for path, expected in EXPECTED.items():
        require(sha(path) == expected, f"{path.name} hash matches bound evidence")

    base_lines = BASE_DECK.read_text().splitlines()
    c01_lines = DECK.read_text().splitlines()
    require([line for line in c01_lines if line not in SAVE_LINES] == base_lines,
            "portable C01 deck differs from portable baseline by only six save lines")
    require([line for line in c01_lines if line in SAVE_LINES] == SAVE_LINES,
            "portable C01 deck contains each added save line exactly once and in order")

    base_names, bn, bp, base_values = parse_raw(BASE_RAW)
    names, cn, cp, values = parse_raw(RAW)
    require((bn, bp) == (78, 1065), "baseline raw shape is 78x1065")
    require((cn, cp) == (89, 1065), "C01 raw shape is 89x1065")
    require(set(names) - set(base_names) == EXTRA, "C01 has exactly the 11 declared extra current vectors")
    for name in base_names:
        bi, ci = base_names.index(name), names.index(name)
        for row in range(bp):
            left = struct.pack("<d", base_values[row * bn + bi])
            right = struct.pack("<d", values[row * cn + ci])
            if left != right:
                raise ValueError(f"baseline mismatch in {name} at row {row}")
    print("PASS all 78 baseline vectors are bit-identical")

    time = column(names, cn, cp, values, "time")
    require(all(left < right for left, right in zip(time, time[1:])), "C01 time is strictly increasing")
    diff = [p - n for p, n in zip(column(names, cn, cp, values, "v(cml_p)"),
                                  column(names, cn, cp, values, "v(cml_n)"))]
    require(crossings(diff) == 10, "differential input has ten sign-changing crossings")
    require(crossings(column(names, cn, cp, values, "v(cmos_out_n)"), 0.6) == 0,
            "CMOS output N has zero 0.6 V crossings")
    require(crossings(column(names, cn, cp, values, "v(cmos_out_p)"), 0.6) == 0,
            "CMOS output P has zero 0.6 V crossings")

    with TABLE.open(newline="") as handle:
        rows = list(csv.reader((line for line in handle if line.strip()), delimiter="\t"))
    header, data_rows = rows[0], rows[1:]
    require(len(data_rows) == 50, "crossing table has 50 data rows plus one header")
    require([int(row[0]) for row in data_rows] == [group for group in range(1, 11) for _ in range(5)],
            "crossing table has five ordered rows for each of ten crossings")
    require(header[2:] == [name for name in header[2:] if name in names], "all table vectors exist in raw")
    for row in data_rows:
        target_ps = row[1]
        indices = [i for i, value in enumerate(time) if f"{value * 1e12:.3f}" == target_ps]
        if len(indices) != 1:
            raise ValueError(f"table time {target_ps} ps does not map to one raw sample")
        index = indices[0]
        for field, name in zip(row[2:], header[2:]):
            actual = column(names, cn, cp, values, name)[index]
            if field != f"{actual:.6g}":
                raise ValueError(f"table row {row[0]} at {target_ps} ps mismatches raw {name}")
    print("PASS all 1,250 crossing-table values match native raw formatting")

    correction = (HERE / "C01-CORRECTION.md").read_text()
    require("AMBIGUOUS" in correction and "not an exact\n   8-file closure" in correction,
            "correction retains ambiguous-cause and root-closure boundaries")
    print("PASS C01 public evidence derivative verified; signoff not claimed")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AttributeError) as error:
        print("FAIL " + str(error), file=sys.stderr)
        sys.exit(1)
