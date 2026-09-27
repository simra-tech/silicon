# G1 red-team 2026-09-27: digital (g1_ctrl / g1_seu, r3 macro)

Scope: frozen ECO RTL (`blocks/g1_ctrl/rtl_eco_20260925`, `blocks/g1_seu/rtl_eco_20260925`),
the r3 `g1_digital` macro (gate netlist `4b83f181…`, powered netlist `476885d7…`, macro GDS
`67d049bf…`, SPEF `0b626c7f…`, run root `${BULK}/digital-eco-r3cand2-20260926`), its GLS
(`blocks/g1_ctrl/sim/gls_eco_r3v2`), the formal equivalence (`…/gls_eco_r3v2/equiv`), the SDF
corner runs, the serial protocol and register map 1.2, trip timer, SEU monitor, EN/POR reset
and the clock-domain crossings. Paths below starting `blocks/` are under
`${REPO}/designs/g1-guardian/blocks/`; `RT/` is this directory. All results are **simulated**
or static (Icarus Verilog 14.0 devel s20260301-328, Yosys 0.67, ABC, Verilator 5.050,
OpenSTA as shipped in the pinned container `tapeoutbench-eda`, IHP SG13G2 PDK
`84374023…`); nothing is measured. CPUs 16-21 were used.

## 1. Verdict

**Yes, r3 is safe to submit as is for the digital aspect.** This round found no BLOCKER and no
MAJOR that justifies a GDS change. The logic in the GDS is the frozen RTL. The chain is closed:
RTL ≡ `4b83f181` (the committed proof, plus a new closure of its POR assumption, D4).
`4b83f181` equals `476885d7` cell for cell (5045 logic instances, 0 differences; new check).
`476885d7` is the netlist that LVS matched against the macro GDS. Timing holds with margin.
Hold is still met at the fast corner with a ±10 % OCV derate, which was not applied before:
worst 64 ps, 0 violations. The core logic tolerates any oscillator frequency the trim can
produce: reg-to-reg setup slack is 93.4 ns of 100 ns at the slow corner. RTL lint is clean.
The new items are MINOR:
- A single upset in the serial write hand-over **replays the last host write**. After a
  `CTRL.CLEAR` this clears a latched trip and turns `GATE` on. After `SEU_CMD.CLR_CNT` it erases
  the SEU counts of an irradiation run. The fix costs nothing in silicon: a host rule that
  always ends with a no-op write.
- Three flops are single points of failure for a whole-core reset.
- The evidence package still lists as "not run" two checks that have passed.

S1 from the previous round (serial framing without chip select or CRC) remains open by owner
decision. The host library mitigates it.

## 2. Findings

