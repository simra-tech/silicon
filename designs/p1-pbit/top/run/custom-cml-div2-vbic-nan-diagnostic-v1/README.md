# Isolated VBIC NaN Diagnostic Evidence Package V1 (`p1_clk_divider_div2_tran_v5_vbic_diag_v1`)

## 1. Scope & Package Summary

This evidence package contains the isolated C-source diagnostic patch, execution history, raw dataset summary, and diagnostic marker analysis for the $4.0$ ns transient simulation on Candidate V5 (`p1_cml_div2_front_integrated_sinks.spice`).

## 2. Invocation History & Execution Audit

Execution history across all build and simulation attempts is documented in `EXECUTION-HISTORY.tsv`:
* **Build Attempt 1:** `make -j4` timed out at 180s. Build log `build_attempt1_incomplete.log` is incomplete ending at process termination (retained in private workspace).
* **Build Attempt 2:** `make -j8` resume completed in 29.84s (exit code 0). Compiled executable `ee402436` in isolated build tree. Resume stdout transcript was not retained.
* **Simulation Attempt 1:** `ngspice` CLI run with `-s` flag exited 1 because `-s` specifies server mode in ngspice main.c, ignoring positional deck arguments and returning error no circuit loaded. Created zero raw file.
* **Simulation Attempt 2:** Executed without `-s` flag. Exited 0, creating raw dataset `raw_tb_p1_cml_div2_front_tran_v5.raw` (`c2f70547`) and log `evidence/tb_p1_cml_div2_front_tran_v5_vbic_diag.log` (`854dd63d`). Exactly one loaded $4.0$ ns transient was executed.

## 3. Diagnostic Marker & Warning Line Audit

* **`[VBIC_NAN_DIAGNOSTIC]` Marker Count:** `1`
* **Generic Warning Line 1 Count:** `1`
* **Generic Warning Line 2 Count:** `1`

### Exact First Diagnostic Marker Line:
```
[VBIC_NAN_DIAGNOSTIC] Instance: q.xdiv2.xqs_comp_s.qnpn13g2 | Vrth(current): -nan (isnan=1) | Vrth(stored): -0x1.802fd620a7987p+8 (isnan=0)
```

* **Mapped Device Instance:** `XQS_COMP_S` (Physical Line 91 of Candidate V5 netlist `p1_cml_div2_front_integrated_sinks.spice`, $N_x=6$ Slave Stage PTAT Tail Source).
* **Current Operand:** `-nan` (`isnan = 1`)
* **Stored Hex Operand:** `-0x1.802fd620a7987p+8` (`isnan = 0`)
* **Operand Physical Unit:** `unresolved` (No physical unit confirmed for internal `.t` node from local sources).

## 4. Preservation & Status Classifications

* **Preservation Status:** All previous candidates (V1 `12177cd5`, V2 `64226d85`, V3 `d5900dae`, V4 `e4c68bc7`, V5 `689d4beedfce278f0c13cf0e79a25b87ba8a12d25b9459e51dfbfde041cd3db7`), packages, schematics, netlists, symbols, logs, raw datasets, and TSVs are preserved 100% untouched on disk.
* **Engineering Status:** `Status: UNKNOWN / NOT EVALUATED` (Isolated VBIC NaN diagnostic execution only; no performance, specification, signoff, or tape-out-readiness claims made; project engineering status remains UNKNOWN).
