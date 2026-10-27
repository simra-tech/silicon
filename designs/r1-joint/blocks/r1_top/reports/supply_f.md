# r1_top try f: supply network check (track T8, 2026-10-27)

Run: `asm-20261027-f3` (f2 values differ only in the bgr VSS riser: 1.649 / 2.21 Ω). Script: `flow/supply_f.py`. Output: `<G1_RESULTS_ROOT>/r1_top/asm-20261027-f3/supply_f.json`.
Command (repository root): `python3 designs/r1-joint/blocks/r1_top/flow/supply_f.py <run dir>/supply_f.json`.

## Method and its limits

1. All numbers are **estimated** by square count. No extraction tool ran on the supply network.
2. Each resistance is (length / width) x sheet resistance of a drawn top-level shape of
   `layout/r1_top_assemble_f.py`. A via group is (via resistance / number of vias).
3. Sheet resistance, via resistance and EM limits: IHP SG13G2 process specification Rev 1.2
   (`SG13G2_os_process_spec.pdf` in the PDK doc, sections 2.12-2.15). The EM limits are from section 2.15, page 16
   (11 years at 105 °C, DC).
4. Values used:

| Layer | Sheet (mΩ/sq, min / typ / max) | EM limit (line) |
| --- | --- | --- |
| Metal3, Metal4, Metal5 | 73 / 88 / 103 | 2.0 mA/µm |
| TopMetal1 | 15 / 18 / 21 | 15 mA/µm |
| TopMetal2 | 7.5 / 11 / 14.5 | 16 mA/µm |

| Via | Resistance (Ω per via, min / typ / max) | EM limit |
| --- | --- | --- |
| Via3, Via4 | 5 / 9 / 20 | 0.4 mA |
| TopVia1 | 1 / 2.2 / 4 | 1.4 mA |
| TopVia2 | 0.5 / 1.1 / 2.2 | 10 mA |

5. Block currents are the worst cases in the block READMEs (simulated, or estimated where the README says so).
   `r1_ctrl` VDD 33.4 mA is the 0.6 sign-off power estimate (0.0401 W typ at 1.2 V). The `r1_adc` currents are
   pre-layout tt values of layout A. Layout A has no SAR logic, so the ADC VDD current is low.
6. The ring and the pads are not modelled, except the VDD ring from pad 1 to the north row.
7. Not included: dynamic drop, decoupling, package and bond wire.

## Resistance from the pad core pin to the macro pin (Ω, estimated)

| Supply | Macro | min | typ | max |
| --- | --- | --- | --- | --- |
| VDDA | `u_safe` | 1.791 | 2.164 | 2.549 |
| VDDA | `u_isense` | 13.182 | 15.896 | 18.621 |
| VDDA | `u_adc` | 3.576 | 4.316 | 5.068 |
| VDDA | `u_afe` (far pin x 520.8) | 12.060 | 14.543 | 17.038 |
| VDDA | `u_bgr` | 7.274 | 8.773 | 10.285 |
| VDDA | `u_bias` | 14.762 | 17.801 | 20.851 |
| VDDA | `u_t2f` | 7.839 | 9.455 | 11.083 |
| VDD | `u_ctrl` (7 TopMetal1 stripes, from the north row) | 0.023 | 0.038 | 0.063 |
| VDD | `u_isense` | 4.050 | 5.223 | 7.082 |
| VDD | `u_osc` | 4.337 | 5.295 | 6.292 |
| VDD | `u_adc` (from the Metal4 VDD trunk) | 1.372 | 1.654 | 1.936 |
| VSS | `u_ctrl` (7 TopMetal1 stripes) | 0.028 | 0.044 | 0.070 |
| VSS | `u_isense` (to the east outer column) | 0.264 | 0.353 | 0.520 |
| VSS | `u_bgr` (to the south outer row, 4 bars with 2 µm gaps) | 0.065 | 0.102 | 0.168 |
| VSS | `u_afe` | 1.826 | 2.229 | 2.672 |
| VSS | `u_adc` (from the Metal4 VSS trunk) | 1.737 | 2.094 | 2.451 |

VDD ring, pad 1 to the north row: 0.777 Ω (typ).

## Isense ground: shared resistance to the bandgap ground

