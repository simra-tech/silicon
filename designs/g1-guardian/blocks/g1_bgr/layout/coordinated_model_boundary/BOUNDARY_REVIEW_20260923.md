# BGR compact-model / native-metal terminal boundary

The existing native-M1 metallic diagnostic has a concrete geometric interface
discrepancy: all **301 HBT emitter injections lie on M1 below the published
native M2 emitter pin**. An independent saved-GDS audit found all 301 unchanged
native HBTs, eight native Via1 cuts per emitter (2408 total), and the same x/y
inside each M2 pin. A separate published-pin diagnostic is therefore justified.
This does **not** prove that subtracting any part of VBIC `re` is valid.

## Pinned model evidence

Runtime PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, KLayout 0.30.9,
native GDS `6d86b9d40333958cb8186d486d29db1532a816e302871e11d07e0f1d999cfc04`,
canonical source `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b`.
The reproducible `audit_boundary.py` saves exact installed-file hashes and
line-numbered excerpts, plus source-bound geometry for all 700 HBT/R devices.

- `sg13g2_hbt_mod.lib` selects VBIC level 9. At Nx=1 and typical scale factor 1,
  the card contains `re=28.52 ohm`, `rcx=52 ohm`, and `rci=51.6 ohm`. These are
  compact-model emitter, external-collector and internal-collector parameters,
  not extracted resistances of our drawn routing; the collector terminology
  follows the [ngspice VBIC parameter definitions](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf).
  The card names the measured
  device/conditions, but the inspected text does not identify a calibrated
  geometric cut surface within the native metal/via stack.
- `npn13G2_code.py` declares C/B pins on M1 and E on M2. Its native geometry
  includes the eight Via1 cuts, emitter M1 electrode and M2 plate. The old
  `prepare_metal_r_network.py` explicitly changed E probes from M2 to M1.
- The actual `rhigh` and `rppd` wrappers set `c1=c2=1`, `rc=rz`, `postsim=0`.
  The R3CMC implementation has separate n1→i1 and n2→i2 end-resistance branches;
  at nominal temperature each is `(rc+rcw/w)/c`. For our source dimensions,
  the wrapper gives 160 ohm/end for 0.5 um rhigh and 35 ohm/end for 1 um rppd.
  Native M1 pin regions equal the complete two native head rectangles in all
  399 resistors; all 798 existing injection points are their exact centers.
- The `postsim` expression also subtracts `4.5e-6/w` when enabled and changes
  capacitance area/perimeter terms. It is **not enabled**, not a safe M1-sheet
  correction, and not authorization to alter the card. Generic Cont R was
  never added to the metallic diagnostic.

The public process documentation independently calls the 35/80 ohm-um terms
metal-to-body resistance, but does not establish the lateral M1 de-embedding
boundary used here. The installed pinned model/geometry evidence is the basis
for this review; the current online document is corroboration, not a PDK repin.
[IHP process-control parameters](https://ihp-open-pdk-docs.readthedocs.io/en/latest/process_specs/02_process_control_params.html).

## Isolated geometric controls, not fitted-model partitions

Unchanged native geometry was solved using the same native positive-metal
engine and separate resistance tables. A 1 A mathematical stimulus measures
linear equivalent resistance; it is not a physical current-capacity test.

| Native-only coupon | KPEX table (ohm) | LEF table (ohm) |
| --- | ---: | ---: |
| HBT same-x/y M1-to-M2 attachment | 1.15490358 | 2.53640188 |
| Eight ideal parallel Via1 cuts alone | 1.125 | 2.5 |
| rppd head center to 0.300 um lateral point | 0.110 | 0.135 |
| rhigh head center to 0.225 um lateral point | 0.0951923 | 0.116827 |

The rhigh point stops 5 nm inside its native head; it is not falsely extended
to the external via center. These coupons are not the resistance of an
assembled multi-terminal network and cannot be subtracted from a whole net.
Small head resistance relative to `rc` does not prove disjoint ownership or
justify excluding the whole native head. Nor does positive added R prove
absence of double counting: a fitted terminal resistance can already absorb
an unknown part of electrode spreading. A scalar terminal fit alone cannot
uniquely assign that part to a geometric segment.

## Actionable partition and limits

Use the published M2 emitter pin as a **separate conditional interface**:
move only the 301 E point layer tags, keep x/y, every physical polygon/cut,
all 1036 primitive records, all resistor attachment points and every model
parameter. Re-extract with all positive edges retained and require exact
source reconstruction plus zero-R parity before nominal OP. The prospective
[contract](EXTERNAL_PIN_CONTRACT_20260923.md) freezes those gates.

Do not post-process the old mesh by deleting edges whose endpoint happens to
lie inside a native bounding box. Endpoint coordinates are not a proved
support polygon for a square-counting element. A future routing-only
device-owned-mask partition would need explicit conductor-cut surfaces,
multi-contact terminal treatment, no shared-route removal, and authoritative
model-plane applicability. It is not established by this investigation.

| Check | Status |
| --- | --- |
| All 301 HBT / 399 resistor source-to-native geometry bindings | Passed |
| 301 emitter plane discrepancies and 798 resistor pin centers | Passed |
| Six isolated positive-metal coupon solves | Passed |
| Native/model/source mutation | Not applicable; read-only investigation |
| Exact calibrated rc/re geometric ownership | Failed to establish |
| Safe numeric subtraction from rc/re or whole-net R | Not run; not justified |
| Complete substrate/contact/de-embedding qualification | Not run |

Audit r1 failed on the KLayout instance-iteration API before geometry results;
its receipt/snapshot remain. Corrected read-only r2 passed in 0.325 s. This
failure is not erased by the later result. No new physical or electrical
qualification is claimed by the review.
