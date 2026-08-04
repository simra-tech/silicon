#!/usr/bin/env python3
"""Fail-closed recount for the retained C57 DRC and C60 LVS package."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

EXPECTED = {
    "C57-SUBSTRATE-TIE-M1B-REPAIR.gds": "e8be3e0ee88df96c6e8a05d581a51ca150356de38b4ea037fb60b9f831c1921e",
    "C57-manifest.json": "6734cd34c0f7b2f97efef54a45d58de3ed73f6477139fa344eb79d5269811455",
    "drc/c57-drc.log": "a99d616bd8466fe54f87f3cbc478bab85b4116efc2798053fed6a79a5de94827",
    "drc/c57-drc.lyrdb": "48caf2e7df26fba73088d8ea51cc2e7fac8d1b0d5e64082cbcf36c64e19c7e20",
    "drc/c57-drc.stdout.log": "93fd127dd209f993f60920943fb8c21537d856394b2f7413968f9a8008f213ca",
    "lvs/C60-first-lvs-plan.md": "3b5130070c6a55c69143ac895b091d450b8632aceb8b824b4b4bac0cbb56e857",
    "lvs/C60-nine-port-lvs.spice": "1ddc583d59a60b7b4999d0d9ba4bd1cd80402df8173d7feb72e7815e431db9f7",
    "lvs/c60-extracted.cir": "0059e12cd2eac02a7b380b5d5b058fb8113236c095c932adca340e73c7c6db56",
    "lvs/c60-lvs.log": "97a18aa28d30426f0f51d0be3b0b59b409654ebc668821c2f8e86a55c502190c",
    "lvs/c60-lvs.lvsdb": "68d3ea517949f0b04cc5973642d6b0836dc43e0cf4018922fcdf7985e62d7d98",
    "lvs/c60-lvs.stdout.log": "c260dc1cf6f6349ad9b5c00ea4309b12591e20e465874782765c0a7b6ef85fa3",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> None:
    for relative, expected in EXPECTED.items():
        data = (ROOT / relative).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            fail(f"hash mismatch: {relative}: {actual}")

    drc_root = ET.parse(ROOT / "drc/c57-drc.lyrdb").getroot()
    items = drc_root.find("items")
    if items is None or list(items):
        fail("DRC report does not contain an empty <items> element")

    source_lines = (ROOT / "lvs/C60-nine-port-lvs.spice").read_text().splitlines()
    subckt = next((line for line in source_lines if line.upper().startswith(".SUBCKT ")), None)
    if subckt is None or len(subckt.split()) != 11:
        fail("C60 source does not have one top name plus exactly nine ports")
    devices = [line for line in source_lines if line and line[0].upper() in {"Q", "R"}]
    if len(devices) != 7 or any(line[0].upper() == "X" for line in devices):
        fail("C60 source is not exactly seven native Q/R devices")

    for relative in ("lvs/c60-lvs.log", "lvs/c60-lvs.stdout.log"):
        text = (ROOT / relative).read_text()
        if "flag_missing_ports enabled" not in text:
            fail(f"strict-port evidence absent from {relative}")
        if text.count("INFO : Congratulations! Netlists match.") != 1:
            fail(f"unique native match statement absent from {relative}")
        if "Netlists don't match" in text:
            fail(f"native mismatch statement present in {relative}")

    lvsdb = (ROOT / "lvs/c60-lvs.lvsdb").read_text()
    final = lvsdb[lvsdb.rfind("\nZ(\n") :]
    if not re.search(r"X\(C57_SUBSTRATE_TIE_M1B_REPAIR C57_SUBSTRATE_TIE_M1B_REPAIR 1", final):
        fail("top-level LVS pair is not a match")
    counts = {
        "nets": len(re.findall(r"^   N\([^\n]+ 1\)$", final, re.M)),
        "ports": len(re.findall(r"^   P\([^\n]+ 1\)$", final, re.M)),
        "devices": len(re.findall(r"^   D\([^\n]+ 1\)$", final, re.M)),
    }
    if counts != {"nets": 10, "ports": 9, "devices": 7}:
        fail(f"unexpected LVS pair counts: {counts}")

    print("PASS: hashes exact; DRC items=0; strict LVS pairs nets=10 ports=9 devices=7")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
