# Full-chip PEX: feasibility before 2026-09-29 (time-boxed, 2026-09-25)

**Answer: no.** The full-chip capacitance extraction did not finish within
its wall bound. Its own progress shows that the kpex 2.5D engine needs about
5.5 days for the fill-free chip and about 13 days with fill. Even with an
extracted netlist, one 28 µs chip transient is estimated at 17 hours to 6
days. The affordable alternative is below: block PEX, plus the new top-level
interconnect lumps
([README_top_interconnect_20260925.md](README_top_interconnect_20260925.md)),
plus the RTL co-simulation.

Every runtime below is either **measured** (named log) or **extrapolated**
(the method is stated). Nothing in this note is a simulation result.

## Built against

PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`. Container `tapeoutbench-eda:latest`
`sha256:ddeb6957…`. KLayout 0.30.9, kpex 0.3.12, ngspice 46 (`--version` in the
container). Input `blocks/g1_padring/layout/g1_chip_top_1414.gds` `629d303a…`.
CPUs 28-33 for the extraction and 34 for the progress probe (`taskset`,
`flow/launch_pinned.sh`).

Revision r2 (`g1_chip_top_1414_r2.gds` `9049e87b…`, now the file of record)
changes only metadata: two text labels and three cell names. Its sign-off
report states that the geometry is identical on every layer
(`../../../g1_padring/reports/signoff-1414r2-20260925/README.md`). The
numbers here therefore apply to r2 as well. r2 was **not re-extracted**.

## 1. Fill removal and size (measured)

`flow/pex/strip_fill.py` deleted every datatype-22 shape (`<layer>.filler` in the
PDK `sg13g2.lyp`) from every cell of a copy. Nothing else changed: nofill (23)
markers, drawn layers and cells are kept. Output `g1_chip_top_1414_nofill.gds`
`6406ba36…` (bulk); report [fullchip_strip_fill_20260925.json](fullchip_strip_fill_20260925.json).
Most fill sits in the top cell (273 422 shapes). The rest is in DOSE, DUT and the
`*_FILL_CELL$n` cells instanced in OSC, TRIP, T2F, GATE and digital.

| Flat count | with fill | fill-free | fill share |
|---|---|---|---|
| All shapes | 4 895 906 | 4 615 978 | 279 928 removed |
| Conductor shapes (Activ, GatPoly, Metal1-5, TopMetal1-2) | 648 525 | 368 597 | 43 % of conductor shapes |
| of which Metal4 / Metal5 / TopMetal1 / TopMetal2 | 94 022 | 15 923 | fill is 83 % of the upper-metal shapes |
| Contacts / vias (Cont … TopVia2) | — | 3 620 229 Cont, 425 019 vias | unchanged |
| kpex conductor polygons after merge (GatPoly … TopMetal2) | ≈ 718 988 (estimate: fill-free + 251 334 fill shapes on kpex layers) | **467 654** (measured, probe log) | — |
| Extracted devices (kpex LVS deck, flat, uncombined) | same | **94 357**: 43 905 LV NMOS, 43 884 LV PMOS, 2 152 HV NMOS, 1 622 HV PMOS, 1 678 rppd, 15 rhigh, 308 npn13G2, 19 cap_cmim, 635 ptap1, 139 antenna diodes | — |
| Extracted nets | — | 31 929 | — |

The device count is higher than the 61 684 devices of the sign-off LVS. That
LVS combines fingers and parallel devices; the kpex deck here runs with
`combine=false`.

## 2. kpex CC on the fill-free chip, 6 threads, CPUs 28-33

| Step | Result | Evidence (bulk `${BULK}/fullchip-pex-20260925/kpex_nofill/`) |
|---|---|---|
| kpex internal LVS (deck `klayout_pex/.../sg13g2.lvs`, deep) | ran in 215 s wall. "Netlists don't match" against the projected CDL; kpex extracts from the layout netlist anyway | `run.log` |
| 2.5D engine, attempt 1 (`kpex --gds`) | **failed** after 4 min 37 s: `Layout.top_cell` "multiple top cells". The LVSDB holds an unplaced device-abstract cell `D$sg13_hv_pmos$33` (4 shapes) | `run.log`, `run.log.rc` |
| attempt 2 (LVSDB with that cell deleted) | **failed**, same error (the abstract cell presumably comes back from the netlist when kpex rebuilds the layout; not examined) | `run2.log` |
| attempt 3 (`flow/pex/kpex_named_top.py`: unchanged kpex, top cell looked up by name for the substrate halo box) | **not run to completion**. The engine started 14:29:45. The wall bound was 6 400 s from launch; outcome in §2a | `run3.log` (no `.rc` written) |
| threads | `--threads 6` has no effect on the 2.5D engine. The process ran at 95-98 % of one CPU, 3.9 GB RSS | `ps` samples |
| output size, capacitor count | **none produced** | — |

### 2a. Outcome of attempt 3

**Not run to completion.** The 2.5D engine ran from 14:29:45 on one CPU and
produced no output. The log's last line is the engine banner. By 16:21 the
`launch_pinned.sh` launcher, its `timeout` process and the podman client had all
exited, but no `run3.log.rc` was written, and the containerised `kpex` process
was still running at 16:21. It was then killed by hand at the 2 h time box
(total engine time about 1 h 51 min). The wall time budgeted for B, 14:16-16:21,
was used up. Output files: none besides the LVS-layer dumps kpex writes before
the engine starts. Separate observation: a bounded launch can leave the container
process running after its host-side wrapper exits, so CPU allocations should be
checked with `ps` after a bound expires.

### 2b. Why it cannot finish: measured progress and extrapolation

A second, instrumented copy of attempt 3 ran on CPU 34
(`flow/pex/kpex_progress_probe.py`). The extraction is identical; the copy
only adds counters, logged in
[fullchip_kpex_probe_20260925.log](fullchip_kpex_probe_20260925.log). The
engine's first pass computes the overlap capacitance to the substrate. It
treats the substrate as one polygon, the chip box plus an 8 µm halo, and
visits every polygon above it. For each one, it subtracts a "shielded"
region that grows with every visit
(`klayout_pex/rcx25/c/overlap_extractor.py`, `neighbors`). The cost of each
visit therefore grows linearly, and the pass as a whole grows quadratically.
Measured: 2000 visits took 5.9, 20.7, 37.0, 55.3, 70.4, 89.5, 110.6 and
127.4 s (blocks 1-8), which fits t<sub>block</sub>(i) = 17.53·i − 14.3 s.

| Case | polygons in the pass | extrapolated substrate pass | status |
|---|---|---|---|
| fill-free chip | 467 654 (measured) | **4.8 × 10⁵ s ≈ 5.5 days** | extrapolated from the chip's own 8 blocks |
| with fill (not run, as instructed) | ≈ 718 988 | **1.1 × 10⁶ s ≈ 13 days** | extrapolated, same fit |
| control: top-interconnect view | 20 936 | measured 361 s of a 465 s run (78 %) | `view_kpex_probe_20260925.log` |

The sidewall and fringe passes come after the substrate pass. They are not
included above, so the totals are lower bounds. Block runs for scale (measured,
one CPU): TRIP NF4, 23 k conductor shapes, 761 s; BGR586, 27 k shapes, 2 158 s.

## 3. ngspice cost of a full-chip PEX netlist (extrapolated, not run)

Two measured anchors, both the compact `c_mid` case over 28 µs, transistor-level
analog blocks and RTL digital through `d_cosim`:

| Anchor | Block extractions in the deck | Wall | Log |
|---|---|---|---|
| A, 2026-09-21 | earlier BGR/SENSE/TRIP/GATE C-PEX (about 18 k caps, the "~40 min" figure) | 2 315 s | `sim/campaigns/INTEGRATED_ANCHOR_20260922.md` |
| B, 2026-09-25 | BGR586 (978 C, 1 036 devices) + TRIP NF4 (18 333 C, 2 329 devices) + SENSE partial C + GATE | **19 264 s** | `RESULTS_20260925.md` §3d, `c1414fullc` |

Anchor B is the chip deck as it stands today, and it is already 8× slower than
the "18 k caps → 40 min" premise. A full-chip netlist has 94 357 devices,
about 26× the ≈ 3.6 k in deck B. It would also have about 1-3 × 10⁵
capacitors: 0.29-0.79 C per conductor shape, the ratios of the interconnect
view and of TRIP. The digital core would run as about 88 k transistors
instead of RTL. Scaling linearly with the device count, which is optimistic
because it ignores matrix growth and the extra time points from 1 200 flops
switching at 9.4 MHz, gives **about 17 h per 28 µs case from anchor A and about
6 days from anchor B**. The existing corner, temperature and supply matrix
(72 cells) is out of reach. A fill-inclusive netlist adds about 250 k floating
fill nodes. kpex does not reduce them, and ngspice needs a DC path at every
node, so that variant is not usable as is.

## 4. Recommendation

**A full-chip PEX simulation is not feasible before 2026-09-29.** The
extraction alone (≥ 5.5 days fill-free) is longer than the time left, and a
single transient would take another day or more. What fits:

1. **Chip deck = today's block PEX + `top_interconnect_20260925.spice`.** The deck
   already has BGR586, TRIP NF4, SENSE partial-C, GATE, OSC, T2F and LS PEX. The
   new file has 57 routed top-level nets with extracted ground and coupling C
   and series R (≈ 800 C elements per subcircuit). That is about 4 % of anchor
   B's 21 k capacitors, so no significant runtime increase is expected (not run).
   Replace the `Cw_*` guesses with it. The ISENSE guess of 300 fF becomes
   64.5 fF; `cmp_soft` goes from 20 fF to 270 fF, and the other digital nets
   are 6-13× their guesses.
2. **Run targeted sensitivity cases on the couplings the extraction exposed.**
   VREF–osc_clk is 38 fF, ISENSE–en_i 13 fF and ISENSE–vref_buf 28 fF. The
   SENSE_P/SENSE_N routes are 171 Ω and 106 Ω, which is about 0.65 % of the
   10 kΩ input resistor. Each case is one c_mid/q run at anchor-B cost
   (≈ 5 h).
3. Keep the documented gaps as **not run**: the digital macro's transistor-level
   PEX (its SPEF exists, but the deck uses RTL), coupling between top-level
   wires and macro internals, fill, IO-cell metal and bondpads (53 fF each by
   kpex).
4. A future full-chip extraction first needs the substrate pass fixed: merge
   the shielded region, or use Region booleans once per layer. That is a kpex
   tool change, and this note does not propose it for tape-out.

## Not run

| Item | Status |
|---|---|
| Full-chip kpex CC, fill-free | not run to completion (see §2a) |
| Full-chip kpex CC, with fill | not run (extrapolated only, as instructed) |
| Any ngspice run on a full-chip netlist | not run (no netlist exists) |
| Chip deck with the interconnect lumps | not run |

## Commands

```sh
B=${BULK}/fullchip-pex-20260925
python3 flow/pex/strip_fill.py --input designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414.gds \
  --output $B/nofill/g1_chip_top_1414_nofill.gds --report $B/nofill/strip_fill.json
flow/launch_pinned.sh 28-33 . 7200 $B/kpex_nofill/run.log  kpex --pdk ihp_sg13g2 --threads 6 --gds $B/nofill/g1_chip_top_1414_nofill.gds \
  --cell g1_chip_top --schematic /work/designs/g1-guardian/blocks/g1_padring/netlist/g1_chip_top_1414_projected_ref.cdl --2.5D --mode CC --out_dir $B/kpex_nofill/out
flow/launch_pinned.sh 28-33 . 6400 $B/kpex_nofill/run3.log python3 /work/flow/pex/kpex_named_top.py --pdk ihp_sg13g2 --threads 6 \
  --lvsdb $B/kpex_nofill/out/<run>/g1_chip_top.lvsdb.gz --cell g1_chip_top --2.5D --mode CC --out_dir $B/kpex_nofill/out3
flow/launch_pinned.sh 34 . 3900 $B/kpex_nofill_probe/run.log python3 /work/flow/pex/kpex_progress_probe.py <same arguments, --threads 1>
```

(Each command was wrapped in `sh -c` with `date` and `/usr/bin/time -v` inside the container.)