| ID | Title | Severity | Evidence | Proposed fix | Effort, GDS change |
|---|---|---|---|---|---|
| D1 | One upset in the write hand-over (`wr_tog`, its 2 synchroniser flops, `wr_tog_d`, `wr_en`) replays the last serial write. If that write was `CTRL.CLEAR`, a latched trip clears and G1_GATE re-arms (`GATE` on). If it was `SEU_CMD.CLR_CNT`, the SEU counters are zeroed | MINOR (functional on the irradiation bench; no silicon failure) | `RT/tb/tb_rt27.v` U1, U3: FAIL (hazard reproduced) on the RTL and on netlist `4b83f181`, line for line identical (`RT/tb/tb_rt27_rtl.log`, `RT/tb/tb_rt27_gls.log`). U1: `trip` 1→0 and the G1_GATE latch 1→0 after the upset, `STATUS` reads 0x80. U3: `SEU_PLAIN_L` 0x01→0x00. U2 (host writes `CTRL`=0x00 after the CLEAR): passed | Host rule and `g1_host.py`: after every `CTRL` or `SEU_CMD` write, write `CTRL` = 0x00 so that a replay is a no-op. Add to map §1.3/§4.3 and to the irradiation plan. For a future revision: triplicate the write toggle path or add a consumed/acknowledge handshake | 1 h, no GDS change |
| D2 | Three flops (`rs0`, `rs1`, `en_off`) each assert the whole-core reset on a single upset. Configuration returns to defaults, `FAST_EN` drops to 0 and the inrush mask re-opens for 1024 cycles | MINOR (radiation characterisation) | `RT/tb/tb_rt27.v` U4 (RTL = netlist): after one `rs0` upset, `dac_hard` 0xC8→0xFE, `fast_en` 1→0, `STATUS` 0x88 (INRUSH_ACTIVE). `rs0`/`rs1` also existed in r2; `en_off` is new in the ECO | Document it as a single-point cross-section in the irradiation plan. The host keeps a canary (a non-default `SENSE_OFS` or `OSC_DIV`), polls it and re-arms on a mismatch. The existing S7 read-back scrub does not see a reset that only restores defaults the host happens to use | 0.5 h, no GDS change |
| D3 | The evidence package contradicts itself. `README.md` (bullet "not run: SDF GLS fast/slow, formal equivalence…"), `review/TAPEIN_PACKAGE_20260924.md` (row "Digital GLS on the chip's netlist") and `blocks/g1_padring/reports/signoff-1414r3-20260926/README.md` ("Not run") list formal equivalence and fast/slow SDF GLS of `4b83f181` as **not run**. `blocks/g1_ctrl/ECO_20260925.md` and commit `200fe17b` (2026-09-26) record both as **passed** | MINOR (documentation) | the three files named; `blocks/g1_ctrl/sim/gls_eco_r3v2/equiv/dprove.log` ("Networks are equivalent"), `…/sdf_corners/*_r3cand2_{slow,fast}.log` | Update the three places to "passed", with links | 0.5 h, no GDS change |
| D4 | The committed equivalence proof forces `por_n` low in the first cycle. On the chip `por_n` is tied high, so silicon never passes through that state. The proof covers silicon only if an EN-low period drives the netlist into the POR state | MINOR (evidence qualifier), **closed here** | New X-flush GLS (`RT/xflush/`): every one of the 1222 flops starts at X with `por_n` = 1. After 10 EN-low `osc_clk` edges, 1221 flops are known and equal to a POR-started copy; `en_seen` stays X until EN is first high, which is harmless. After EN rise, a write, a read and an EN cycle, all 1222 flops and all outputs are equal. With 9 edges, 1205 flops are still X; they converge once EN rises (the filter samples EN late). A direct formal miter with EN as the only reset and free initial state (`RT/equiv_en_reset/`) was **undecided** by ABC `dprove` (BMC 19 frames clean, PDR timeout 60 s; see §3 D4 for the longer PDR). Its negative control (`c3aa2856`) gave a counterexample in frame 64 | Add one sentence and the X-flush reference to the equivalence paragraph of `ECO_20260925.md` | 0.25 h, no GDS change |
| D5 | `clk_div_out = osc_pre[osc_div + 8]` indexes bit 15 of the 15-bit `osc_pre` when `OSC_DIV` = 7. The result is X in RTL and undefined in synthesis | MINOR (cosmetic) | `blocks/g1_ctrl/rtl_eco_20260925/g1_regfile.v` (osc counter block). The macro pin has no load on the chip: `i_core_clk_div_out` appears once in `blocks/g1_padring/netlist/g1_chip_top_1414_r3.cdl`. `OSC_CNT` at `OSC_DIV` = 7 is correct (`pre_mask` 0x7FFF) | None for r3. State in map §4.5 that `clk_div_out` is unconnected; widen `osc_pre` to 16 bits in any future RTL | 0 h |
| (S1, carried over) | Serial framing: one SCLK glitch or stall re-frames a write onto another register | carried over, not re-ranked (owner decision, out of ECO scope) | `blocks/g1_ctrl/sim/gls_eco_r3v2/tb_redteam_eco_gls_r3cand2.log` R3 | Unchanged. The host library already applies the ≥128-cycle idle before every frame, read-back, and pull-downs (`measurement/bringup/g1_host.py`). The 1.2 `SOFT_TIME_H` shadow removes the worst redirect (the 0.86 s window) until the next `_L` write | — |

## 3. Per finding

### D1: write replay on a single upset

