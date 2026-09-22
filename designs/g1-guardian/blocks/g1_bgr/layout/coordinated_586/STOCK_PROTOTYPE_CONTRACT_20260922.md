# First isolated stock-rule prototype gate

This prospective gate covers exactly the eight source-bound MOS prototypes in
`build/scratch/bgr-mos-contact-prototypes-20260922-r2`, not a BGR macro.
The saved r1/r2 nontext polygon XOR, text inventory and CDL must be identical;
the r1 live-Region post-mutation audit remains failed. Native W/L and explicit
source diffusion area/perimeter must match before rule execution.

Run unchanged pinned IHP stock hard and recommended DRC, including off-grid
and angle checks, on all eight prototypes, sequentially with one CPU and a
180-second bound per invocation. Density and antenna are **not run** in this
first isolated-device gate; full-macro density/antenna remain required later.
Require completed reports and zero markers, not merely wrapper exit zero.
No rule-value edits or suppression are allowed.

Run unchanged stock LVS on prototypes00 (source-tied PMOS body) and03
(source-tied NMOS substrate) with their source-derived CDL, strict top ports
and ordinary tap extraction. Bound each invocation to180seconds. The initial
CDL contains the exact active-device source line but no added explicit tap
devices: any tap-device or terminal mismatch must be reported as failed, not
waived using extraction-to-golden fitting. The contact implementation and
physical tap annotation may then be revised under a separate prospective gate.

Each invocation retains argv, tool/deck hashes, status, time, report counts and
raw logs. Solver timeout, missing report or unknown LVS outcome is failed.
Random seed is **not applicable**. PDK revision is
`84374023ee8b4b126bebbba67fcbada0a9c0ff0b`; KLayout is0.30.9.
The batch requires a fresh resource gate for0.15GiB growth and uses one CPU.
No population simulations, routing, full physical fit, voltage/current
reliability or adoption are authorized by a pass here.
