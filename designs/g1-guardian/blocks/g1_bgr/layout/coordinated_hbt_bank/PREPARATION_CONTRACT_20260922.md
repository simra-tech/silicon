# Source586 HBT-bank return ownership — preparation contract

This revision prepares two contact controls and an immutable 301-device source /
placement ledger. It does not generate or qualify a routed full bank. The passed
34-HBT worst-row r2 pilot remains unchanged; its original r1 DRC failure remains
part of the evidence.

## Frozen inputs and limits

| Input | SHA256 / identity |
| --- | --- |
| Source586 | `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |
| Fixed pack | `2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb` |
| Passed HBT contact manifest | `bcdb1f01f4287db750935896756b5947db22898612a9bb77b229f6f0553d4fc2` |
| Combined stock controls | `42d35eaf4daec387389fc0e027e1db271f542536d850f4b01524f5d5a496ae48` |
| Original contact builder | `1fdc4be4be7cbcc0891aab1403c7f4024a4dc301bfae2ce2cf6592e15118ebdd` |
| Original helper generator | `dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e` |
| PDK | IHP SG13G2 `84374023ee8b4b126bebbba67fcbada0a9c0ff0b` |
| Runtime | KLayout 0.30.9; image `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2` |

One geometry preparation invocation only, CPU0, 180 s watchdog, 4 GiB RAM
reservation (not an enforced rootless-v1 limit), at most 0.10 GiB HOME growth,
after a fresh 50%-otherwise-available-CPU / RAM / effective quota / inode gate.
No stock check, analog run, placement change, model/deck edit or retry ladder.

## Exactly two contact variants

Use frozen prototype 01 (C=B, XQ56 representative) and prototype 02 (C!=B,
XQ67 representative). Their source hashes and all five original prototype GDS
hashes are checked against the frozen manifest. Copy the original GDS hierarchy
without regenerating native devices. Remove exactly six top-level bridge
shapes per variant, all at the original local origin (10,10) µm:

| Layer | Shape / bounding box in µm |
| --- | --- |
| M1 | extra pad `(9.58,6.97)-(10.42,7.27)` |
| M1 | Via1 landing `(9.64,6.97)-(10.36,7.27)` |
| Via1 | left cut `(9.695,7.025)-(9.885,7.215)` |
| Via1 | right cut `(10.115,7.025)-(10.305,7.215)` |
| M2 | Via1 landing `(9.64,6.97)-(10.36,7.27)` |
| M2 | emitter-to-ring stem `(9.64,6.76)-(10.36,9.76)` |

Delete exact top-level shape identities, not flattened geometric differences:
overlapping native metal must never be removed. All other top-level shapes,
texts and instances, and every recursive native-child layer, must be identical.
Record exact shape deltas and flattened layer XOR. Native Activ/GatPoly and all
other non-M1/M2/Via1 layers must have zero XOR. The nine all-ground dummies use
the original prototype 00 without any edit.

For each variant, a physical M1/M2/M3 graph through Via1/Via2 must demonstrate:
the original E and substrate-guard seeds connect, while the revised E and guard
seeds are separate; C and B have precisely the source's diode/distinct pattern;
neither C nor B shorts to either return; every via is landed on both layers.
Labels are observations, never virtual conductive joins. Unjoined contact
controls retain the original source-VSS labels and exact source-terminal CDL;
there is intentionally no source-exact connected VSS claim or LVS credit until
a physical external star is supplied and checked. The graph proves metal
separation only, not isolation through the silicon substrate.

## Full-bank ledger and prospective return topology

Freeze all 301 original HBT source lines and fixed pack positions, eight source
nets (`vss vbe c2 dvbe vd1 vd2 b1b vbe3`), all original replication groups and
their centroids. Preserve all nine dummy devices. Actual source count is 336
MOS + 301 HBT + 399 resistors; no full-macro source terminal is renamed.

| Functional E=VSS family | Count | Proposed physical return ownership before star |
| --- | ---: | --- |
| XQ56 | 24 | Precision loop: emitter branch meets XR16 R1 return at declared precision reference point |
| XQ60 | 4 | Separate output-reference leg branch; do not hide its drop in the XQ56/R1 branch |
| XQ67 | 24 | Separate mode-coupled branch; assess selectable-path current before sharing impedance |
| XQ62 | 24 | Separate startup-detector branch; avoid startup-current drop in precision branches |
| All substrate guards and nine dummies | 301 guards / 9 dummies | General VSS metal, separate from functional emitter branches until star |

The other 216 functional HBT emitters use their actual source nets: 192 DVBE
and 24 VD2. Their original contact recipes remain unchanged.

These are physical route roles, not new source nets. A future ledger must
distinguish four functional return trees and general guard VSS even though all
are source VSS. Merely routing XQ56 separately is insufficient. XQ60, XQ67 and
XQ62 remain coupled by the intended source circuit and eventually by finite
shared impedance at the star. No current/IR/noise/matching budget is established.

The separate resistor-bank pilot presently declares its XR16 precision / general
VSS join at local x=16 µm between M3 y=15.06 and 16.26 µm. A future integrated
layout must choose this same star or explicitly revise the combined ownership
contract; it must not add a second star through guard rings, dummy cells,
source-VSS labels, another bank trunk or upper-metal power-ring geometry.
The HBT-to-resistor precision connection is not run. The contact controls do
not themselves include a star or claim that this location is optimal.

After the contact controls, a future bounded routing test must review the
worst-row channel demand with these extra physical return roles, collector
widths/via pads, all neighboring contacts, and finite star routing. The passed
six-net pilot cannot automatically cover four return-role trees plus eight
source nets. Fixed positions, all 50 macro replication centroids and native
devices remain invariants; full routing may fail without changing them.

## Prospective status reporting

| Check | Status before preparation |
| --- | --- |
| Two-variant native/shape/terminal controls and source-pack ledger | not run |
| New variant stock DRC / strict LVS, full-bank routing and stock checks | not run |
| Single-star cut test on a routed bank; upper-metal ring separation | not run |
| PEX, matching, finite return impedance, startup and analog qualification | not run |
| Source/model/PDK modifications | not applicable; prohibited |
| Simulation seed | not applicable |

Any failed control is retained under its unique run ID. No reroute or extra
stock test is implied by a passed preparation gate.
