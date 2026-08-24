# code-540 crossing re-location — refuted: the l=5.4u comparator is saturated, not band-misplaced (2026-08-24)

After `val540-nomismatch-negative/` showed the l=5.4u build flat LOW across every
l=483u crossing band, the next step was to *re-locate* the `pbit_raw_core`
LOW→HIGH crossing on the surviving `C169-final.spice` netlist, then re-band the
island check around it. This directory holds that attempt and its result: **the
crossing to re-locate does not exist** — the comparator is saturated LOW at code
540 by DAC over-drive, so re-banding at any offset can only reproduce uniform LOW.

All four decks ran in container `sandboxy-dfae180cb900847d`, ngspice-46, PSP via
OSDI from the PDK `.spiceinit`.

## The result, bounded

`pbit_raw_core` is **pinned LOW** (≈ 8.5e-8 V; `pbit_out_core` = 1.2 V) at every
sampled input offset, and the analog collector pair never balances. The combined
sampled coverage is −400…−365 mV, −120…−70 mV, +100…+160 mV (code 540) plus the
earlier −45…+50 mV and ±200 mV probes; gaps between those bands are NOT measured.

| deck | sweep (code 540 unless noted) | result |
| --- | --- | --- |
| `probe540w.cir` | −400…+200 mV, 5 mV steps (stopped at −365; −400 hit "Timestep too small") | `pbit_raw_core` LOW at −400…−365 mV |
| `probe540d.cir` | −120…+120 mV, 5 mV steps (stopped at −70) | LOW; analog `c_p−c_n` = +0.167…+0.145 V, **never ≤ 0** |
| `probe540p.cir` | +100…+400 mV, 20 mV steps (stopped at +160) | LOW; `c_p−c_n` grows +0.242…+0.772 V |
| `probe0d.cir` | code 0, −60…+60 mV, 10 mV steps (complete) | **HIGH** (1.2 V); `c_p−c_n` ≈ −0.17 V |

The analog `c_p−c_n` gap is U-shaped, bottoming at **+0.145 V** near vv = −70 mV
and growing on both sides. It is never ≤ 0, so the regenerative latch is biased to
settle LOW for all inputs at code 540. The **code-0 control** on the same netlist
gives the opposite clean state (HIGH, `c_p−c_n` negative), proving the latch /
sense-amp chain is functional and the code-540 pin is a DAC-bias effect, not a dead
latch. (Code 0 is itself saturated HIGH across ±60 mV — the V7 DAC full-scale
exceeds ±60 mV, versus the old l=483u netlist whose code-540 crossing sat at −38 mV.)

## Root causes (netlist facts, verified independently; no source modified)

1. **Primary — V7 DAC over-drive.** At code 540, 135 of 150 unary elements are ON
   (`floor((v(code)*100+0.5)/4) = 135`), each ON element steering into `c_n`
   (`XSWUN*`), which holds `c_n` below `c_p` for the entire input range. The V7
   merge drops the `1.037u` DAC compensation (`C169-final.spice` lines 269–270:
   *"NO 1.037u compensation encoded … re-tune on the ensemble targeting x=1.03"*),
   so the LSB is several× the netlist that produced the −38 mV crossing.
2. **Secondary — undriven `SACLK`.** The sense-amp clock appears only as a gate
   input (`XSA_T` line 205, `XPC1`/`XPC2` lines 240/241) and is never tied to
   `CLK_N`, despite the design comments ("evaluate on CLK_N high" line 195,
   "gate=CLK_N" line 236). It floats ≈ 0.719 V. `CLK_N` drives only the HBT latch
   tail (`XQCLK_LATCH`, line 146).

## What this means for the island question (G-12 aftermath)

The prior `val540.cir` "all four codes uniformly LOW" was **not** a wrong band
location. It was a **saturated comparator**: at codes 540–543 the DAC over-drive
pins `pbit_raw_core` LOW over the whole input range, so there is no HIGH background
to expose a LOW island against and no crossing to band around. Reproducing the
541-543 island requires a **source-level fix** (re-tune the V7 DAC LSB back toward
the −38 mV / code-540 regime, and connect `SACLK` = `CLK_N`) — a source modification
gated on operator sign-off. Option (b) of the island-rate re-baseline
(re-baseline on the l=5.4u v7-merged build) is therefore invalidated on a second,
mechanistic ground: not only does the l=5.4u build not share the l=483u trim origin
(`l54u-crossing-probe/`), it saturates at the exact codes the island would occupy.

The island-rate result stands at n=8 (Wilson 95% 0–32.4%, `../` README). The 5.75x
scaling recommendation is unchanged — it rests on dead codes and monotonicity, not
on the island rate. Absence of a crossing outside the sampled offsets is NOT
measured.

## Deck/log identity (sha256)

| file | sha256 (first 16) | role |
| --- | --- | --- |
| `probe540w.cir` / `.log` | `8e6fa45d…` / `147ff251…` | widened digital sweep −400…+200 mV |
| `probe540d.cir` / `.log` | `8bb02f27…` / `a878d261…` | code-540 diagnostic −120…+120 mV (digital + c_p/c_n/cml) |
| `probe540p.cir` / `.log` | `8ed23359…` / `dfd1e951…` | code-540 positive sweep +100…+400 mV |
| `probe0d.cir` / `.log` | `cd219be9…` / `1fd9f3ee…` | code-0 control −60…+60 mV (complete) |
| `FINDINGS-540-relocate.md` | `c6518063…` | Design Engineer's narrative + tables |
| `SHA256SUMS.txt` | `49ee1183…` | Design Engineer's full evidence manifest |

The four `.cir` decks carry container run paths in their `.include`/`.lib` lines;
they map onto the parent directory: `/tmp/C169-final.spice` →
`../C169-SOURCE-coarse-dac-v7-merged.spice` (`97938952…`) and the
`C156-ISOBUF-PBIT_OUT.spice` workspace path → `../C156-ISOBUF-PBIT_OUT.spice`
(`81c708e1…`). All four decks retain the two inert `VEDP`/`VEDN` force-biases
(H-1343: `vedp#branch = 0`, `vedn#branch = 0`).

## Run requirement

ngspice must start from `/foss/pdks/ihp-sg13g2/libs.tech/ngspice` with
`PDK_ROOT=/foss/pdks PDK=ihp-sg13g2`, or the IHP PSP models fail to load
('Unknown model type psp103va' / 'model name is not found').
