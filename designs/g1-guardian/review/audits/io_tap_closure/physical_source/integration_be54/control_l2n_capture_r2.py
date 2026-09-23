#!/usr/bin/env python3
"""Successor capture control retaining a real two-terminal synthetic device."""
import hashlib
from pathlib import Path

base=Path(__file__).resolve().with_name('control_l2n_capture.py')
code=base.read_text()
old="        'capture = lambda do |target_netlist|\\n'"
assert code.count(old)==1
new="""        'nl=netlist\\nklass=RBA::DeviceClassResistor.new\\nklass.name="CONTROL_R"\\nnl.add(klass)\\n'
        'c=nl.circuit_by_name("CAPTURE_CONTROL")\\ndev=c.create_device(klass,"R1")\\n'
        'dev.connect_terminal("A",c.net_by_name("A"))\\ndev.connect_terminal("B",c.net_by_name("B"))\\n'
        'dev.set_parameter("R",123.456789012345)\\n'
        'capture = lambda do |target_netlist|\\n'"""
code=code.replace(old,new)
needle="    reread=a.output/'roundtrip.l2n';"
assert code.count(needle)==1
code=code.replace(needle,"    devices=list(top.each_device());assert len(devices)==1\n"
    "    assert devices[0].parameter('R')==123.456789012345\n"+needle)
exec(compile(code,str(base),'exec'),globals())
