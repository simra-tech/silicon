# BGR native power-interface candidate

This isolated additive candidate preserves final BGR `6d86b9d4` native geometry,
source devices, models, and all port annotations. It is not adopted. The frozen
screen context is actual decap-PDN r4 GDS SHA256
`88e5911aeaa4f0ae9c3c4712f4f2430563affa32bae0fe6c6c48c142e9611bdb`,
whose parent core is `a001df1aec9d38d18bbf9649b0944f977eb40cb04a5a23f2f49be4f79d2476c5`.
The parent connectivity passed; the new r4 stock DRC is not yet run at contract
freeze. Earlier r2 stock passes do not qualify the two changed r4 feeders.

## Exact interfaces

Coordinates are chip micrometres, identity transform, 1 nm database unit.

| Net | Native access | New conductor | Reserved handoff |
|---|---|---|---|
| VDDA | M5 `(743.4,878)` | 2×2 TopVia1, 1×2 Y-oriented TopVia2; TM2 width 2.2 | TM2 `(743.4,922)` |
| VSS | M5 `(749.65,873)` | M5 width 1.10 via `(749.65,875.975)` and `(736.8,875.975)`; 2×2 TopVia1 | Existing TM1 VSS spine `(736.8,873)` |

The VDDA handoff is unpowered until separately routed to pad07. It must not
join core VDD or the existing SENSE-only VDDA feeder. No root spine is moved.
In particular, placing the VDDA pod at x750 would short the core VDD spine;
that option is rejected. The VSS route bypasses the final thin M3 port neck
using proven native M5 ground metal, without changing the logical pin.

## Prospective gates

- Pin/egress points must bind to the actual native source net, not a text name.
- Exact r4 drawing geometry and cuts are screened, not just ideal spine axes.
- Foreign metal overlap, conservative proximity, old foreign-cut capture and
  new-cut enclosure/spacing screens must all pass before GDS is written.
- Saved candidate equals parent polygons plus declared overlay, and all native
  texts remain exact. Root VDD, root VSS and BGR VDDA remain distinct.
- Stock overlay and native-neighbor checks, single-cut-loss connectivity and
  actual signal-route context remain separate required checks.

## Current scope

The declared branch target is 1 mA exploratory, not a PVT bound. The source-held
standalone nominal BGR observation is 319.692370 µA at 27°C and 3.3 V with IPTAT
held at 1 V. The lower current from a conditional metallic-IR solve is not used
as capacity relief. A qualified worst-case branch envelope is not run.

The public PDK limits apply at 105°C for 11 years. The 50% engineering target
is not a foundry derating. Four TopVia1 cuts yield 2.8 mA at that target under
equal sharing, or 2.1 mA with one cut unavailable; two TopVia2 cuts yield 10 mA
or 5 mA respectively. The 1.10 µm M5 bridge yields 1.10 mA. Actual distribution,
internal BGR necks, full-wire IR, pulse lifetime, 125°C applicability and shared
VDDA aggregate capacity are not qualified by these arithmetic checks.

All failures are retained. No deck/model edits, full-field PEX, electrical
adoption, or canonical assembly changes are authorized by this candidate.

## Preserved first-screen failure

The r1 straight VSS M5 bridge at y873 failed the native screen before GDS
write: 1.506 µm² foreign M5 overlap and four existing Via4 contacts. Revision
r2 proposes the y875 dogleg above. Its native same-net allowance is traced
through actual BGR metal/via components on every layer; a same-layer bbox
alone is not used to label pre-existing vias. The r1 script and failure remain
immutable in its run directory. Revision r2 also failed before GDS write:
0.357 µm² foreign M5 overlap and two foreign Via4 contacts near y874.8.
Revision r3 narrows the bridge to 1.10 µm and moves its horizontal center to
y875.975, leaving nominal gaps of 0.475 µm to the nearby foreign metal and
native VDDA row. It retains the 1 mA exploratory target and reserved handoffs;
this is an explicit geometry change, not a spacing-rule waiver.
