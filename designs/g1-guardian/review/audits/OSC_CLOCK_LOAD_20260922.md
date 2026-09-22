# Actual OSC clock receiver and routing load

The delivered CTRL netlist has one direct clock receiver: `sg13g2_buf_16 clkbuf_0_osc_clk`, input A connected to `osc_clk`, output X to `clknet_0_osc_clk`. Its output drives 16 `sg13g2_buf_8` inputs, named `clkbuf_4_0_0_osc_clk` through `clkbuf_4_15_0_osc_clk`. This is a concrete replacement for the arbitrary 50 fF load in a selected OSC fixture; no oscillator simulation is performed by this audit.

Sources:

- `blocks/g1_ctrl/flow/runs/run7/final/nl/g1_digital.nl.v`, root input instance at line 22775.
- `blocks/g1_ctrl/flow/runs/run7/final/spice/g1_digital.spice`, line 6194: root buffer terminal order X, A, VDD, VSS.
- `blocks/g1_ctrl/flow/runs/run7/final/spef/nom/g1_digital.nom.spef`, net-map 29 input and 2686 root output.
- Installed unchanged library `/foss/pdks/ihp-sg13g2/libs.ref/sg13g2_stdcell/spice/sg13g2_stdcell.spice`.

The retained digital nominal SPEF input net has 32.9182 fF wire capacitance and a five-resistor chain totaling 256.0579 Ω (20.1957, 88.3534, 40.4146, 67.0942, 40 Ω). Exact node topology and capacitance distribution are retained in `osc-clock-input-20260922-r2.spef-fragment`. The root output net has 124.751 fF wire capacitance; complete distributed topology and receiver list are in `osc-clock-root_output-20260922-r2.spef-fragment` and `osc-clock-load-20260922.json`. The SPEF explicitly says `PIN_CAP NONE`: actual transistor-level receiver capacitance should be included separately. The listed coupling entries in the input fragment are zero; do not infer clock-aggressor coupling was qualified.

The assembled OSC-to-CTRL DEF route is separately audited against delivered GDS in `osc-route-geometry-20260922-r1.json`: total centerline 659.72 µm, all sampled widths 0.2 µm, coverage passed. Layer lengths are M2 333.265, M3 1.745, M4 128.87, and M5 195.84 µm. Nominal technology-LEF estimates give 339.7558 Ω wire resistance plus six single-cut crossings at 20 Ω = 459.7558 Ω, and 60.3853 fF ground capacitance. These are **whole-tree geometric estimates**, including physical port stubs, not exact point-to-point extracted RC. The macro-internal SPEF is a distinct scope and may be combined with a declared assembly-route approximation; neither includes package effects. Native via definitions and source hashes are retained in the JSON.

The audit does not qualify current drive, edge timing, supply sensitivity, jitter, the full clock tree, or assembly coupling. A transistor-level fixture should include actual root buffer and its 16 immediate receiver inputs (or a justified output-load sensitivity), avoid adding pin capacitance twice, and distinguish extracted digital wiring from estimated assembly wiring.

Reproduce using the pinned EDA container and unused route output path:

```sh
G1_CPUS=1 flow/run.sh python3 designs/g1-guardian/review/audits/audit_external_routes.py designs/g1-guardian/review/audits/osc-route-geometry-new.json --nets i_core.osc_clk
```

`audit_clock_load.py` records canonical fragments/hashes and refuses to overwrite the aggregate JSON. Its initial run failed on an incorrect `.spi` library suffix; log and initial fragments remain. The corrected `.spice` lookup completed in `osc-clock-load-20260922-r2.log`, with fresh fragment filenames. No physical or reference artifact was changed.
