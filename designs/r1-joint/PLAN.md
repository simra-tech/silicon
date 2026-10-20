# R1 plan — specification phase

Written 2026-10-20. The specification is the source of truth for what the chip does; each block's
README is the source of truth for what was run. A step with no evidence linked next to it did not
happen.

## 1. Phases

| Phase | Output | Gate |
| --- | --- | --- |
| P0 specification | top-level specification, pin map, parameter classification, block budgets (area, power, pins), verification gates | owner review |
| P1 architecture studies | encoder chain accuracy budget; BiSS-C/SSI protocol and register map; area and floorplan feasibility; safety architecture | numbers in the specification, each marked simulated / estimated / assumed |
| P2 block design | schematics and RTL, block simulations at corners, MC where mismatch matters | block freeze: DRC/LVS clean or cut |
| P3 integration | floorplan, assembly, chip-level DRC/LVS/PEX, STA, full-chip co-simulation | top freeze: zero-marker decks |
| P4 sign-off | release package, bond plan, status tables | GDS frozen; human signs |

## 2. Cut list

If area, pins or schedule do not close, blocks are removed in this order and the README says so:

1. ABZ incremental output (3 pins) — fold into SPI-only reporting.
2. Second encoder track (nonius absolute) — single-track incremental with index.
3. PWM/commutation generator — gate outputs become controller-driven pass-through with safety gating.
4. Second current channel — one channel, single-phase monitoring.
5. T2F temperature output pin — report over the bus only.

What is never cut: the sine/cosine ADC path, the position computation, one serial interface, the
safety channel with the latched fault output, the bandgap.

## 2a. Area and pin closure (from S3, 2026-10-20; all numbers estimated, nothing run)

Measured on the G1 chip of record: interior inside the IO rows 772 × 772 µm = 0.596 mm²; G1 placed
0.458 mm² of macros there (77 %). Derived conversion for the digital macro: about 11 µm² per gate
equivalent at G1's 81–86 % utilisation.

The R1 block list as first written needs about 1.03 mm² (two SAR ADCs 0.20, digital 0.27, G1-size
BGR 0.15, two G1-size sense amplifiers 0.18, comparators 0.10, AFE 0.08, rest 0.06). The pin list
counts 26. Decisions taken to close:

| # | Decision | Effect |
| --- | --- | --- |
| D1 | Single-track encoder input (on-axis heads, one cycle per revolution, or any single sin/cos track); nonius second track dropped (cut 2) | −4 pins, −0.02 mm² |
| D2 | No ABZ output (cut 1); position over BiSS-C/SSI/SPI only | −3 pins, −0.01 mm² |
| D3 | One SAR ADC with two track-and-holds for simultaneous sine/cosine sampling; the current channels are multiplexed into the same ADC between encoder conversions; the safety comparators stay analog and do not depend on the ADC | −0.10 mm²; defines the current-sense ADC path |
| D4 | PWM pattern generator reduced to a safety-gated pass-through with dead-time insertion for three external low-side FETs (cut 3 in part); the controller generates PWM | −0.02 mm² |
| D5 | Compact new bandgap and compact current-sense cells; the G1 BGR586 (mismatch-averaged, 0.15 mm²) and G1 sense cell (0.09 mm²) are too large for R1 | −0.24 mm² |
| D6 | Iterative CORDIC and a 32-register file; pipelined CORDIC rejected | digital ≈ 0.18 mm² |
| D7 | `MA` shares the pad with `SCLK` and `SLO` with `SDO`; `CS` low selects SPI; no SPI access during a BiSS/SSI frame | −2 pins |
| D8 | `TEMP_OUT` pin dropped (cut 5); temperature over the bus; the freed pad is `EN`/`STO_IN`, a hardware enable the first list lacked | safety input added |
| D9 | Baseline die 1.414 mm (G1 ring reused). If block freeze areas exceed 0.45 mm², the fallback is a 1.5 mm die (interior ≈ 0.86 mm², area ≈ 2.25 mm², above the 2 mm² budget: owner decision at the floorplan gate) | — |

