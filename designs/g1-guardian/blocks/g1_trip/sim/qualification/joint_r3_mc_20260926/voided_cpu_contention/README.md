# Voided attempts (CPU contention), 2026-09-26

Seeds 79005 and 79007 (CPUs 104, 106) and 79017, 79018 (the same CPUs, relaunched there) timed out at the
1200 s probe watchdog on their first probes. Other chip-level ngspice runs of this account (g1_top
`run_top.py`, not part of this screen) were pinned to the same CPUs 104 and 106 and took about 62 % of each
core. For example, 79005 p00 had reached t = 1.0177 us of 1.02 us when the watchdog killed it.

These are infrastructure failures, not solver or electrical ones. The attempts are kept here unchanged
(per-seed `summary.json`; bulk logs under `${BULK}/joint_r3_mc_20260926/voided_cpu_contention/`), and the
four seeds were rerun from scratch on uncontended CPUs. 79017 and 79018 were stopped by `podman kill`
during their second probe.
