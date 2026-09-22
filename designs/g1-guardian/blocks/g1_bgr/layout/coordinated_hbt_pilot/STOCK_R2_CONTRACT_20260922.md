# HBT r2 stock contract — not run

Root approved only ten collector Via1 array rotations. Preparation passed in
14.092 s with 378025 bytes output. Exact source586, all 34 positions, all 136
terminal incidences/six ports and all other geometry remain unchanged. Subset
CDL and physical terminal-graph JSON are byte-identical to r1. Native
Activ/GatPoly, known 1002-neighbor clearance and all added-via enclosures passed.

Serialized GDS XOR against retained r1 is confined to the ten declared landing
windows: M1=0.435 µm² (20 polygons), M2=1.89 µm² (10 polygons), Via1=1.444 µm²
(40 polygons). Every other drawn layer and all texts are unchanged. Ledger
differences are exactly 20 old/20 new landing records and 20 old/20 new Via1
cuts; all other routes/cuts/nets are unchanged. Arrays remain two 0.19 µm cuts
on 0.42 µm pitch with 0.055 µm enclosure. Predicted side gap is 0.30 µm; stock
rules still decide.

Frozen inputs in build/scratch/bgr-hbt-worstrows-20260922-r2:

| File | SHA256 |
| --- | --- |
| pilot.gds | `ec730fb53152217a5f2c35c44f53362b9ab47684cdd8726a320388eaf34cc295` |
| pilot.cdl | `8aeac3748ccc6c00a6804bb75e63f07332a67acf64b27daf6cac71f8e3990e72` |
| revision_audit.json | `093ad13ac6a79ba215001ad4b302057bf60f1ac06e76fc1bb817bdce28151a61` |
| preparation.json | `b8f3a3b2187e693cc8f93e62212e135757f25d1c4071543e3d26d624944da40d` |

run_stock_r2.py binds these plus subset, terminal-graph, neighbor and route-ledger
hashes and all 18 source/contact inputs. Its logic is the frozen r1 stock runner
with only candidate/output/contract paths and frozen hashes changed. Historical
running run.json hash within preparation remains explicitly historical; no
mutable run receipt is included in the frozen input gate.

After root review and a fresh resource gate, propose exactly one stock DRC and
one strict stock LVS, separately on CPU0, 180 s per invocation, 0.10 GiB combined
growth. Unchanged IHP PDK 84374023ee8b4b126bebbba67fcbada0a9c0ff0b/KLayout 0.30.9.
Same acceptance as r1: stock hard/recommended/off-grid/angle DRC (--no_density)
must complete with zero markers; require explicit LVS match and every circuit,
device, net, pin and subcircuit cross-reference status Match, not
MatchWithWarning/Skipped/None. Missing reports, timeout, nonzero exit, frozen
input changes or deck changes fail. Preserve all failures; no automatic reroute
or retry. No source/model/rule edits.

R1 remains DRC failed (ten M2.b markers)/LVS passed. Density, antenna, full-macro,
current, PEX, analog and physical adoption remain not run; seed not applicable.
No feed or upper metal is added.
