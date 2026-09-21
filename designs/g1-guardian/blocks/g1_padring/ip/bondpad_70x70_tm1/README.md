# bondpad_70x70_tm1

70 × 70 µm square wire-bond pad for the G1 ring, generated from the PDK's own
`bondpad` PCell (KLayout `SG13_dev` library) by `gen_bondpad.py`. The stock
`sg13g2_io` cells carry no passivation opening (no `Passiv` 9/0 shapes in
`sg13g2_io.gds`); each pad cell exposes a 70 × 3 µm `pad` stub on Metal2 to
TopMetal2 at its outer edge, and the PDK's LibreLane configuration expects an
external cell named `bondpad_70x70` at offset (5.0, −70.0) from the IO cell,
which the PDK does not ship ("TODO bondpads need to be part of the PDK" in
`libs.tech/librelane/sg13g2_io/config.tcl`). This directory supplies it.

| Item | Value |
| --- | --- |
| Metal stack | TopMetal1 + TopVia2 + TopMetal2 (PCell `bottomMetal` = TM1); TopMetal1 is the PCell's 1073 µm² frame, TopMetal2 the full 4900 µm² plate |
| Passiv opening | 65.8 × 65.8 µm (2.1 µm enclosure), layer 9/0 |
| Recognition | `dfpad` 41/0 |
| Origin | lower-left at (0, 0); PCell output is re-centred by the script |
| Cross-check | with the PCell default stack (Metal3 up) the script output is polygon-identical (XOR = 0 on all 11 layers) to `ip/sg13g2_ip__bondpad_70x70` of iic-jku/ihp-sg13g2-ams-chip-template commit `6524ffdd`; the TM1 variant differs only by the missing Metal3–Metal5 plates and vias |

`lef/bondpad_70x70_tm1.lef` is hand-written: `CLASS COVER`, one `pad` pin
(`DIRECTION INOUT`) and obstructions on TopMetal1 and TopMetal2 (the layers
present in the GDS). Why TM1 only: see the block README, "Surprises" item 2.
Regenerate the GDS with `flow/run_ring.sh` (step 1) or directly:

```
G1_WORKDIR=designs/g1-guardian/blocks/g1_padring flow/run.sh bash -c \
  'KLAYOUT_PATH=$PDK_ROOT/$PDK/libs.tech/klayout klayout -zz -nc -n sg13g2 \
   -r ip/bondpad_70x70_tm1/gen_bondpad.py -rd output=ip/bondpad_70x70_tm1/gds/bondpad_70x70_tm1.gds'
```
