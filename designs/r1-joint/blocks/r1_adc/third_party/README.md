# third_party

`IHP-AnalogAcademy/` is a local clone of https://github.com/IHP-GmbH/IHP-AnalogAcademy (Apache-2.0),
commit `133ecf657572e021b5921b5a1b7693abfb209623` (2026-06-15), cloned 2026-10-20 with `git clone --depth 1`.
The clone is gitignored (404 MB). Re-create it with:

```
git clone https://github.com/IHP-GmbH/IHP-AnalogAcademy third_party/IHP-AnalogAcademy
git -C third_party/IHP-AnalogAcademy checkout 133ecf657572e021b5921b5a1b7693abfb209623
```

Used as reference only (no file is copied into `schematic/`):

| Source in module_3_8_bit_SAR_ADC | Used for |
| --- | --- |
| `part_1_comparator`, `part_5_analog_layout/comparator/layout/lvs_netlist/DIFF_COMPARATOR.spice` | double-tail dynamic comparator with PMOS input pair (Lin et al., JSSC 2010 lineage); `r1_cmp` re-draws this topology with a Schinkel-style second stage |
| `part_2_digital_comps/bootstrap_switch` | bootstrapped NMOS switch topology; `r1_bootsw` is a re-drawn Abo-Gray switch |
| `part_2_digital_comps/algorithm/verilog/sar_logic.v` | B / BN flag scheme (one flag per side and decision); `r1_sar_logic` uses the same scheme in XSPICE `d_dff` cells |
| `part_3_array_components/C-DAC` | monotonic top-plate-sampled binary array; R1 extends it to a 12-bit split 6+6 bridge array |