Requirement (brief): shared resistance from the `r1_bgr` ground to the `r1_isense` vss pins ≤ 2.3 Ω.

| Corner | Shared R (Ω) | Result |
| --- | --- | --- |
| min sheet | 1.213 | passed |
| typ sheet | 1.657 | passed |
| max sheet | 2.218 | passed (margin 0.08 Ω) |

Path: isense vss Metal3-Metal5 stack, Metal5 plate (y 705-726), TopMetal1 plate to x 1338.7, TopVia1 into the east
outer VSS column, column and south outer row to the bgr VSS tap. Ground offset from the isense own current: 3.52 mV
(max sheet, estimated).

The `r1_ctrl` return current also uses the east column and the south row. Its share on the common segment gives an
estimated offset of about 8 mV between the isense and bgr grounds. This number is an estimate. It is not
simulated. It is open issue 4 of try f.

## Worst static IR drop (max sheet, estimated)

| Path | Drop (mV) |
| --- | --- |
| VDDA `u_afe` far pin | **35.75** (worst VDDA) |
| VDDA `u_bias` | 19.84 |
| VDDA `u_adc` | 13.78 |
| VDDA `u_isense` | 8.38 |
| VDD `u_ctrl` (ring from pad 1 + stripes) | **32.38** (worst VDD, 2.7 % of 1.2 V) |
| VDD `u_isense` | 8.06 |
| VSS isense - bgr ground offset (own current) | 3.52 |

The worst VDDA drop is 35.75 mV, 1.1 % of 3.3 V.

## EM against the PDK limits (section 2.15)

| Shape | Current (mA) | Limit (mA) | Result |
| --- | --- | --- | --- |
| VDDA trunk Metal4 8 µm (all VDDA) | 4.300 | 16.0 | passed |
| pad-7 riser Metal4 6 µm | 4.300 | 12.0 | passed |
| west VDDA riser Metal3 9.4 µm | 2.340 | 18.8 | passed |
| AFE VDDA rail Metal4 2.8 µm | 2.000 | 5.6 | passed |
| isense VDDA Metal4 2 µm | 0.450 | 4.0 | passed |
| isense VDD Metal4 2 µm | 1.138 | 4.0 | passed |
| ctrl VDD TopMetal1 stripe 2.2 µm (1/7 of 33.4 mA) | 4.771 | 33.0 | passed |
| ctrl VDD TopMetal1 stripe 2.2 µm (all 33.4 mA in one stripe, bound) | 33.400 | 33.0 | failed (bound case only) |
| ADC vdda riser Metal3 2 µm | 1.036 | 4.0 | passed |
| ADC vdda neck / pin Metal3 0.4 µm | 1.036 | 0.8 | **failed** |
| ADC vdd neck / pin Metal3 0.4 µm | 0.903 | 0.8 | **failed** |
| ADC vss neck / pin Metal3 0.4 µm | 1.939 | 0.8 | **failed** |
| AFE vss pin Metal3 0.4 µm (2 pins, half each) | 1.000 | 0.8 | **failed** |
| AFE vdd pin Metal3 0.4 µm (2 pins, half each) | 1.000 | 0.8 | **failed** |
| safe vdda pin Metal3 0.4 µm | 0.418 | 0.8 | passed |
| bias vdd neck Metal4 0.5 µm | 0.050 | 1.0 | passed |
| osc vdd Metal4 2 µm | 0.317 | 4.0 | passed |
| ctrl VDD TopVia2 per stripe | 4.771 | 70.0 | passed |
| isense VSS TopVia1 into the column | 1.588 | 537.6 | passed |
| AFE VSS stack TopVia1 | 2.000 | 89.6 | passed |
| ADC vdda Via3 at the trunk | 1.036 | 22.4 | passed |

Result: all top-level shapes pass. The five failures are the 0.4 µm supply pins of `r1_adc` layout A and
`r1_afe` E3. The top level cannot fix them, because the pin width is inside the macro. Requirement for ADC layout
B and AFE E4: supply pins ≥ 1 µm wide, or more pins (`reports/integration_checklist_f.md`).

The ctrl stripe "all current in one stripe" row is a bound, not the real distribution. The real case (7 stripes)
passes.
