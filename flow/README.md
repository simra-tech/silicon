# flow/ — how every tool in this repository is run

All EDA tools run inside one pinned container image so that every log carries
the same tool versions and the same PDK commit. Nothing is installed on the host.

| Script | Purpose |
| --- | --- |
| `run.sh` | Runs one command inside the container with the repository mounted at `/work`, `PDK_ROOT=/foss/pdks`, `PDK=ihp-sg13g2`, as the calling user. `G1_WORKDIR=<repo-relative dir>` sets the working directory inside the container; `G1_EDA_IMAGE` overrides the image tag. |
| `run_ring.sh` | Reproduces the pad-ring build of `designs/g1-guardian/blocks/g1_padring` (bondpad generation, LibreLane `Chip` flow). |

Examples:

```
flow/run.sh ngspice -v
G1_WORKDIR=designs/g1-guardian/blocks/g1_bgr flow/run.sh ngspice -b sim/decks/vref_temp.cir
flow/run.sh python3 /foss/pdks/ihp-sg13g2/libs.tech/klayout/tech/drc/run_drc.py --help
```

Tool versions and the PDK commit inside the image are listed in
`designs/g1-guardian/PLAN.md` section 2 and are re-established by each run log
(simulator banner, `klayout -v`, flow log header). The container clock is UTC;
timestamps in logs are therefore two hours behind the CEST host during the
2026 tape-out.

The image itself is not part of this repository; its digest is recorded in the
plan so a run can be attributed to it.
