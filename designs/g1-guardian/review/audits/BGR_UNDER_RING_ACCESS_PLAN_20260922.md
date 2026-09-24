# BGR under-ring access and isolation plan — not routed

This is a source-preserving implementation plan for the ring-aware 420 × 354 µm BGR envelope, not a stock-fit claim. Exact source53513ab4, all1,036 native units, 50 replicated-group centroids and the existing2 µm MOS/HBT reservations remain fixed. The separately reviewed586ffb58 two-device HV-length derivative requires an explicit source/footprint refresh before use; it is not substituted here.

The [native/ring screen](fit-ring-net-screen-20260922-r3.json) proves the instantiated BGR units contain no Metal5, TopMetal1/2 or TopVia1/2. That alone does not qualify placement beneath the VDD/VSS ring. The required new contacts, lower-metal routing, supply stacks, global fill and coupling have **not run**.

## Reuse source-derived contact recipes

The original [BGR generator](../../blocks/g1_bgr/layout/g1_bgr_layout.py) has SHA-256 `dee7f8fa5ab94165946e342625ed72c00e6a174592bb47a0af9f9054b8ce171e`. Its established recipes are the starting point, with unchanged PDK cells/decks and no extracted-to-golden parameter tuning.

| Structure | Existing recipe and proposed treatment | Remaining gate |
|---|---|---|
| MOS gate access | Extend GatPoly from y−0.18 to y−1.0; one0.16 µm contact at y−0.70;0.3×0.5 µm M1 landing. Reapply relative to the exact native Activ origin, not bbox origin. | Exact polygons, electrical gate contact and neighboring-layer spacing. |
| MOS source/drain escape | M1 extension reaches0.35 µm outside Activ; Via1/2 cuts0.19 µm on0.42 µm pitch with0.055 µm enclosure. Keep native Activ unchanged so per-unit junction area/perimeter are not fitted. | Via landing, other-net clearance and redundancy/current allocation. |
| Cascode PMOS well/source tie | Preserve an independent well per source/body net. Existing L4 recipe extends NWell/TGO to y+w+2.4; n+ tie is y+w+1.2…w+1.6 and connects by M1 to the source. The1.78 µm extension beyond native bbox fits inside the2 µm reservation arithmetically. | Exact NWell/TGO rules, contact enclosure, and no merge across d1/d2/d3/d5 or VDD body domains. |
| VDD mirror PMOS well tie | Original shared mirror well reaches2.88 µm beyond its native bbox and **does not fit** the2 µm reservation if copied unchanged. Proposed first isolated prototype uses source-derived per-unit well/tie treatment with bulk/source stillVDD; common VDD wells may be merged only after legal geometry checks. | This is a new well-layout choice, not a qualified inherited shape. Small-L PMOS tap dimensions need their own legal contact check. |
| HBT substrate contacts | Original contact rows/columns and0.26 µm M1 ring lie inside each6.7×7.11 µm native bbox; retain the collector/base/emitter-specific access recipe. Keep exactlynine existing dummyHBTs, not unreferenced extra active devices. | Native pin identity, isolated emitter nodes, legal ties and contacts; no accidental short of dvbe/vd2 emitters toVSS. |
| Outer HBT/resistor guards | Retain p+ substrate rings,0.30 µm Activ and existing contact/M1 construction, with multiple low-resistance M2/M3 return connections. | Guard geometry, well/substrate separation, actual return impedance and cross-net checks. |

HBT source mapping is not interchangeable: XQ56 emitterVSS; XQ67 baseb1b/emitterVSS; the eight Q2 originals have emitterdvbe; XQ75 emittervd2; XQ62 emitterVSS; XQ60/Qref emitterVSS. Substrate guards areVSS regardless of these emitter nets. Each PMOS well must retain the exact fourth-terminal net. No blanket well merging or body reassignment is permitted.

## Lower-metal routing proposal

Keep M1 for native pin extensions/taps, M2 for local vertical escapes and M3 for horizontal row collection. The native HBT grid has4 µm gaps between bboxes. Reading the exact packed source shows at mostfive non-VSS nets in any HBT row; five0.3 µm signal tracks at0.6 µm pitch occupy2.7 µm. An additional0.8 µm VSS return plus0.3 µm separation gives3.8 µm, before actual landing/turn geometry. This is a tight routing reservation, **not a legal-route proof**. Rows7/11 are the maximum-five-net cases; mirrored rows retain their source symmetry.

Use the approximately12 µm gap between the HBT bank and MOS banks for common vertical signal/return collection. If legal escapes cannot fit, M4 is a possible separately reviewed lower-metal routing layer; do not silently shrink native spacing or source geometry. New M4 use changes extraction and coupling requirements. Preserve the R1 ground-to-HBT-emitter star connection; do not route precision emitter return through a long thin substrate-guard ring merely because it is the same net.

Reserve separate M3 supply/return bars and distributed M2/M3 taps, not one long0.26 µm M1 guard carrying the entire macro return. The proposed north access band is localy352–354, beyond all unchanged native-plus-margin boxes (max351.24). The existing outer ring occupies top metals above part of this region; new stacks must connect to the **VDDA grid**, not merely to the nearest ring conductor, which isVDD orVSS. Exact native/guard clearance of that access band is not yet demonstrated.

## Feed placement and current ownership

Propose two independently landed interior VDDA accesses and at leasttwo VSS accesses, with the known legal stacked-via recipe as a starting point. Interior access locations must be selected from actual proposed VDDA/VSS stripe polygons and physical net IDs. Do not place TopVia2 at an accidental VDDA/foreign-ring crossing. The local420×354 geometry, IO ring expansion and chip PDN must share one frozen coordinate manifest before any feed is drawn.

Root's nominal BGR source current is about317.6 µA; this is a nominal simulated macro total, not an access partition or worst-case current bound. Even if the total is below the0.4 mA single Via1–4 stock limit at the documented105°C/11-year condition, it exceeds the separate50%-target0.2 mA assumption if all current is assigned to one cut. Parallel cuts do not prove equal sharing. Record worst-allocation and equal-sharing diagnostics separately; actual per-cut extraction, transient/RMS/PVT current and hot applicability remain **not run**. No125°C or pulse/EM qualification follows from this plan.

## Required isolated implementation gate

1. Build a source-bound native/contact/well/guard prototype in a separate candidate only after approval; retain all originals and exact per-unit parameters. Audit every generated contact, well domain, native polygon and device count against the source, with no extra dummy devices.
2. Demonstrate local pin-to-escape connectivity and no shorts, legal spacing and complete via landings. Run unchanged stock checks; do not turn a warning or bbox containment into a pass.
3. Draw and audit the actual lower-metal routes and VDDA/VSS stacks against the frozen expanded-ring geometry. Account for every conductor/cut and one-cut-open connectivity where applicable; keep current-share unknowns explicit.
4. Freeze the combined geometry, including deliberate no-fill regions and legal new/global fill. Do not blindly scale the original all-metal no-fill masks across the whole enlarged macro and assume density will pass.
5. Run complete unchanged stock DRC/LVS/antenna/density and affected extraction/coupling/current checks. The broad MC/adoption hold remains until the owner-directed geometry gate is genuinely satisfied.

No prototype contacts, wells, guards, new feeds, routing, GDS or broad extraction have been generated by this plan.
