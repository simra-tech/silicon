# SPDX-License-Identifier: Apache-2.0
"""Derive the 'padbare' views of sg13g2_IOPadAnalog from the stock PDK files.

The stock sg13g2_IOPadAnalog exposes the bond pad as pin `pad` with two port
geometries: the 70 x 3 um stub at the die-side edge (y = 0..3, all metals)
and a 24.8 x 1 um strip at the core-side edge (Metal2/Metal3, y = 179..180).
Both are the same conductor, in front of the series protection resistor
(`padres` is behind it). To let the router use the core-side strip as a
resistor-free analog terminal, this script writes copies of the PDK LEF,
Verilog model and the three 1.2 V/3.3 V liberty files in which that strip is
a separate pin `padbare` (Metal3 only, as in the iic-jku ams-chip-template
whose approach this follows). The GDS is untouched: the layout cell stays the
stock PDK cell, and `pad`/`padbare` are one net in the layout.

Inputs are read from $PDK_ROOT/$PDK/libs.ref/sg13g2_io (Apache-2.0, IHP PDK
Authors); outputs go next to this script. Run inside the container:
    python3 ip/sg13g2_io_padbare/make_padbare_views.py
"""
import os
import pathlib
import re

PDK = pathlib.Path(os.environ.get("PDK_ROOT", "/foss/pdks")) / os.environ.get("PDK", "ihp-sg13g2") / "libs.ref/sg13g2_io"
OUT = pathlib.Path(__file__).resolve().parent
CELL = "sg13g2_IOPadAnalog"
CORE_PORT_M2 = "      LAYER Metal2 ;\n        RECT 26.105 179.000 50.875 180.000 ;\n"
CORE_PORT_M3 = "      LAYER Metal3 ;\n        RECT 26.105 179.710 50.875 180.000 ;\n"
HEADER = "# Derived from the IHP SG13G2 PDK (Apache-2.0) by make_padbare_views.py: sg13g2_IOPadAnalog core-side pad port renamed padbare.\n"


def lef():
    src = (PDK / "lef/sg13g2_io.lef").read_text()
    a = src.index(f"MACRO {CELL}\n"); b = src.index(f"END {CELL}\n", a)
    macro = src[a:b]
    core_port = "    PORT\n" + CORE_PORT_M2 + CORE_PORT_M3 + "    END\n"
    assert macro.count(core_port) == 1, "core-side pad port not found as expected"
    macro = macro.replace(core_port, "")
    padbare = ("  PIN padbare\n    DIRECTION INOUT ;\n    USE SIGNAL ;\n    PORT\n"
               + CORE_PORT_M3 + "    END\n  END padbare\n")
    macro = macro.replace("  PIN padres\n", padbare + "  PIN padres\n", 1)
    out = HEADER + src[:a] + macro + src[b:]
    (OUT / "lef/sg13g2_io.lef").write_text(out)
    print("lef ok")


def verilog():
    src = (PDK / "verilog/sg13g2_io.v").read_text()
    old_hdr = f"module {CELL} (pad, padres, vdd, vss, iovdd, iovss);"
    assert old_hdr in src
    src = src.replace(old_hdr, f"module {CELL} (pad, padres, padbare, vdd, vss, iovdd, iovss);")
    a = src.index(f"module {CELL}"); b = src.index("endmodule", a)
    body = src[a:b]
    m = re.search(r"\n(\s*)inout\s+padres\s*;", body)
    assert m, body[:400]
    ind = m.group(1)
    body2 = body.replace(m.group(0), m.group(0) + f"\n{ind}inout padbare;", 1)
    # same conductor as pad
    body2 = body2.rstrip() + f"\n{ind}assign pad = padbare;\n{ind}assign padbare = pad;\n\n"
    out = "// " + HEADER[2:] + src[:a] + body2 + src[b:]
    (OUT / "verilog/sg13g2_io.v").write_text(out)
    print("verilog ok")


def lib(name):
    src = (PDK / f"lib/{name}").read_text()
    a = src.index(f"cell ({CELL})"); b = src.index("\n  cell (", a + 1) if "\n  cell (" in src[a + 1:] else len(src)
    cell = src[a:b]
    m = re.search(r"\n(\s*)pin \(pad\) \{\n(.*?)\n\1\}\n", cell, re.S)
    assert m, "pin (pad) block not found"
    ind = m.group(1)
    attrs = {}
    for k in ("input_voltage", "related_ground_pin", "related_power_pin", "capacitance",
              "rise_capacitance", "fall_capacitance", "rise_capacitance_range", "fall_capacitance_range",
              "max_capacitance"):
        mm = re.search(rf"\n\s*{k}\s*(:\s*[^;]+;|\([^)]*\);)", m.group(2))
        if mm:
            attrs[k] = mm.group(1)
    block = f"\n{ind}pin (padbare) {{\n{ind}  direction : \"inout\";\n{ind}  is_pad : false;\n"
    for k, v in attrs.items():
        block += f"{ind}  {k} {v}\n" if v.startswith("(") else f"{ind}  {k} {v}\n"
    block += f"{ind}}}\n"
    cell2 = cell.replace(m.group(0), m.group(0) + block.lstrip("\n"), 1)
    out = "/* " + HEADER[2:].strip() + " */\n" + src[:a] + cell2 + src[b:]
    (OUT / "lib" / name).write_text(out)
    print("lib ok", name)


lef(); verilog()
for n in ("sg13g2_io_typ_1p2V_3p3V_25C.lib", "sg13g2_io_fast_1p32V_3p6V_m40C.lib", "sg13g2_io_slow_1p08V_3p0V_125C.lib"):
    lib(n)
