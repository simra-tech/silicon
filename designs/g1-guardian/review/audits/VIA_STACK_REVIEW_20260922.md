# Actual via/stack inventory and redundancy plan

The SENSE route candidate remains unpromoted and unchanged, SHA-256 `af9ac30034c8c11e09d1f24f732f3476c5653fb95eaa0b67f214c2e14c56f76d`. This review inventories actual geometry, identifies scoped one-cut-open behavior, and prepares a prioritized design plan. It does not establish electromigration/current-margin compliance or authorize release. Tools: pinned KLayout Python 0.30.9, PDK `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; one allocated CPU per geometry job.

## Actual top-level geometry

The [raw inventory](route-via-inventory-20260922-r2.json) resolves all 1,878 selected DEF-assigned via records against actual candidate GDS instances and cuts. All sampled wire centerlines and three transverse samples per routed segment are covered. It replaces obsolete DEF SENSE routes with the exact candidate manifest. This is not exhaustive minimum-neck extraction.

The [deduplicated analysis](route-via-inventory-analysis-20260922-r3.json) has 1,828 unique cut-bbox groups. It removes 174 repeated cut-group records, including coincident LS stacks and repeated grid definitions. Repeated instances at identical coordinates do not provide additional physical cuts or parallel capacity. Counts are conductor-pair/array groups, not a guarantee that every group has uniform current.

| Scope | Actual transition inventory | Disposition |
|---|---|---|
| SENSE P/N | Four Via3 transitions, four cuts each | Existing candidate evidence credited; no duplicate redesign |
| Selected critical signals | 31 single-cut transitions | Local two-cut placement screening completed; no candidate yet |
| Macro-feed stacks | Generally five Via3, five Via4, two TopVia1 cuts per stack; lower levels recorded where present | Already multi-cut; do not describe as single-cut feeds |
| TopVia2 grid | 286 unique single-cut transitions: VDD 143, VDDA 62, VSS 81 | Alternate-path screening below; original raw count 364 included duplicates |

Signal singles are gate_o 2, cmp_clk 4, IPTAT 4, ISENSE 2, pbias 4, pcasc 4, VREF 9, and VREF_BUF 2. VREF uses Metal2/3 and Via2 at these transitions; VREF_BUF/clock/ISENSE use the recorded Metal3/4 geometry. `gate_o` is the internal low-current control feeding pad `c2p`, not the external high-current GATE conductor.

The first route inventory timed out after 600 seconds due to repeated full-chip region operations. Its source and [not-run record](route-via-inventory-20260922-r1-run.json) are retained. The completed revision uses spatial queries and also requires complete cut-array bounding-box landing coverage before claiming a local remaining bridge.

## Pad and macro interiors

The [pad inventory](pad-internal-via-inventory-20260922-r2.json) covers `IOPadOut30mA`, `IOPadIOVdd`, `IOPadIOVss`, and `IOPadAnalog`: 1,362 lower/upper plate-pair groups, 43 single-cut groups, zero unassigned cuts. Top-cell port labels only associate already physically connected conductors; labels never merge nets. Recursive child labels, their local aliases and off-metal observations are retained separately. Every selected top-cell port label lands on metal.

On the output pad's actual PAD net, native device-contact branches have 13/19 cuts (larger protection branches also exist), Via1 branches have at least 22, and the upper common stages have 858 Via2, 70 Via3, 70 Via4, 35 TopVia1, and 35 TopVia2 cuts. These are not equally loaded arrays or a current-margin result. Eight single Via1 groups remain on the IOVSS network and small input/control contacts remain; they must not be mislabeled as a single-cut external PAD output stack. Stock PDK cells were not modified.

The [six-macro inventory](macro-internal-via-inventory-20260922-r1.json) contains 12,206 plate-pair groups and 9,243 single-*shape* groups. Native non-square/bar geometry is explicitly separated: 1,874 noncanonical cut shapes cannot be assigned a standard square-cut limit merely by counting shapes. Twenty-eight contacts remain unassigned by the simple diffusion-minus-gate/poly classifier (22 BGR, six T2F), with their exact coordinates retained. This is a classifier limitation, not a claimed DRC defect or an omitted pass.

| Macro | Plate-pair groups | Single-shape groups | Unassigned contacts |
|---|---:|---:|---:|
| SENSE | 2,520 | 1,934 | 0 |
| BGR | 494 | 350 | 22 |
| GATE | 572 | 449 | 0 |
| TRIP | 7,690 | 5,814 | 0 |
| OSC | 455 | 372 | 0 |
| T2F | 475 | 324 | 6 |

No per-device current distribution or internal-current margin is inferred from these counts. A large macro total must not be assigned to every local device contact as though it were the actual current there.

## Current evidence and conditions

The pinned [current-limit record](current_limits_20260922.json) applies to 11 years at 105 °C only. Contact/Via1–4/TopVia1/TopVia2 limits are 0.3/0.4/1.4/10 mA per standard cut. The engineering 50% utilization target is not a foundry derating rule. There is no inferred 125 °C lifetime rule, pulse duty-cycle relaxation, uniform sharing, or continuous-peak bound.

The analysis binds all 36 recorded macro accesses to actual transition coordinates. Eleven accesses have matching macro/rail entries in the [nominal integrated current envelopes](current-envelopes-20260922-r1/summary.json). It records mean, RMS and sampled peak independently. Applying the entire observed macro current to one access is explicitly a diagnostic allocation—not extracted access current or a proven bound. Worst-single-cut allocation, conditional equal sharing, and conditional sharing with one cut lost are separate fields. Source hashes and waveform scope are retained. Real access partition, shared-return currents, operating extremes and applicable hot/lifetime margin remain **not run**.

## Prioritized geometry plan

1. Critical signals: preserve the existing cut and add one standard 0.19 µm cut at 0.41 µm pitch, with an enclosed landing rectangle. The [four-direction local screen](signal-via-redundancy-screen-20260922-r1.json) finds an option at 30/31 sites using 0.05 µm enclosure, 0.21 µm distinct-metal clearance and 0.22 µm cut clearance. Provisional options add 5.6264 µm² metal in aggregate and intersect no sampled 0.30 µm fill keepout. These are individual conservative local checks, not combined-patch stock DRC. Prioritize clock, VREF, IPTAT and gate_o; evaluate added capacitance/current access with the circuit owners before promotion.
2. The constrained VREF Via2 at (644.16, 774.48) µm is blocked by widening its existing Metal3 south edge to symmetric 0.05 µm enclosure. A [separate asymmetric option](vref-via-asymmetric-screen-20260922-r1.json) passes the local screen: retain 0.05 µm elsewhere, use 0.01 µm on that Metal3 south edge, and add the cut in +x. The south enclosure is twice stock Vn.c's 0.005 µm minimum, leaving a 0.215 µm neighbor gap above Mn.b's 0.21 µm minimum. This is an explicit geometry tradeoff, not a rule waiver. Stock checks and simultaneous-option interactions are **not run**.
3. TopVia2 grid: the [actual upper-metal graph](topvia-single-open-screen-20260922-r1.json) finds explicit alternate paths after one-cut removal at 278/286 sites. Eight lack an upper-only alternate path. The [all-seven-metal/source-access probe](fullmetal-topvia-open-probe-20260922-r2.json) recovers alternate paths at the two VSS sites. Of six remaining metal disconnects, two isolate recorded T2F feeds: VDD (630,909.46) and VDDA (568.02,948.36) µm. The other four leave every recorded macro access source-connected; that does not establish that the detached metal is unused by every digital/internal load. The inventory also retains one perimeter-shaped nonstandard TopVia2 polygon rather than treating it as an ordinary standard cut. Preserve the many already redundant mesh crossings unless current redistribution or another requirement justifies changes.
4. Internal macro and stock-pad singles: retain pending device/branch current assignment and canonical/bar-contact interpretation. Do not blindly duplicate thousands of contacts or alter stock PDK cells. Record each unresolved current/geometry class and prioritize proven current or functional-open bottlenecks.

Any accepted combined candidate must preserve the current SENSE remedy, pass whole-layout change accounting, actual connectivity, stock hard/recommended DRC, antenna/density, and affected LVS, then receive scoped R/C and coupling checks. Full IO-inclusive LVS remains independently failed. No new via geometry has been adopted and broad affected PEX/freeze remains gated.

## Isolated priority candidate, checks pending

The approved first stage is 19 clock/VREF/IPTAT/gate_o transitions plus the two proven T2F feed-open sites. The other 12 signal singles are deferred, not waived. The [T2F landing screen](t2f-feed-topvia-pair-screen-20260922-r1.json) retains each 0.9 µm cut and adds one at +1.96 µm x pitch. A 2.2 µm-wide landing gives 0.65 µm enclosure; conservative local clearance is 2 µm on TopMetal1 and 3 µm on TopMetal2. Both chosen options add 4.312 µm² TopMetal1 and no TopMetal2 area, with no local fill intersection. Current capacity is not the justification: the actual load partition is unknown, and functional single-open isolation was demonstrated directly.

`prepare_priority_via_candidate.py` generated isolated scratch candidate SHA-256 `04fb6443010bed31595974cca636a9dbd292fda47f0cd45507688f05b1c9a7d8` from the unchanged SENSE candidate. Every non-text layer matches exactly the original plus the listed additions; zero geometry or fill was removed. Added drawing area is M2 1.2789, M3 1.27515, M4 1.122 and TopMetal1 8.624 µm², plus nine Via2, ten Via3 and two TopVia2 cuts. Each original/added cut pair is fully covered by both common landing rectangles. The candidate is unpromoted.

| Exact priority21 candidate check | Status | Evidence |
|---|---|---|
| Stock hard/recommended DRC | passed, zero markers, 366.41 s | [summary](priority-via-stock-drc-20260922-r1/summary.json) |
| Stock antenna | passed, zero markers, 110.49 s | [summary](priority-via-stock-antenna-20260922-r1/summary.json) |
| Stock density | passed, zero markers, 40.64 s | [summary](priority-via-stock-density-20260922-r1/summary.json) |
| Core-only stock LVS | passed explicit strict-port comparison, 251.88 s | [summary](priority-via-core-lvs-20260922-r1/summary.json) |
| Combined actual-metal connectivity and scoped cut-open cases | passed, 2,619 probes, no missing probes | [four-view check](priority-via-connectivity-20260922-r2.json) |
| IO-inclusive LVS on this new candidate | not run; prior independent full-IO failure remains unresolved | no inherited IO acceptance |
| Affected electrical R/C/current-margin qualification | not run | no promotion or freeze claim |

The independent core reference remains SHA-256 `70f0a6b1a107a9252fac29d55c9af8b128fff0f4c71e657e882229a639674ea5`, identical to the earlier passing reference. No extraction-to-golden copying or reference fitting occurred.

The connectivity check compares actual parent/candidate net partitions and every hierarchical circuit's net count, then separately removes all 21 original cuts and all 21 added cuts in memory. Every view preserves all 2,619 selected route/source/access probe partitions and net counts. Labels and device conduction do not merge nets. The first checker left unused raw cut layers registered after constructing boolean-removal layers, inflating orphan-net counts; its failed aggregate is retained. The corrected version uses the same flattened-cut representation in every in-memory view and requires exact cut-region XOR after transformation. No test view was saved over a GDS.

The [coupling coverage inventory](priority-via-clip-coverage-20260922-r1.json) shows a clock interval clip with 24 µm context and 20 µm endpoint margin includes only three changed stages: clock at (734.4,630.42)/(734.4,601.02), and VREF at (732,612.36) µm. Even the union of all four proposed interface windows covers only five of 21 stages; the other 16 are explicitly listed. Prior wide-IPTAT timeout and full-matrix context-convergence failure remain unchanged; no automatic wider retry or watchdog escalation is authorized.

The [bounded paired clock-window extraction](priority-via-clock-delta-20260922-r1/summary.json) completed both parent/candidate fill variants and all 16 capacitor-graph AC checks. Before clipping, seven-metal physical connectivity proves each ISENSE/clock target midpoint matches every recorded route-via anchor, without text joining. Parent matrix values exactly reproduce the corresponding earlier delivered-GDS window. With actual floating fill, parent→candidate mutual capacitance is 5.23383049→5.28634526 fF (+0.05251477 fF, about 1.003%). ISENSE ground-equivalent capacitance changes by −0.00190913 fF; clock ground-equivalent capacitance changes by +0.09248650 fF. Output growth was 8.94 MB; existing 120-second extraction/KPEX child limits were unchanged.

This is a paired local delta for three changed stages, not convergence, complete RC or an electrical pass. The other 18 changed stages' R/C effects and the new candidate's dynamic circuit effect remain **not run**. The earlier delivered-source clock decision-error result cannot be inherited automatically by this changed candidate.
