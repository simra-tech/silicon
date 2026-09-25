# Draft: upstream report on sg13g2_io KLayout LVS (not posted)

Status: **draft, not posted**. The owner decides whether to post. Prepared 2026-09-25.

## Upstream state found (2026-09-25)

| Item | URL | State | Relevance |
|---|---|---|---|
| Issue #1218 "Poly resistor is not being extracted in secondary protection for Analog IO" (LuighiV, 2026-09-07) | https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1218 | open | our cause (1) |
| PR #1223 "stdcell and IO alignment sg13g2 and sg13cmos5l" (b10346), merged to `dev` 2026-09-18 as `719b8fd6` (content commit `2e256188`) | https://github.com/IHP-GmbH/IHP-Open-PDK/pull/1223 | merged, `dev` only (not on `main` at `5e6d592e`) | adds PolyRes 128/0 to RPPD in SecondaryProtection and RCClampResistor |
| Issue #1130 "SG13G2 IO diode leaves do not strict-deep LVS-match official schematics" (2026-08-30) | https://github.com/IHP-GmbH/IHP-Open-PDK/issues/1130 | open, no replies | our cause (3), DCN/DCPDiode |
| PR #1105 "Honor PURGE conditional in rfmos_model_mapping.lvs" (merged `dev` 2026-08-26, on `main`) | https://github.com/IHP-GmbH/IHP-Open-PDK/pull/1105 | merged | removes the unconditional `purge_devices` that dropped the three LevelDown dummy PMOS |
| Issue #955 / PR #1032 `--disable_tap_extraction` | https://github.com/IHP-GmbH/IHP-Open-PDK/issues/955 | option merged | tap checking can be switched off; does not fix IO references |

Because #1218 and #1130 already exist, a new issue is only needed for the
residual substrate/tap mismatch that remains **after** #1223 and #1105. Two
texts follow: (A) a comment for #1218, (B) a new issue.

## Evidence behind the texts (runs of 2026-09-25, KLayout 0.30.9, pinned image `ddeb6957…`)

- XOR of `libs.ref/sg13g2_io/gds/sg13g2_io.gds` at `84374023` (sha256 `4281a855…`)
  against `dev` `4fd47c5e` (`25ecbd87…`): the only geometry differences are
  128/0 PolyRes: one 1×2 µm body in `sg13g2_SecondaryProtection`, 26 bodies
  (520 µm²) in `sg13g2_RCClampResistor`. Two via cells are renamed with identical
  shapes. `sg13g2_IOPadOut30mA`, `IOPadVss`, `IOPadIOVss`, `Filler200`, `Corner`
  are identical.
- Our design-local cells `g1_io_secondary_polyres_r1` and `g1_io_rc_polyres_r1`
  (in `g1_chip_top_1414.gds`, `629d303a…`) are identical on every layer to the
  `dev` stock `sg13g2_SecondaryProtection` and `sg13g2_RCClampResistor`.
- Cell-level LVS, `dev` deck + `dev` GDS + `dev` CDL, flat, `--top_lvl_pins`:
  IOPadAnalog, IOPadIn, IOPadVdd, Filler200 all **failed**. The RPPD bodies are
  now extracted with correct `pad`/`padres` terminals (the `pad`+`padres`
  short is gone); the dummy PMOS `I0.P0` in IOPadIn is now paired. Residual:
  local `sub!` nets, ptap and diode pairing.
- Same with a reference-only copy of the `dev` CDL prefixed by `.GLOBAL sub!`:
  still **failed** on all five cells tried (IOPadOut30mA added); mismatch counts
  dropped (IOPadIn from 8 nets/6 devices to 4/3).
- Full chip, `dev` deck, canonical CDL, deep: **failed**, the same 14 IO sub-cell
  NoMatch as with the pinned deck.

Logs are retained locally, not in the repository.

## (A) Comment for #1218

