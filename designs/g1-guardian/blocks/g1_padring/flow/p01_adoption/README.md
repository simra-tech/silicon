# Unpromoted P01 adoption proposal

`prepare_views.py` builds a reviewable local-cell/source proposal from the
scratch candidate that passed stock hard/recommended DRC, antenna and density.
It refuses an unverified input hash or incomplete physical-check manifest.
It writes only to a new output directory; no production file or PDK file is
changed. The actual checked GDS remains a diagnostic until full IO-inclusive
LVS and electrical checks close.

```sh
G1_CPUS=2 flow/run.sh python3 designs/g1-guardian/blocks/g1_padring/flow/p01_adoption/prepare_views.py --candidate build/scratch/pad-outward-dummy-clean-20260921/g1_chip_top.gds --manifest designs/g1-guardian/review/audits/pad-outward-dummy-clean-20260921/manifest.json --output build/scratch/p01-adoption-replay
```

The candidate is reproducible with the retained `geometry_candidates.py`
recipe and its archived source snapshot in `review/audits`.

Generated artifacts:

- `g1_chip_top_proposed.gds`: local cell names; every merged polygon layer is
  compared to the checked candidate and must be identical. Labels are not
  independently compared.
- `ip/g1_p01/sg13g2_IOPadIn_g1_vdddummy.gds`: local input-pad cell with the
  independently specified W4.65/L0.45 all-VDD PMOS, plus Activ/GatPoly/Metal1
  no-fill metadata for future fill regeneration. That metadata is additional
  to the identical full-chip snapshot and requires fresh checks after assembly.
- `ip/g1_p01/bondpad_70x70_tm1_g1_exit.gds/.lef`: existing 70 µm pad opening
  geometry with a 4 µm inward TM1/TM2 extension. A placement offset of
  `(5,-74)` moves the opening outward 4 µm while keeping the electrical stub
  connection. The LEF includes the resulting 70×74 µm metal footprint.
- `g1_chip_top_proposed.cdl`: original design with the explicit added dummy
  and local cell names. `ip/g1_p01/g1_p01.cdl` contains only the two local
  cells and requires the unchanged stock IO child definitions. Add this file
  as another `--lib` when running `assemble_chip_cdl.py`; do not replace the
  original macro/CDL libraries with an extracted netlist.
- Full IO LEF/Verilog and Liberty files containing the cloned input cell.
  Liberty timing is copied from the stock cell for a flow rehearsal and is
  **unqualified** for the modified physical cell. Electrical, power-sequence,
  capacitance and timing qualification are **not run**.
- `proposed_adoption.patch`: unapplied changes to both flow configs and the
  top RTL. Copying generated views into production, applying this patch,
  regenerating the assembly/fill and all resulting checks are **not run**.
- `padmap_delta.csv`: all 24 original and proposed opening centers, keyed by
  bondpad instance, with exact ±4 µm deltas.

The proposal does not resolve the independent stock IO resistor-recognition,
substrate-tap parameter and diode/clamp topology mismatches. It is not a
signoff waiver. Evidence for the executed proposal is retained in
`review/audits/p01-adoption-20260921-r3`; its patch passes `git apply --check`.