Checked: `g1_serial.v` hands a write over with a toggle. `wr_tog` is in the SCLK domain and
holds its value while SCLK idles. It passes a two-flop synchroniser; `wr_en = wr_tog_s ^ wr_tog_d`.
`wr_addr_r`/`wr_data_r` keep the last frame's address and data indefinitely. Any flip of
`wr_tog`, `s0`, `s1`, `wr_tog_d` or `wr_en` therefore makes a `wr_en` pulse that re-executes the
last write. For a normal register this rewrites the same value and is harmless. For the
self-clearing commands it repeats the command. The 2026-09-21 fault-injection campaign
(`blocks/g1_ctrl/FAULT_INJECTION_20260921.md`) did not inject into the serial hand-over.

Run (repository root):
`G1_CPUSET=19 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/review/redteam-20260927/digital/tb flow/run.sh bash run_rt27.sh`.
The bench uses the environment of `blocks/g1_ctrl/sim/eco_20260925/tb_redteam_eco.v` (G1_GATE
latch model, dynamic comparators, `por_n` = 1). The upset model inverts `wr_tog_d` from a
falling `osc_clk` edge until just after the next rising edge, which is when the flop reloads.
RTL: a procedural write. Netlist: force/release of the Q net
`\u_core.u_serial.wr_tog_d`, `-DFUNCTIONAL -DUNIT_DELAY=#1`.

Results (RTL and netlist identical):
- U1 (latched mode, a second fault latched after a host CLEAR; upset at 180.25 µs): `trip`
  and the G1_GATE latch both go to 0 at 181 µs, and `STATUS` = 0x80. In latched mode the map
  promises "trip holds until CLEAR or EN cycle". In the model `GATE` turns on again into
  whatever load state exists. If the fault persists, the hard path re-trips after its 9-12
  cycles and `TRIP_CNT` increments.
- U2 (same, but the host wrote `CTRL` = 0x00 after the CLEAR): passed. The replayed write is
  a no-op.
- U3 (irradiation run started with `SEU_CMD.CLR_CNT`, one upset in the plain register counted
  `SEU_PLAIN_L` = 1, then one hand-over upset): `SEU_PLAIN_L` reads 0x00. The count, which is
  the measurement, is erased silently.

Why it matters: this is a radiation test chip, and these five flops are unprotected. The
existing S7 mitigation (periodic read-back of the configuration registers) cannot detect a
replayed command, because commands leave no register value to compare. The host fix costs
nothing. An RTL fix (a triplicated toggle path, or an acknowledge that invalidates
`wr_addr_r`) would need a re-harden and re-sign-off. That is not justified for r3.

### D2: single-flop whole-core reset

Checked: `arst_n = por_n & ~en_off & (en | en_seen)` drives `rs0/rs1`, and `rst_n = rs1`
resets all 1200 core flops. One upset of `rs0` (low for one cycle), `rs1`, or `en_off` (high
for one cycle) resets the core. Run: same command, test U4. `dac_hard` 0xC8→0xFE, `fast_en`
1→0, and `STATUS` = 0x88 (the inrush window restarts) about 20 µs after the upset. If the core
was tripped, the G1_GATE latch stays set and is re-adopted with cause "hard" (logic in
`g1_trip_timer.v`, `trip_ext`), so the gate stays off. This is the safe side, but the
configuration is lost. Before the ECO the single points were `rs0`/`rs1`; the ECO adds
`en_off`. The flip is equivalent to the documented "EN low ≥ 8 samples" behaviour, but it
happens without EN.

### D3: stale "not run" entries

