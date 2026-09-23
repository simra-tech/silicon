# Source-held TRIP internal DAC access candidate

The native GDS SHA256 is
`c99f3ae11b4501610939aa09b4581535a42d257f76951a25b4c84dd72a3afb90`;
the unchanged source-derived CDL SHA256 is
`60a9ad6e3744ff0b3dcd407a78febcb49315840a65fdf8ef851032d6e88bfd76`.
This candidate changes drawing-metal/via geometry only, not native devices,
contacts, wells, labels, logical pins, source parameters or rule/model cards.
The coordinate frame is original `g1_trip`, translated(+771,+736) µm in
the assembled chip. It is separate from the external distributed-feed overlay.

The initial native-only screen failed nearby M1 spacing. Revision2 retains
that failure and uses0.26 µm source-strip additions, two Via1 and two Via2
cuts for each of64 native HV-PMOS source accesses. Sixteen bit-VDD rail
accesses receive two cuts per level. M3 collectors and M4 risers connect to
the retained native headers; top Via3 arrays preserve, rather than duplicate,
the four existing center cuts. The recipe adds464 cuts in total.

The native-only screen reads the pinned rule dictionary's0.18 µm M1 and
0.21 µm M2 minimum spacing. These are not substitutes for conditional stock
spacing/enclosure checks. Saved geometry must pass exact native-plus-recipe
polygon and text roundtrip, preserve the flat metal net count, and bind every
one of80 source probes to its intended distinct VDD/VDDA root. Construction
passed these gates. Strict source LVS subsequently passed all four circuits
and every compared child with `Match`. Stock main DRC failed45 markers:
two M3.b gaps and43 fill-spacing markers (18 M2Fil.c,3 M3Fil.c,22 M4Fil.c).
Maximal DRC was not run after that failure. The native-only clearance screen
did not inspect datatype22 floating fill and was insufficient for stock legality.
No failing geometry is approved for integration.

Revision3 shifts the wide M3 collector down0.3 µm and removes exactly125
conflicting floating-fill polygons: M2 ten polygons/10 µm², M3 forty-six/
106 µm², M4 sixty-nine/414 µm². Only affected fill arrays are split into
surviving repetitions; shared fill-cell definitions and functional/device
instances remain unchanged. The ledger records the original arrays and
removed repetition transforms. All remaining fill is exactly original minus
that selection, and all non22 geometry is original plus the declared metal.
The revised candidate passed stock main/maximal0/0 in30.705 s and strict
source LVS in25.468 s. The original45-marker failure remains preserved.

The global addition and removal overlays passed exact inverse-translation
XOR with(+771000,+736000) database units. The reusable fill-pruning helper
was replayed independently on a namespaced copy of the original hierarchy;
its remaining fill exactly matches the qualified candidate. It rejects
non-fill children, non22 geometry and ambiguous array matches. No primitive
hierarchy replacement is required for chip integration.

A subsequent actual native-plus-addition graph audit passed all464 new-cut
removals, preserving all80 M1 source-probe connections. Baseline ideal-metal
via-only half-table collector limits are1.8 mA per DAC VDD and5.0 mA per DAC
VDDA, against exploratory1/4 mA targets. These are not current-sharing,
wire/contact or lifetime qualifications. The cut-loss cases check connectivity,
not redistribution after a cut opens. Native Contact and all original via
single-open cases remain not run.

Next checks use the unchanged stock main/maximal decks and a180-second
bounded full-macro LVS comparison. Acceptance requires explicit comparison
success and every circuit/device/net/pin/subcircuit pair strictly `Match`;
`MatchWithWarning`, absent output, missing comparisons and timeouts fail.
The source CDL is copied byte-for-byte, never derived from the extraction.
Stock LVS parameter selection does not prove ignored ng/junction parameters.

The geometry assumptions are4 mA per DAC analog feed and1 mA per DAC digital
feed. They are not measured operating limits, validated current sharing or
per-device contact allocations. Comparator VDD accesses, all VSS accesses,
fullnative PDN/signal context, intrinsic/field extraction completeness,
actual distribution/IR/EM/PVT and adoption remain independent unresolved gates.