> PR #1223 (merged to `dev` 2026-09-18) adds PolyRes 128/0 over the RPPD
> bodies in `sg13g2_SecondaryProtection` (1 body, W1/L2 µm) and
> `sg13g2_RCClampResistor` (26 bodies, W1/L20 µm). With the `dev` KLayout deck
> the RPPD in IOPadAnalog/IOPadIn/IOPadVdd is now extracted and `pad`/`padres`
> are separate nets. An XOR of `sg13g2_io.gds` between `84374023` and `4fd47c5e`
> shows no other geometry change apart from the 128/0 shapes. Could this issue be closed with a
> reference to #1223, and could #1223 be carried to `main`?

## (B) New issue

**Title:** sg13g2_io: IO cells still fail cell-level KLayout LVS against sg13g2_io.cdl after #1223 (local `sub!`, ptap, Filler200)

**Body:**

> **PDK:** `dev` at `4fd47c5e` (also reproduced at `84374023`). KLayout 0.30.9.
>
> **Reproducer** (from `ihp-sg13g2/libs.tech/klayout/tech/lvs`):
>
> ```
> python3 run_lvs.py --layout $PDK_ROOT/ihp-sg13g2/libs.ref/sg13g2_io/gds/sg13g2_io.gds \
>   --netlist $PDK_ROOT/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl \
>   --topcell sg13g2_IOPadAnalog --run_mode flat --top_lvl_pins --run_dir run_analog
> ```
> Repeat with `sg13g2_IOPadIn`, `sg13g2_IOPadVdd`, `sg13g2_IOPadOut30mA`, `sg13g2_Filler200`.
> All report "Netlists don't match".
>
> **After #1223 and #1105:** RPPD extraction and dummy-PMOS purging are fixed.
> These three classes remain:
>
> 1. **`sub!` is local in every subcircuit.** The CDL has no `.GLOBAL sub!`, so
>    the flattened reference has one `sub!` net per instance (`I3.SUB!`,
>    `I5.SUB!`, `I4.SUB!`, ...). The layout extracts one substrate net.
> 2. **Filler200 taps.** The layout extracts four `ptap1` devices: three on
>    separate `iovss` rail pieces (`iovss`, `iovss$1`, `iovss$2`, A≈13.5–13.75 µm²)
>    and one on `vss` (A=0.678 µm²). The CDL has two (`XR0 iovss sub!`
>    A=40.96 µm², `XR1 vss sub!` A=0.681 µm²). `vdd` and `iovdd` connect to no
>    device. The rails are joined only by abutment, so the cell cannot pass
>    alone.
> 3. **Antenna diodes / ptap pairing.** Even with `.GLOBAL sub!` added to a copy
>    of the CDL, the dantenna/dpantenna and ptap devices do not pair. In a
>    full chip with 22 IO cells we see: DANTENNA record count −2 with equal
>    summed multiplicity (64 = 64: layout m=4 groups vs reference m=2); source
>    A=35.003 µm² vs extracted 35.0028 µm²; 386 reference ptap1 records vs two
>    combined extracted taps. This overlaps with #1130 (DCN/DCPDiode).
>
> **Questions**
> - Is `sub!` meant to be global in `sg13g2_io.cdl`? If so, can `.GLOBAL sub!`
>   be added, or can the LVS deck map `sub!` to the substrate net?
> - Are the IO cells meant to pass cell-level KLayout LVS, or only as abutted
>   rings? If only as rings, is there a reference ring (GDS + CDL) that passes?
> - Should the ptap1 A/P values in the IO CDL match the drawn tap geometry, or
>   are they electrical-model values that the deck should not compare?

## (C) Possible fix to propose

The PolyRes fix upstream is a GDS change, already merged. Nothing is left to
propose for it.

For the residual mismatch, a fix that changes only the reference or the deck is
possible. It is **not validated**: the `.GLOBAL sub!` test above did not reach a
match.

```diff
--- a/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl
+++ b/ihp-sg13g2/libs.ref/sg13g2_io/cdl/sg13g2_io.cdl
@@ -1,3 +1,4 @@
+.GLOBAL sub!
```

A deck-side alternative is to treat `sub!` as a global net when the reference
is read, so the CDL stays as it is. Neither alternative fixes the
Filler200/ptap area comparison. That still needs the IO CDL tap values aligned
with the drawn taps, or IO-cell tap comparison disabled
(`--disable_tap_extraction` exists but applies to the whole chip).