Checked by reading. `README.md` "Digital" bullets; `review/TAPEIN_PACKAGE_20260924.md` row
"Digital GLS on the chip's netlist `4b83f181`"; the r3 sign-off README section "Not run". The
records that supersede them are `blocks/g1_ctrl/ECO_20260925.md` (sections "Gate-level
simulation" and "Formal equivalence") and the logs in `blocks/g1_ctrl/sim/gls_eco_r3v2/`. The
error is on the conservative side: the package claims less than was done.

### D4: equivalence under the chip's reset

What the committed miter proves: `blocks/g1_ctrl/sim/gls_eco_r3v2/equiv/miter_top.v` ties both
designs to the same free inputs. It drives `por_n` low until the first `osc_clk` rise
(`started`), leaves all flop initial values free (`write_aiger -zinit`) and compares all 36
output bits. `clk2fflogic` models both SCLK edges and the asynchronous resets. Nothing is
blackboxed; `read_liberty -ignore_miss_func` leaves only fill, decap and antenna cells without
a function. The proof is sound for every state reachable from POR. On the chip `por_n` is a
`sg13g2_tiehi`, so silicon starts from an arbitrary state.

New runs:
1. X-flush, `RT/xflush/tb_xflush.v`, generated from the netlist's 1222 `sg13g2_dfrbpq_1`
   instances. Command:
   `G1_CPUSET=18 G1_CPUS=1 G1_CONTAINER_ENGINE=podman G1_WORKDIR=designs/g1-guardian/review/redteam-20260927/digital/xflush flow/run.sh bash run_xflush.sh`.
   Log: `RT/xflush/run_xflush.log`. With EN low for NLOW = 10, 11, 12 or 16 edges, 1 flop
   (`en_seen`) is X and 0 flops differ from the POR copy. After EN rise +20 edges, and again
   after a write, a read and an EN cycle, 0 flops are X and 0 differ. Every flop is therefore
   determined by the EN-low period. With `en_seen` = 0 or 1 the state lies in the POR proof's
   reachable set. The committed proof thus covers silicon after the first EN-low period of
   ≥ 10 edges (contract P6). Icarus X semantics are conservative for this purpose: a value
   that resolves to 0/1 does so for every concrete initial state.
2. Direct formal miter with `por_n` = 1 in both designs, EN forced low for 12 edges and
   outputs compared after that (`RT/equiv_en_reset/miter_en.v`, `seq_equiv_en.ys`,
   `run_equiv_en.sh`, CPUs 16-17). ABC `dprove`: BMC clean to 19 frames; the induction
   stages did not close; PDR reached its 60 s timeout: **UNDECIDED** (`RT/equiv_en_reset/dprove_en.log`).
   Negative control against the superseded `c3aa2856`: "asserted in frame 64"
   (`dprove_en_negctl.log`). A longer PDR on the reduced miter `sm01.aig`
   (`pdr -T 1500`, CPU 20): **UNDECIDED** at the 1500 s limit, frame 94, no counterexample (`RT/equiv_en_reset/pdr_sm01.log`). The AIGs, witness maps and Yosys logs are
   in `${BULK}/redteam-20260927/digital/equiv_en_reset/` (sha256 in
   `RT/equiv_en_reset/bulk_files.sha256`).

### D5: `clk_div_out` index

Found by reading. For `OSC_DIV` = 7 the index `osc_div + 4'd8` = 15 is outside `osc_pre[14:0]`.
Verilator `-Wall` does not flag it because the index is dynamic. There is no silicon
consequence: the pin is unloaded. Recorded so that a future revision does not route the pin
out as it is.

## 4. Checked and clean

- Netlist identity (new): `4b83f181` (GLS/equivalence) ≡ `476885d7` (LVS/CDL), 7784 instances, 5045 logic instances, 0 cell/pin/net differences after dropping power pins and fill/decap/tap/antenna cells (`RT/nlcmp.py`, `RT/nlcmp.log`, files from `${BULK}/digital-eco-r3cand2-20260926/final/`).
- The EN-filter reset net `arst_n` in the netlist is one `sg13g2_o21ai_1` (`en`, `en_seen`, `por_n`) into one `sg13g2_nor2_1` (with `en_off`): with `en_seen` = 1 an EN glitch cannot reach `rs0/rs1` through a reconvergent path.
- Hold with OCV derate (new): `RT/sta_derate.tcl`, macro `4b83f181` + SPEF `0b626c7f`, merged macro SDC. Worst hold at the fast corner is 114/98/64 ps at derate 0/±5/±10 %, typ 195/176/130 ps, slow 337/308/250 ps; 0 violations. At fast ±10 %, 8 endpoints are below 100 ps and none below 50 ps. Removal on `rs0/rs1` (the new `en_off` path): 213 ps at fast ±10 %. Summaries in `RT/sta_derate/`.
- Frequency headroom (new, `RT/sta_fmax.tcl`): at 100 ns, reg-to-reg setup slack on `osc_clk` is 97.7/96.6/95.0 ns (fast/typ/slow; worst path is `rs1` → recovery) and 93.4 ns flop-to-flop at slow. The 28.4 ns reported setup slack is the SDO output with its 20 ns output delay. Even the fastest trim-0 oscillator at ff/−40 °C (≈18.6 MHz, 1.5 × 12.41 MHz from `blocks/g1_osc/README.md`) cannot violate core setup.
- Unconstrained endpoints are only the four synchroniser first stages (`cmp_soft`, `cmp_hard`, `tripped`, `en`) (`${BULK}/digital-eco-r3cand2-20260926/sta/main/macro-fast/coverage.rpt`), as intended.
- Lint: Verilator 5.050 `--lint-only -Wall` on the frozen RTL gives 0 warnings. Yosys `proc; flatten; check`: 0 problems, no latches (only `$adff`).
- Register-map reset column ↔ RTL reset values: all 39 entries match (`G1_REGISTER_MAP.md` §4 vs `g1_regfile.v`). `STATUS` 0x80 vs 0x88 during the inrush window is already stated in `measurement/bringup/FIRST_SILICON_SEQUENCE.md`.
- Output glitch hazards to analog: `trip_d`, `cmp_clk` are flop outputs. `fast_en` is an AND of two flops that both fall on reset, so it cannot glitch high. `clr_d` is `|clr_pulse`: its 10→01 transition can at most notch low inside the pulse, never create a spurious pulse.
- CDC read margin: `rd_tog` at rising edge 8, `rd_hold` needed at the falling edge after rising edge 16, which is 8.5 SCLK periods. The osc side needs ≤ 5 `osc_clk` cycles including one metastability cycle, so reads work up to f_SCLK ≈ 1.7 f_OSC. The map limits f_SCLK ≤ f_OSC.
- Trip timer arithmetic: `inrush_cnt` ≤ 0x1FE00 < 2^17; `hold_cnt` resets at `hold_lim` ≤ 0x1FE000 < 2^21 in both the hold and cool-down branches; `soft_cnt` saturates at 0xFFFFFF > max `soft_lim` 0xFFFF00; `hard_cnt` and `trip_cnt` saturate; SENSE_OFS 10-bit signed sum range −128…382. Same conclusion as `redteam-20260925/DIGITAL.md` N6, re-read on the ECO RTL (the `inrush_done` flag does not change the bounds).
- SEU monitor: expected-bit shortcut valid (256/128 even, pattern period ≤ 2); restart on pattern or enable change blocks comparison for `FILL_LEN` = 256 shifts; TMR stage vote rewritten into all copies every shift, so one upset is counted once in `SEU_CORR`; 2 copies in one stage give `SEU_UNC`. Unchanged by the ECO (files byte-identical).
- Host library `measurement/bringup/g1_host.py` matches map 1.2: `SOFT_TIME` written H then L with read-back of the byte in effect, OSC_EN written 1, INRUSH only under inhibit, ≥ 128-cycle idle before every frame.
- T2F: no on-chip counter (`blocks/g1_t2f/INTERFACE.md`: frequency counted off-chip). No digital counter interface to check.

## 5. Not run

- Timing checks in simulation (setup/hold in GLS): **not run** (Icarus ignores them; STA above is the evidence).
- A min/max RC extraction corner: **not run**. Only nominal SPEF exists; the ±10 % derate above stands in for it.
- Synchroniser MTBF (numerical): **not run**. The resolution window is about one `osc_clk` period (≈ 100 ns); no τ characterisation of `sg13g2_dfrbpq_1` is available.
- Digital supply/ground switching noise on the comparators and the oscillator (`redteam-20260925/DIGITAL.md` S6): **not run** (the full-chip decks still run the digital as RTL through `d_cosim`).
- Direct formal equivalence with EN as the only reset: **undecided** (D4). The X-flush closure stands in for it.
- Exhaustive single-upset injection over all 1222 flops: **not run**. U1-U4 cover the serial hand-over and the reset synchroniser only.
- Chip-level co-simulation with the macro's gate netlist and SPEF: **not run** (as recorded in `ECO_20260925.md`).
