# Native MIM ownership and extraction boundary

## Outcome

Read-only native primitive ownership recovery **passed**. Complete,
double-count-safe MIM CPEX remains **not qualified**. No field solver,
meshing, extraction rerun, source change, geometry change, deck change or model
change was performed by this audit. Existing failed whitebox runs remain failed.

The saved native LVS database exposes `shapes_of_terminal(terminal_ref)` as a
dictionary of layer indices to Regions. Those regions recover the three exact
device-owned MIM masks before global-net aggregation:

| Device / native ID | Top / bottom net | Mask dimensions | Area | Perimeter |
|---|---|---|---:|---:|
| XBUF / 934 | `$192` / `vped` | 23 × 23 µm | 529 µm² | 92 µm |
| XOTA / 935 | `n__xota__cz` / `isense` | 69 × 23 µm | 1587 µm² | 184 µm |
| XREF / 936 | `$193` / `vref_buf` | 23 × 23 µm | 529 µm² | 92 µm |

Same-device top/bottom mask XOR, between-device overlap, and union-to-native
MIM-mask XOR are all zero. Owned bottom M5 is 2645 µm²; remaining M5 is
1010.1748 µm², with zero overlap and exact native-M5 partition XOR zero.
`cmim_top` is the dedicated thin MIM plate, **not** the thick TopMetal1 access
metal above it. TopMetal1 access and its fields cannot be discarded as intrinsic
thin-plate geometry.

The ownership result uses the saved r5 PEX-view GDS
`cb9617c97ae522596c5d4aaa7ee91f65e59b418a14d1095e5e0514d4e8c7e010`
and LVSDB `95e8683146bc38ecf9a78e3fde3fe8541c9a888707a77c378b816c9136a1af67`.
It is not a new extraction of the later power-routing revisions. The initial
read-only audit failed on uppercase `W`; the supported native parameter is
lowercase `w`. That failure is retained separately.

## What the canonical model already owns

For this pinned two-terminal `cap_cmim`, the core is an ngspice geometrical
capacitor with `CJ=cap_carea`, `CJSW=40e-18`, zero default narrowing/shortening,
and dimensions converted to micrometres. At the model's 27 °C reference:

`C0 = CJ × Lµm × Wµm + 2 × CJSW × (Lµm + Wµm)`.

The instance scale/mismatch factor multiplies this capacitance, and the model
retains `1 + 3.6e-6 × ΔT + 2e-9 × ΔT²`. Thus the canonical model owns an area
**and perimeter** contribution, not only the plate overlap. These are the
geometrical-capacitor equations in the
[ngspice 46 manual, §3.3.8](https://ngspice.sourceforge.io/docs/ngspice-46-manual.pdf#page=83).

At typical `CJ=1.5 fF/µm²`, mean mismatch and 27 °C, analytic values are
797.18 fF for each 23 × 23 device (793.5 area + 3.68 perimeter), and
2387.86 fF for the 69 × 23 device (2380.5 + 7.36). These are model-equation
calculations, **not measured or extracted capacitances**. The 55 mΩ internal
series resistor, temperature coefficients, corner and mismatch behavior must
remain unchanged. The two-terminal model has no independent substrate terminal.

## Installed-engine implementation boundary

| Stage | Available identity | Consequence |
|---|---|---|
| Native LVS terminal geometry | Device, terminal, layer and net | Exact owned masks can be recovered. |
| FasterCap input `add_conductor` | Net name, Region, z, height | No primitive/terminal ownership argument. |
| Surface generation and export | Net/material; same-net regions unioned | Primitive attribution is lost before the solver matrix. |
| FasterCap parsed result | Net-conductor Maxwell matrix | No native-plate-versus-routing contribution for a same-net pair. |
| 2.5D overlap visitor | Original polygons, layers and net properties | A future owner-aware area partition is conceivable, but unimplemented. |
| 2.5D fringe visitor | Net-grouped/clipped polygons and physical edges | Clipping recreates net-only properties; no validated owner-aware fringe partition. |

Renaming electrically continuous owned plates and routing into separate solver
conductors would change the equipotential boundary conditions and can introduce
artificial surfaces. Collating them back into one conductor restores that
boundary but does not provide an owner-resolved matrix in the installed API.
Therefore pseudo-net renaming is not a demonstrated deembedding method.

A future 2.5D software extension would have to retain physical geometry and
shielding, propagate ownership through clipping, and split contributions before
net aggregation without creating artificial internal fringe edges. It would
also require validated MIM technology coverage and native-model perimeter
composition. This inspection does **not** establish that such an extension is
sufficient or that relevant table coefficients are absent. The historical
unsupported whitebox MIM path remains failed.

The concrete boundary is therefore: **primitive geometry ownership is
recoverable; primitive-owned field decomposition is not supplied by the
inspected pinned engine interfaces**. Whole-net-pair subtraction, subtraction
of a chosen golden/model capacitance, removal of all same-device terminal-pair
coupling, or replacement of the canonical model is not authorized or justified.
Full-macro 3D and complete CPEX remain **not run / not qualified**, respectively.

## Built against

| Component | Version / identity | Evidence |
|---|---|---|
| IHP SG13G2 open PDK | `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` | Existing pinned runtime gate; model/PCell SHA256 values in audit JSON. |
| KLayout | 0.30.9 | Runtime API audit. |
| KLayout-PEX | 0.3.12 | Pinned runtime; five inspected implementation-file hashes in audit JSON. |
| ngspice | 46 | Pinned runtime and manual; no ngspice process launched in this audit. |

Reproduction: run `audit_mim_ownership_api.py --help` for required saved-input
arguments, using the pinned runtime and an unused output directory. The audit
reads saved evidence only; it does not launch a solver. Raw result directory is
`${RESULTS_ROOT}/sense-mim-ownership-20260922-r2`. Public portable export is
**not run** at this checkpoint.
