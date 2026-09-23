# First feeder field pilot — prospective scope freeze

**Not run.** Exactly one site is proposed for review: the middle of
XOTA/XM14's widened VDD feeder, with its neighboring source-proven pc1
drain metal. No other feeder/site or whole-strip extraction is included.

The completed native inventory passed in 16.309 wrapper seconds. Its exact
SHA256 is `338d0eef0acd33ccc13a13b451de4b87eca567bacd26e23fb23b2b4184c4c8ef`.
All four changed M2 regions (2,931.424 um²) and all 32 Via1 cuts were accounted
against original r8 `8060e30a...` and candidate `4b8a82d4...`; both source
graphs retained 134 nets. The complete proposed local-window union still
leaves 2,152.588 um² of changed M2 uncovered, so even completing all those
windows would not prove full-route coverage. Only the site below is proposed.

## Exact geometry and source boundary

| Item | Frozen value |
|---|---|
| P source net | `vdd`, all clipped ordinary-metal pieces independently proven on this full native net |
| N source net | `XOTA/pc1`, all clipped ordinary-metal pieces independently proven on this full native net |
| P anchor | M2 `(122.79, 49.03)` um, present in both original and candidate |
| Longitudinal interval | x `112.79 .. 132.79` um, fixed 20 um |
| 24 um context | y `37.03 .. 61.03` um |
| 48 um context | y `25.03 .. 73.03` um |
| Source | `baab6183c364477da1dd332e4585ae7201b3776bf0f836014744a42809e13877` |

The smaller window contains ordinary-metal nets vdd, vss, pc1, mir and
vbpc. The larger also contains fn, out1, pc2 and iptat; internal names carry
the `XOTA/` prefix except the global supply/bias. Unique physical-component
labels must be retained. Multiple P or N pieces are grouped only through
an explicit ideal outside-clip diagnostic boundary, not a claimed physical
short or finite-R model attachment. Every other drawing net is grounded
for this diagnostic. The raw complete capacitor graph and source-net
membership table remain available; no foreign component is silently dropped.

Actual native floating fill must be enumerated at preparation. This first
four-extraction scope requires zero datatype22 fill in both windows; if fill
is present, stop for a new explicit variant/count contract. The same applies
to any native MIM/Vmim primitive in the windows. The completed inventory
reports no MIM/Vmim there, but clip preparation must independently assert it.
The pilot does not stand in for final fullchip fill/context.

## Exact checks and resource limits

After a fresh resource gate and explicit CPU lease, prepare four clips:
baseline/candidate at 24/48 um context. Require full-net target membership,
unique local-component labels, every included layer's exact saved clip XOR,
and independent extracted-label/component accounting. First review the
prepared clip identities before extraction. No device or PDK deck is edited.

Then, only if separately authorized, run four stock ordinary-metal KPEX
CC extractions, at most 120 s per child and 128 MiB total pilot growth.
Missing output, non-finite terms, disconnected/missing target or a timeout
stops the batch. No larger watchdog or automatic next site is included.

Retain the raw capacitance matrix; reduce the complete P/N group matrix
under the declared grounded-context condition. Use the existing synthetic
capacitor controls and the exact existing 1e-25 F independent AC comparison
tolerance. Drive P and N independently for each of four layouts: eight
required AC checks, at most 30 s per child. All logs must independently
reject simulator errors/fatal conditions even on exit zero. With zero fill,
the Schur internal block is empty; record zero finite residual, not an
unrun floating-fill solve.

The prospective context acceptance metrics are every entry of the reduced
2×2 P/N matrix plus P-ground, N-ground, mutual, differential-energy and
common-mode-energy capacitance. Apply the existing **1% criterion** separately
to baseline and candidate 24→48 context changes. The existing zero-denominator
failure rule remains unchanged. Do not assess only a favorable candidate
minus baseline quantity. Preserve all signed deltas and all failed metrics.
Individual raw couplings to newly entering context nets are retained but
are not represented as independently converged full-net couplings.

## What this cannot qualify

Native Poly, Active, Cont and NWell are present. The inventory's
`projected_overlap_changed_M2_dbu2` fields deliberately report a **full-feed**
projection for each adjacent source group or material, not window-clipped
area; `clipped_area_dbu2` is the separate local-window quantity. Full-feed
new-M2 projection over native Poly is 827.494 um² across four feeders and
over Active is 934.0956 um². These are geometric projections, not field or
compact-model ownership results.

Thus an ordinary-metal-only P/N result omits potentially affected device
electrodes and cannot qualify all extrinsic feeder effects. No resulting
delta capacitor will be inserted into the canonical circuit. Complete
primitive/routing ownership, distributed gate/body reference planes,
complete MIM field handling, source-preserving finite-R composition and
exact zero-R/electrical parity remain open. The first pilot can establish
only a bounded local ordinary-metal coupling change and its context
sensitivity under explicit diagnostic boundaries.
