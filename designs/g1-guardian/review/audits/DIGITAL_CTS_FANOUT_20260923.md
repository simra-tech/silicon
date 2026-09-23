# Digital clock-tree fanout remedy — candidate only

The placed CTS candidate meets the integrated fanout limit of eight without
changing RTL, source timing limits, package pins, or library/model files.
It is **not an adopted macro**: downstream routing and signoff remain not run.

The downstream wrapper `run_digital_postcts.py` resumes the candidate at the
first post-CTS STA step using the original Classic configuration and step
substitutions. Old SDF and placement/timing metrics are deliberately removed
from the initial state; only source headers and lint/synthesis checks survive.
The new flow runs in a fresh bulk directory with one CPU and one flow worker.
Its first preparation attempt failed because `Config.get_meta` requires a
string, not a Path; no flow step ran. The corrected attempt uses the required
argument type. Downstream execution results and independent affected-view
checks must be recorded separately before adoption. The state-isolation unit
control passed, bringing the current helper controls to 12.

## Built against

- Pinned image: `ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`.
- IHP PDK: `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, live COMMIT checked.
- Successful executable: OpenROAD `26Q1-1024-gdcf36133a`, the image's
  `openroad-librelane` binary. Each run records its executable SHA256.
- Stock LibreLane CTS Tcl and helper sources are hash-held. The saved run7
  pre-CTS OpenDB is `fb92d5d466f4d841324082476ef3bf6f88bbd1838ca6a8d23dab9c198a426876`.
- Original macro SDC is `c36bf03041045f951179e22970de05bcdcae2dd66374f175a9da8e91a2b84673`.

## Change and controls

`run_digital_cts_fanout.py` redirects output views to fresh directories and
reconstructs the installed flow's three timing-corner and layer/via-RC
environment from the saved configuration. The original inputs remain held.
The candidate sets `CTS_SINK_CLUSTERING_SIZE=8`; the option is documented in
the [OpenROAD CTS reference](https://openroad.readthedocs.io/en/latest/main/src/cts/README.html).
The actual pinned-runtime result, not that moving documentation, establishes
the observations below.

Smaller clusters removed the leaf violations but left one root driving 16
branches. The second candidate inserts exactly two `sg13g2_buf_16` cells:
each drives eight original root branches, and the original root drives these
two cells. All inserted cells are noninverting. Stock placement legalization,
power connections and placement parasitic estimation follow the insertion.
No clock frequency, uncertainty, load, or acceptance limit is relaxed.

| Check | Status | Result |
|---|---|---|
| First standalone launch | failed | Missing derived corner environment; synthesis not reached |
| PATH OpenROAD 26Q3 replay, two attempts | failed | Stock flow's scene-name/scene-object mismatch in `set_layer_rc`; exact stack retained |
| Explicit 26Q1 baseline | passed, scoped | 12.374 s tool; CTS netlist byte-identical to original run7 CTS, SHA `cf87ffb214b290f9d61f945f612c66b4e253695196cf02141a3bec810c429214` |
| Baseline integrated fanout | failed | Original violations retained |
| Cluster-eight candidate | failed fanout | 12.326 s tool; only root remains at 16 versus limit 8 |
| Cluster-eight plus two-buffer split | passed fanout | 13.379 s tool; 222 clock buffers, maximum attached-pin fanout 8, zero violations |
| Named device/terminal graph | passed | All 4,413 non-clock instances and terminal connections exact after contraction of proved noninverting CTS buffers |
| Dummy-load handling | passed, scoped | All 60 dummy outputs are unconnected; their input pins remain counted in physical fanout |
| Clock register counts | passed | 52 serial-clock and 1,148 oscillator-clock registers |
| Original DEF pin section | passed | All 46 pin declarations and geometries equal after whitespace normalization |
| Placed TMR separation | passed | All 199 stages / 597 flops; minimum 27.4 um, none below existing 20 um criterion |
| Harness and graph controls | passed | 11 tests, including wrong data connection, buffer cycle, inverter substitution and connected dummy output |
| Routed timing/PEX and DRC/LVS/antenna/density | not run | New macro requires downstream implementation and all affected checks |
| Full-chip integration and adoption | not run | Current adopted views are unchanged |
| Statistical seed | not applicable | Deterministic implementation control |

The contraction proof is structural, not timing equivalence. Dummy loading
and new clock latency require actual routed checks. The unchanged logical
graph does not qualify jitter, metastability, power, or final chip timing.

Candidate hashes:

- Netlist: `f991e5af3fa1a5ad1b0178de8287c1dc4519269f1c645a9a914a2bad430f8ad7`.
- OpenDB: `24d4207bcdc507b114f9237d004872155d32756f888b1e23d0c63668cc961c6b`.
- DEF: `c49dd1b75bed7fba3eefc229fc7642887acf4ebffc92061e40371ce4c20bd140`.

Bulk run identities are `digital-cts-baseline-20260923-r1` through `r4`,
`digital-cts-cluster8-20260923-r1`, and `digital-cts-split-20260923-r1`.
They retain source snapshots, environment, commands, input hashes, tool logs,
views and scoped summaries. The graph auditor independently reads the saved
netlists. Original failures are not overwritten by later successful controls.

Reproduction uses the saved run7 pre-CTS inputs and a fresh result directory:

```sh
python3 designs/g1-guardian/review/audits/run_digital_cts_fanout.py \
  --openroad /foss/tools/openroad-librelane/bin/openroad \
  --cluster 8 --split-root --output "${RESULTS}/digital-cts-split-NEW"
```

Run inside the pinned image, with one allocated CPU and the repository at
`/work`. Use `--cluster 0` without `--split-root` for the source-held baseline.
