# Provenance of the release files

Container: `tapeoutbench-eda` (image `sha256:ddeb69576f2808676d1c5d474ecf04f6d1d6f8abdcff6b72b39790ded924bab2`),
KLayout 0.30.9, PDK commit `84374023ee8b4b126bebbba67fcbada0a9c0ff0b`, launched through
`flow/run.sh` of https://github.com/simra-tech/silicon (repository mounted at `/work`).
`${REPO}` is the silicon repository checkout, `${PKG}` this package directory (mounted into the
container through `G1_RESULTS_ROOT`).

1. Re-save with renamed top cell (`resave_for_ihp.py`):

```
cd ${REPO}
G1_CPUSET=0-3 G1_RESULTS_ROOT=${PKG}/.. flow/run.sh klayout -b -r ${PKG}/release/v.1.0.0/doc/provenance/resave_for_ihp.py \
  -rd input_file=/work/designs/g1-guardian/blocks/g1_padring/layout/g1_chip_top_1414_r4.gds \
  -rd output_file=${PKG}/release/v.1.0.0/gds/SoC1816.gds -rd newtop=SoC1816
```

2. Geometry identity (`compare_gds.py`, output `compare_r4_vs_SoC1816.json`): every cell, every
   layer/datatype, sorted shape list with properties, and every instance with its transformation and
   array parameters, compared between the source and the release file, top cell mapped by name.
   Result: identical (304 cells, 3 122 cell-layer pairs, 1 284 438 shapes, 55 646 instances).
   Negative control: the r3 GDS against the release file differs in exactly the TRIP cell
   `__rz_port_text_033_retained_g1_trip` and the top cell (`control_r3_vs_SoC1816.json`).
3. Inspection (`inspect_gds.py`, outputs `inspect_input_r4.json`, `inspect_SoC1816.json`): one top
   cell, dbu 0.001 um, bbox (0,0)-(1414,1414) um, 304 cells, 73 layers, 0 zero-length paths, 0
   zero-area shapes on the layer list of IHP `zero.py`, largest polygon 538 points (< 8000).
4. Raw GDS header (`gds_header.py`, output `gds_header.json`, host Python 3): GDS version 600,
   LIBNAME `LIB`, units 0.001 / 1e-9, 304 structures, no `$$$CONTEXT_INFO$$$` cell. The source file
   has zeroed time stamps; the release file carries the write time (the IHP figure has "Write
   current time to time stamps" checked), so its sha256 changes on every re-save.