Lean total after D1–D8: ≈ 0.45–0.50 mm², marginal on the baseline die.

**D10 (open, 2026-10-20).** T5 synthesis puts the digital macro at ≈ 0.34 mm² placed (30.4 kGE; `r1_pos` 36 %, registers 19 %, `r1_gate` 17 %, `r1_safe` 10 %, BiSS 10 %, SPI 5 %), against the 0.18 mm² estimate, which predates the on-chip PWM generator (open item 6). Choices: (a) trim the RTL (shared multiplier in `r1_pos`, fewer writable registers, narrower PWM counters) to ≈ 0.28 mm² and still take the 1.5 mm die (D9); (b) the 1.5 mm die with the RTL as is; (c) cut the PWM generator back to pass-through (cut 3) and the I²t model to the host. Decision after T1–T4 report their analog areas. Power ≈ 17–21 mW, about
4.5 mA on the single `VDDA` pad (G1 path 11–21 Ω, ≈ 95 mV drop): a second analog supply pad is not
available, so the analog current budget is a design constraint, not a result.

## 3. Studies started 2026-10-20

| Study | Question | Owner | Result |
| --- | --- | --- | --- |
| S1 encoder chain | input standard, ADC resolution and rate, CORDIC widths, calibration, accuracy budget | agent | done 2026-10-20: 40 mVpp–1.4 Vpp differential, CM 0.5–2.8 V, PGA ×1–×32; full accuracy to 100 kHz, count-safe to 250 kHz; 12-bit SAR ENOB ≥ 11.5, simultaneous sampling skew < 0.5 ns; register calibration (offset, gain, phase, H3) brings ≈ ±10° el to < ±0.2° el; iterative CORDIC + tracking loop at ≥ 25 MHz. `specification/studies/S1_ENCODER_CHAIN_20261020.md` |
| S2 bus | BiSS-C/SSI frame, CRC, timing, register map scope | agent | done 2026-10-20: D2 register channel is mandatory (IDs read through CDM/CDS); RS-422 transceiver on the board; SSI trivial on the same pins; AS5047P-compatible SPI read frame proposed; Manufacturer ID registration handled outside the repository. `specification/studies/S2_BUS_20261020.md` |
| S5 oscillator | 25–32 MHz clock options, jitter budget, BiSS timeout | agent | done 2026-10-20: option (a) re-tuned G1 RC at 30 MHz, 5-bit trim, MA-referenced trim count; jitter ≥ 8× inside budget for all options; IHP PLL lacks lock/corner data. `specification/studies/S5_OSCILLATOR_20261020.md` |
| S4 PDK data | MIM/MOS/resistor mismatch models, DRC MIM limits, IO Liberty data | agent | done 2026-10-20: MIM mismatch 1 %·µm (spec blank); MOS and resistor 1σ values listed; no ADC/comparator IP in the PDK; no IO toggle-frequency limit. `specification/studies/S4_PDK_DATA_20261020.md` |
| S3 area and pins | macro budgets from G1 data and literature, floorplan, pin map closure | agent | done 2026-10-20: plan as written ≈ 1.03 mm² of macros against ≈ 0.45 mm² usable on the 1.414 mm die; 26 pins listed against 24; lean variant ≈ 0.56–0.60 mm², marginal. See §2a and `specification/studies/S3_AREA_PINS_20261020.md` |

## 4. Design-trace record

Every run of this design is kept for later reuse (training and evaluation tasks derived from real
design sessions). Rules, binding for every agent on R1:

1. Simulation decks, logs, raw waveforms and reports go under the block's `sim/` or `reports/`
   directory, or under the bulk results root (`G1_RESULTS_ROOT`) with a symlink in the tree. Nothing
   that is evidence lives only under `/tmp`.
2. Each run directory carries a `README.md` or `run.json` with the command, tool versions, PDK
   commit, inputs, the question asked, the result and the disposition (passed / failed / not run).
3. Failed and abandoned runs are kept, not deleted; they are labelled as such. A failure trace is as
   useful as a pass.
