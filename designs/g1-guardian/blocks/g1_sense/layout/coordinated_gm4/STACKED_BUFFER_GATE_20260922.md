# Proposed next isolated geometry gate: stacked pair and routed buffer

Preparation only. This does not authorize a full gm4 OTA/SENSE macro, PEX or adoption. Preserve the completed native/control GDS `dfef42cc...`, all original fidelity failures and the ten stock-written per-node A/P failures. Keep the qualified source `baab6183...` and all card/deck/default parameters unchanged.

## Stacked main pair within230µm

Use two exact native pmosHV W384µm/L2µm/ng64 arrays. Their native boxes remain the r4 rectangles x38.07–191.93µm, y8.38–15.62 and102.88–110.12µm; Activ origins are(38.69,9) and(38.69,103.5). Apply complementary ABBA/BAAB drain-pair groups: each chain contains32 gates from each logical input, giving64 gates/W384µm per logical input. Both gate centroids should be exactly(115,59.25)µm. Physical source strips are counted once, with adjacent-gate allocation reported separately from intrinsic/per-device applicability.

Replace the wide prototype's outer shared well with independent local row wells and native-contact body strips. Proposed local NWell is xActiv−.62 through xActivEnd+.62, yActiv−2.25 through yActiv+8.25. Contacted n+ body strips centered at yActiv−1.8 and yActiv+7.8 tie to VDD. Proposed p+ substrate ring inner box is xActiv−1.45 through xActivEnd+1.45, yActiv−3.05 through yActiv+9.05, using the existing .30µm tap-ring helper. This consumes a small part of the free gap outside the old2µm rectangle reservation; it must be screened against every other actual r4 native polygon and stock spacing, not declared free by assumption. The resulting pair-row outer limits remain inside the main230×164µm rectangle.

Gate-A/B Metal2 rails remain at yActiv−.33 and yActiv+6.33; drain-A/B Metal1 rails at yActiv−1.03 and yActiv+7.03, with Metal2 exits. Source strip contacts reach a Metal3 tail collector at yActiv+8.4. Join the two rows through separate .40µm Metal3 trunks: left x2/3.2/4.4/5.6µm for inn/inp/fn/fp; right x224/225.2/226.4µm for tail/VDD/VSS. Actual via landings, pin widths and neighboring-net clearances must be audited. These tracks are prototype-specific prospective assignments, not a demonstrated whole-main-OTA routing plan.

Required before stock: immutable full polygon snapshots; exact native W/L/ng and per-row diffusion A/P; no native channel delta; exact source/terminal probes including well/substrate ties; coincident logical gate centroids; all new nontext polygons inside230×164µm; explicit actual-native overlap/spacing screen against the unchanged other19 r4 device entries. Do not count a pair-only DRC pass as all-device placement or access closure. Preserve a failure if proposed guards consume a neighboring device's required clearance.

## One source-faithful routed buffer within110×65µm

Use the original OTA generator only through a hash-locked isolated derivative; baseline reproduction was already zero-XOR. Correct MB2/6 to W8/L1/ng2 and MB3/5 to W16/L1/ng4. Extend their4µm-high source rails to the unchanged8µm row bus and connect every alternating diffusion strip. Keep all other source devices, RZ1×6.2µm and CC23×23µm exact.

Replace the inherited single32-gate shared input chain with two native16-gate W96/L2 arrays,2.4µm Activ separation, one legal shared L2 dummy in that gap, and complementary ABBA/BAAB assignments. A virtual coordinate adapter may preserve the old routing helper API, but it must explicitly expose **both** source strips at the internal break; a single old strip index must not silently omit either contact. Corrected row width is79.82µm; the predicted full buffer bbox is100.61×51.2µm, below110×65. This estimate is not accepted until the actual routed geometry and guards are measured.

Audit all19 logical MOS individually against source W/L/ng and actual diffusion polygons, including all gate/source/drain physical nets, not merely total parallel W. Verify all three bias/supply net identities, RZ/CC dimensions, and the source-derived complete19MOS+R+C CDL with the original converter's ng limitation explicitly retained. The complementary pair needs the same split/control attribution scope as the completed prototypes; no stock A/P averaging is adopted as golden truth.

Place only one isolated buffer for this gate. Its future two-instance allocation can use x5–115 and125–235/y175–240 inside the existing385×240 SENSE rectangle, leaving a10µm gap; actual placement and port corridors require later proof. Do not generate the full SENSE macro automatically.

## Prospective execution and acceptance

After review, use CPU7, a fresh0.05GiB resource-growth gate, and≤50MiB phase-capped output. Geometry children stay≤60seconds. First require exact saved-GDS native/source/terminal/bbox audits, then unchanged stock hard/recommended/off-grid/angle DRC and strict stock LVS for each isolated top,≤180seconds per child. Stop on any failed or unknown geometry/stock endpoint. MatchWithWarning is not passed; missing/timed-out checks are failed or not run with explicit reason. Density/antenna, full-main routing, full-SENSE integration, mapped-parasitic extraction, dynamic/current/matching performance and whole-chip legal fit remain not run.
