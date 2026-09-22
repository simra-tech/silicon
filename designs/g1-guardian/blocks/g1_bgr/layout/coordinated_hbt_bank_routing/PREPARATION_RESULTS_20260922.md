# Full 301-HBT bank r2 — preparation passed

The fixed-position 301-HBT candidate passed all eleven preparation gates and
the exact r1-to-r2 change audit. This is a routed-bank preparation result, not
stock DRC/LVS, full-BGR integration or analog qualification. R1's real port
short and its separate missing dummy-base observation points remain failed
and preserved.

| Check | Result |
| --- | --- |
| Complete source / placement | passed; 301 native units, 1204 C/B/E/substrate incidences, eight source ports, nine unchanged dummies |
| Native and saved geometry | passed; exact per-layer contact copies, native nonrouting layers unchanged, saved-GDS polygon parity |
| Full physical source graph | passed; eight components, no opens or cross-net shorts, labels do not merge conductors |
| Five individual star-interface removals | passed; nine components for each removal, including the separated selected branch |
| All five star interfaces removed | passed; thirteen components: seven signals, five separate VSS branch roles and the hub |
| Route ownership / 0.055 µm via enclosure / 0.30 µm other-role spacing | passed; zero errors or spacing findings |
| Known neighbors | passed; all 336 exact MOS contacts and reservation rectangles, actual routed399-R r2; seven explicit resistor-star intersections only |
| Grid and macro bounds | passed; 166848 vertices on 5 nm grid; bbox `(0.8,11.06)-(200.65,351.69)` µm inside 420 × 354 µm macro |
| Exact revision delta | passed; 24 removed/24 added port-related route records, 12 removed/12 added Via2 cuts, nine dummy-B and six port-point changes |
| R1 real VBE3–VD2 port overlap | failed and retained; 0.05 µm physical overlap |
| R1 nine dummy-B observations | failed and retained; original probe outside contact, not a proven device open |
| R1 dependent local-spacing / enclosure audit | not run; all-cut graph had failed |
| Stock DRC / strict LVS, density, antenna, full BGR / ring assembly | not run at this preparation milestone |
| PEX, analog, matching, current, IR/noise and startup | not run |
| Simulation seed | not applicable |

R1 ran 11.538 s and produced 5435697 bytes. R2 ran 73.954 s and produced
5497021 bytes, within its CPU0 / 180 s / 0.20 GiB limit. Fresh RAM/quota/inode
and 50%-otherwise-available-CPU gates passed. All source/tool bindings remained
unchanged. Each run logged three runtime backing-store warnings; neither
reported a geometry exception. Memory was reserved, not enforced.

## Controlled remedy and finite star

R2 moves only six source-port escapes into the independently checked
136–139.6 µm strip and moves nine dummy B probes onto the unchanged native
base conductor. Native cells, source tuples, row routing and all star trees
are unchanged from r1. Source CDL is byte-identical. Serialized XOR is limited
to M2 4.647 µm², Via2 0.8664 µm², M3 12.292 µm² and M3-pin 0.9 µm² within
the port strip; only six source-port text positions change.

The 76 functional grounded emitters use four independent M4-row/M2-trunk
return trees. General substrate guards and nine dummies use a separate tree.
They meet only through the declared finite hub and the x=16 µm R1 join between
y=15.06 and 16.26 µm. Cut tests establish the generated bank's metal ownership,
not zero impedance, substrate isolation, balanced current or analog matching.
The resistor-bank overlap is intentionally confined to that interface; neither
bank result alone proves assembled-BGR stock legality.

## Frozen identities

| Artifact / input | SHA256 / identity |
| --- | --- |
| R2 GDS | `7a8c57b6a05b0cadd4443bb04a3b629b9da23b3919cf16d723122c12fae34e2c` |
| Complete source CDL | `57c27168d72461f1a0def4f0a1d38bac1829462e0a1f76e3829840f0102196e6` |
| Preparation receipt | `efd1448404d08281b0cb4c781074f9578d6e088c83a859eb33d5d4e161d4d218` |
| Exact revision audit | `6bed84066b8ab07e6c0b9ca1215dd76f8910946189bb7840737c6395ed213112` |
| Source586 | `586ffb58b6af31c77a2e7cbcb83b173ffa4713ec62401da30901c5a7e606283b` |
| Fixed pack | `2663805a5180a1961850c1068b0c1c3615c010cd2ec47d38a228d65dde4800cb` |
| KLayout / IHP PDK | 0.30.9 / `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, runtime checked |

Full artifacts are retained under the unique local run IDs
`bgr-hbt-fullbank-20260922-r1` and `bgr-hbt-fullbank-20260922-r2`, pending a
separate exact public export. See the [routing contract](ROUTING_CONTRACT_20260922.md),
[revision contract](REVISION_R2_CONTRACT_20260922.md) and proposed
[stock gate](STOCK_CONTRACT_20260922.md). No stock run is implied by this report.