4. Session and subagent transcripts are copied to durable storage by a scheduled job; agents do not
   need to do this, but must not place artefacts in locations the job does not cover.
5. Large files (GDS, VCD, waveform dumps above a few MB) go to the bulk root, never into git.

## 5. Progress log

| Date | What happened |
| --- | --- |
| 2026-10-20 | r1_afe (T3) schematic revision B simulated: two-stage PGA (rail-to-rail stage 1, level shift to 0.6 V), f3 ≥ 1.057 MHz at all corners and steps, MC pole matching ≤ 0.90 %, THD ≤ −65 dB, ×1 noise 0.35 LSB; ×32 noise at ss (35.3 µV vs 35) and the r1_adc-matched T/H residual (0.506 LSB) fail marginally; ≈ 0.084 mm², 1.5–1.8 mA (estimated/simulated). `blocks/r1_afe/README.md` |
| 2026-10-20 | `r1_osc` (T1) schematic revision r1 sized and simulated at schematic level (`blocks/r1_osc/README.md`): 5-bit trim monotonic, step ≤ 1.81 %, ss/1.08 V/125 °C reaches 32.61 MHz at code 0, loop delay ≤ 2.3 ns, 231 µA tt (all simulated). 30 MHz tt is at code 22, not mid code 16 (binary trim limit), so `OSC_TRIM` resets to 22. Jitter (white noise, code 22): 14.9 ps per period, 103 ps over 30 cycles. Layout and PEX not run. |
| 2026-10-20 | T6 `r1_padring` ring reference built from the G1 r4 ring cells for the 24-pin R1 map (1414 µm, empty core, core window 692.6 × 689.1 µm = 0.477 mm²). Run `ring-20261020-a`, GDS `3a477ab4…`. Main, maximal, precheck DRC and density (with fill) pass, 0 markers; antenna fails (12 markers on the 4 `IOPadIn` gates: empty core has no `vdd` gate load, control on G1 r4 without decaps reproduces it); projected LVS fails in the G1 form (substrate not tied to `VSS` without core p-taps) and passes in the ring-only form (261/261 devices); canonical LVS fails as on G1. Bond plan: 0 wire crossings, bond map verified. Bonding-service acceptance, PEX and the IHP intake pre-check: not run. `blocks/r1_padring/README.md`, `padframe/README.md` |
| 2026-10-20 | T5 `r1_ctrl` RTL draft 0.1 (pos, bus, gate logic, safe FSM, registers) and `R1_REGISTER_MAP.md` 0.1. Run `r1ctrl_20261020_r3`: V3 RTL vs float reference ≤ 0.021° el, after bench calibration 0.051° el (0.17° el with constant); 217 chip-level protocol/gate/safety checks passed at 21/30/42 MHz. Yosys cell area 0.221 mm² = 1.23 × the 0.18 mm² budget, macro estimate 0.34 mm² (1.88 ×): floorplan decision needed. LibreLane/STA not run. `blocks/r1_ctrl/README.md` |
| 2026-10-20 | S4 (PDK data) and S5 (oscillator) done; specification open items 1 and 2 closed; three technical open items remain (reference buffer vs pin, 5 V heads, current-sample timing). |
| 2026-10-20 | Top-level specification draft 0.1 written (`specification/R1_TOP_LEVEL_SPECIFICATION.md`): blocks, 24-pin map, parameter classification, verification gates V1–V8, six open items. |
| 2026-10-20 | S1 done: ADC and accuracy numbers into the specification; CORDIC clock ≥ 25 MHz means a new or multiplied oscillator (open). |
| 2026-10-20 | S2 done: BiSS-C D2 control channel kept (read-only IDs). |
| 2026-10-20 | S3 done: as-written plan does not fit; decisions D1–D9 taken (§2a). |
| 2026-10-20 | Design chosen; skeleton and plan written; studies S1–S3 started. Name set to R1 (first draft said G2). Design-trace record rules added; durable copy of transcripts scheduled. |
