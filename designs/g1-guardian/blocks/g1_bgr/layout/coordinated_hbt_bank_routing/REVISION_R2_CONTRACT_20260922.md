# R2: source-port escape relocation and nine dummy-base probes only

R1 remains failed: the VBE3 M3 port escape centered at y=140.8 µm overlaps
the first-row VD2 M3 collector centered at 141.05 µm by 0.05 µm. Nine dummy
base observations were also absent because the functional contact's extension
point `(origin X+0.6, origin Y−1.5)` is outside the unchanged dummy contact.
That observation failure is separate from a proven physical device open.

R1 source/native/serialized/grid/bounds and all known 336-MOS / routed399-R
obstacle checks passed. Full source graph and star-cut graphs failed; the
dependent local role-spacing / enclosure audit was not run. No stock check
or analog run occurred. R1 evidence and source snapshots remain unchanged.

Exactly two textual substitutions in the frozen r1 builder are permitted:

1. Seven source-port centers become `136 + 0.6*i` rather than `136 + 1.2*i`
   µm for the same ordered seven signals. The first remains unchanged; the
   other six source-port escapes, Via2 landings/cuts, minimum lower source-trunk
   extents, pin rectangles and text positions move correspondingly. The new
   range 136–139.6 µm keeps 0.30 µm M3 edge gaps and clears the first-row
   collector at 141.05 µm. No row collector or functional-return tree changes.
2. For only the nine all-ground dummies, observe B at native coordinate
   `(0,−1.14)` µm instead. The unchanged native base M1 rectangle is
   `(-0.975,-1.260)-(0.975,-1.020)` µm; the new seed is inside both that native
   base conductor and the existing contact. Functional probes are unchanged.

Freeze and execute the read-only native seed proof. No native/contact geometry,
source line, fixed position, star interface, dummy/general tie or model changes.
Re-run every saved-GDS terminal graph, five individual star cuts/all-star cut,
ownership/enclosure/spacing, grid/bounds and complete known-neighbor gate.

Require the source CDL byte-identical to r1; exactly 24 removed/24 added route
records, 12 removed/12 added Via2 cut records, and exactly the nine dummy-B plus
six source-port probe-coordinate changes. Serialized GDS XOR may change only
M2, Via2, M3 and M3-pin geometry inside x=190.4..200.8, y=135.8..143.5 µm;
the only text changes are the six source-port positions. Other source, native,
terminal and routing geometry remains identical. These are prospective gates,
not a claim of success.

One new CPU0 / 180 s / 4 GiB reservation / 0.20 GiB HOME preparation after a
fresh resource gate. No automatic retry, stock DRC/LVS or analog launch.
