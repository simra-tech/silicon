"""Readable xschem sheets of the SENSE amplifier on the chip of record: comp45 + R100.

comp45 + R100 is revision B (../../schematic/gen_sense.py) with the main amplifier XOTA
replaced by g1_ota_main_candidate: input pair M1/M2 w=384u (ng=64), NMOS sources M3/M4
320u/4u (ng=40), PMOS sources and cascodes M14/M11/M15/M12 384u/4u (ng=48), zero resistor
RZ rppd 1u/100u (R100) and Miller cap CC 45u x 23u (comp45).  The buffers XBUF/XREF keep
g1_ota.  Source netlist: ../../reports/rz100-partial-field-evidence-20260923-r1/
sense-comp45-rz100-actual-source-20260923-r1/candidate.spice (decoded repo copy, sha256
aeee4d41; bulk source bb933fda differs only in the sch_path comment).

Run from this directory: python3 gen_comp45_r100.py ; netlist and check as recorded in
designs/g1-guardian/review/schematics-readability-20260925/README.md.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schematic"))
import gen_sense as g  # noqa: E402  (importing does not write the revision-B sheets)

REF = ("reports/rz100-partial-field-evidence-20260923-r1/sense-comp45-rz100-actual-source-20260923-r1/"
       "candidate.spice sha256 aeee4d41 (source bb933fda)")
MAIN = {"M1": ("384u", "2u", 64), "M2": ("384u", "2u", 64), "M3": ("320u", "4u", 40), "M4": ("320u", "4u", 40),
        "M14": ("384u", "4u", 48), "M11": ("384u", "4u", 48), "M15": ("384u", "4u", 48), "M12": ("384u", "4u", 48),
        "RZ": ("1u", "100u"), "CC": ("45u", "23u")}
VAR = ("comp45 + R100, the SENSE amplifier on the chip: layout g1_sense_physical.gds 450a4906, "
       "LVS reference native-reference CDL 696b43fd")
out = os.environ.get("SENSE_OUT_DIR", HERE)
g.ota_sheet("g1_ota", what="3.3 V folded-cascode OTA, buffer version (XBUF, XREF)",
            ref="the g1_ota subcircuit in " + REF, variant=VAR, out_dir=out)
g.ota_sheet("g1_ota_main_candidate", sizes=MAIN,
            what="3.3 V folded-cascode OTA, main amplifier XOTA (comp45 + R100)",
            ref="the g1_ota_main_candidate subcircuit in " + REF, variant=VAR, out_dir=out,
            text_extra="comp45 + R100: M1/M2 4x wider, NMOS/PMOS sources and PMOS cascodes 4x wider and L=4u, "
                       "RZ 1u/100u (R100), CC 45u x 23u (comp45). The notes below are the revision-B design values.\n")
g.sense_sheet("g1_ota_main_candidate", ref=REF, variant=VAR, out_dir=out)
print("wrote comp45_r100 sheets")
