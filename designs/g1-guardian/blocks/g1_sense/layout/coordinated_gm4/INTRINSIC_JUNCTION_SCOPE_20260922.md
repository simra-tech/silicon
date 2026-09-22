# SENSE junction annotation versus intrinsic applicability

## Result

The 51 failed stock A/P annotations are now localized to a **representational
MOS-combination failure**, not evidence that 51 physical native devices have
wrong junction dimensions. All failures remain recorded as failures; no stock
deck, source, model, stored database or golden parameter was corrected.

The separate shared-PSP applicability question concerns **six input MOS**, not
all 58: XM1/XM2 in XOTA, XBUF and XREF. The other 52 devices have single-owner
native diffusion and independently match source-native W/L/ng and default A/P.
That geometry result is not a new electrical/model qualification.

## Orientation-controlled native combiner reproducer

The installed KLayout0.30.9 API was tested in memory with two MOS4 devices
connected in parallel. A same-orientation control preserves each physical
net's area/perimeter. A second control reverses the second device's S/D
identities and also reverses its A/P fields, so the two physical circuits have
identical intended per-net geometry. Native `combine_devices()` then produces
incorrect averaged per-net A/P, while aggregate S+D totals stay conserved.

| Two-device diagnostic | Expected source / drain | Actual source / drain |
|---|---|---|
| Same orientation, area µm² | 4.08 / 2.28 | 4.08 / 2.28 |
| Reversed second S/D, area µm² | 4.08 / 2.28 | 3.18 / 3.18 |
| Same orientation, perimeter µm | 25.36 / 12.76 | 25.36 / 12.76 |
| Reversed second S/D, perimeter µm | 25.36 / 12.76 | 19.06 / 19.06 |

The official v0.30.9 implementation adds same-named A/P parameters before
joining terminals, including when their source/drain connectivity is reversed.
This independently agrees with the installed API control.
[KLayout v0.30.9 MOS combiner source](https://github.com/KLayout/klayout/blob/v0.30.9/src/db/db/dbNetlistDeviceClasses.cc#L279-L365).

The diagnostic completed in 8.946 s including runtime startup. It generated no
GDS, ran no circuit simulation and modified no extraction rules. A source-to-
binary rebuild was not run; installed behavior was tested directly.

The new analysis of all58 r7 records shows that every stock source/drain area
equals `(native AS + native AD)/2`, and every perimeter equals
`(native PS + native PD)/2`, within 1e-8 µm/µm² arithmetic tolerance. Exactly
51 even-ng devices have asymmetric defaults and therefore fail; all seven
odd-ng devices have symmetric defaults and pass. This complete correspondence
and the reversed-terminal control explain the observed annotation pattern.
Stock main-LVS Match still does not compare A/P or ng.

## Actual shared physical junction scope

The independently saved native strip/gate-owner audit identifies:

| Logical pair | Cross-owner source strips | Shared physical area | Shared physical perimeter |
|---|---:|---:|---:|
| XOTA XM1/XM2 | 32 | 72.96 µm² | 408.32 µm |
| XBUF XM1/XM2 | 8 | 18.24 µm² | 102.08 µm |
| XREF XM1/XM2 | 8 | 18.24 µm² | 102.08 µm |

Every shared strip belongs to that pair's common tail net, with one neighboring
gate from each logical device. The existing equal adjacent-gate allocation
reproduces each canonical default A/P; globally each physical strip is counted
once. This is exact geometric accounting, not a uniquely defined physical
partition into two independently mismatched PSP junctions. Drain strips and
all other devices are single-owner in this audit.

## Why correcting annotation does not close intrinsic applicability

The already-hashed pinned PSP103 sources show linear area/STI-edge/gate-edge
weighting of junction current and charge **at common internal junction bias,
model, temperature and limiting conditions**. Equal external tail and body
net names do not prove those internal conditions:

- `SWGEO=1`, `SWJUNCAP=3` derive effective gate-edge width from `WE`; STI
  perimeter subtracts that width. Width mismatch therefore changes the edge
  partition even though nominal AS/AD/PS/PD were geometrically preserved.
- W/L mismatch changes effective geometry; DELVTO/FACTUO act on the channel
  and can indirectly change operating voltages. None is safely assumed to
  leave all junction terms identical.
- Non-RF cards retain finite well/bulk and source/drain junction resistances.
  Junction voltage is evaluated between SI and BS, not just source and bulk
  pins. The source-level `RJUNSO=5000 L/W` is26.0417 Ω for each main input
  device and104.1667 Ω for each buffer input. Internal NF scaling and branch
  multiplication must both be retained; these are parameter calculations,
  not measured layout resistances or a claimed time constant.
- Forward-current limiting depends on junction geometry. Additivity outside
  a proven common regime cannot be assumed from aggregate A/P equality.

These facts block an **unconditional equivalence proof**. They do not by
themselves demonstrate a consequential numerical mismatch in the present
operating region. Actual internal-junction-voltage and electrical-sensitivity
controls remain **not run**. No model change is presently proven necessary.

## Bounded next choices requiring review

1. Keep the present source and geometry, and establish a reviewed applicability
   contract for the six shared input devices. A diagnostic could observe
   executable internal junction bias/charge in a small frozen nominal/mismatch
   pair fixture before proposing any model-boundary alteration. It cannot
   establish silicon truth solely by comparing two arbitrary fitted models.
2. Use independent complete native arrays for each logical input MOS, which
   removes cross-device diffusion sharing without source A/P tuning. Existing
   isolated independent-array controls establish native geometry feasibility,
   but placing two disjoint straight arrays loses the current exact coincident
   centroids. Matching/layout tradeoffs and rerouting would need explicit review.
3. A foundry-supported shared-junction compact-model boundary could address
   the issue directly, but no such supported contract is established here.
   Splitting/replacing canonical devices, tying internal PSP nodes, changing
   model cards or fitting golden A/P is **not implemented or authorized**.

The representational failure could separately be addressed by an upstream
orientation-aware combiner or source-preserving parasitic mapping, but neither
is applied to the frozen stock flow. Complete extrinsic MIM PEX remains an
independent blocker documented in the ownership-boundary report.

## Evidence and reproduction

[Native API control](mos-combiner-semantics-20260922-r1.json),
[all58 attribution/shared-strip analysis](intrinsic-junction-scope-20260922-r1.json),
and the previously committed [pinned PSP equations](psp-junction-source-equations-20260922-r1.json)
retain exact source/artifact hashes. Run `audit_mos_combination_semantics.py`
in the pinned runtime with one CPU7 and a fresh output; then run
`audit_intrinsic_junction_scope.py` against the recorded r7 reference, junction
audit and control JSON. Both commands preserve design and rule/model sources.

Built against IHP SG13G2 PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`,
KLayout0.30.9 and the existing pinned PSP/OSDI hashes. Version was checked at
runtime; new OSDI compilation and ngspice simulation were **not run**.
