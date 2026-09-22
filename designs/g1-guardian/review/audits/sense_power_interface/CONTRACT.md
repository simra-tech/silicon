# Source-held SENSE chip power interface

This isolated candidate does not change the r8 macro, primitive geometry,
canonical electrical source, package pins, root supply spines or production GDS.
SENSE `vdd` is **VDDA**, not the core-ring VDD. SENSE `vss` is VSS.

Inputs are the source-pinned full native instance assembly r3 and its matching
DEF-preparation r3 / OpenDB r4. The original assembly SHA256 is
`8b66a958759478987fa9de59746a0554f9bd065307e730342f10e891082134e6`.
SENSE r8 source SHA256 is
`8060e30ac14a1c4aeb1cf62204c9e95d9a68dbad3d73412fbb34c6a33be8b4f7`.
The canonical electrical source remains
`baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877`.

## Frozen first implementation

All coordinates below are chip-level micrometres.

- VDDA: TM2 2.2-wide path (813,714), (813,726), (1048,726),
  (1048,395). M3 2.2-wide bridge from (1048,395) to pad07 bare access
  (1093.145,395). At (1048,395), Via3 and Via4 each 4-by-3,
  TopVia1 2-by-2 and TopVia2 2-by-1. No via lands on either core ring.
- VSS: TM1 2.2-wide escape (805,714), (803.8,714), (803.8,722).
  TopVia2 2-by-2 at (803.8,722); TM2 2.2-wide connection to
  (736.8,722); TopVia2 2-by-2 at that reserved root VSS lane-5 handoff.
  The handoff TM1 footprint is [734.72,719.92,738.88,724.08].
- No other vias. The VSS flyover crosses proposed root TM1 axes 750 (VDD)
  and 774 (VSS) without cuts. Root owns these axes and all spines.

Prospective gates: exact source hashes; immutable primitive and text snapshots;
additive layer-XOR and saved roundtrip; native other-net overlap/spacing screen;
same-net layer continuity, legal arrays and no existing-cut interference;
physical SENSE-VDDA to pad07 connection, SENSE-VSS to handoff connection,
and continued distinct core VDD/VSS domains; stock DRC with original failures
retained. Root merge must independently check routed signals, spine geometry,
all other macro interfaces, final stock rules and source connectivity.

The first read-only screen passed for VDDA; the original VSS landing centred
at x805 had conservative 5-um proximity and is retained as an unsuccessful
placement screen. The implementation uses x803.8 instead. No rule is waived.

## Current scope

The exploratory SENSE branch envelope is 2 mA, with a prospectively declared
50% engineering target against public SG13G2 105 C / 11-year table limits.
This is not a foundry derating rule or 125 C qualification. M3 bridge width
2.2 provides a 2.2-mA half-table screen; twelve Via3/Via4 cuts provide 2.4 mA,
or 2.2 mA with one cut unavailable, assuming equal current sharing.
Worst-single-cut allocation is reported separately and fails that screen for
lower vias. Actual current sharing, local temperature, IR, pulse/lifetime,
full-corner bound and native pad07 internal capacity are **not run**.

Representative simulated hot SENSE VDD peak is 1.5091687157 mA from the
qualified 102-terminal fixture (one seed, nominal supply/process, CM0 and
25-mV shunt, 1.02-us DC-initialized transient). It is not a worst-case bound
or a budget for the other VDDA consumers. Full field-domain composition and
SENSE parasitic qualification remain blocked independently; no extraction
or electrical adoption follows from this supply routing candidate.

## Built against

| Item | Pinned version / evidence |
|---|---|
| PDK | SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; unchanged rules/cards |
| KLayout | 0.30.9; runtime assertion |
| Execution | One CPU per process, fresh shared-resource gate, bounded runtime |
| Stock DRC | Not run at contract creation |
| Full-chip LVS, density, antenna, PEX and adoption | Not run |
