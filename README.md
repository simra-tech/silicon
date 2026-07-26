# Simra Silicon

Chip designs produced by an autonomous agent team, on the IHP SG13G2 open PDK
(SiGe BiCMOS, HBT fT ≈ 350 GHz).

This repository holds **only what is needed to reproduce and verify the designs**:
sources, constraints, scripts, and the evidence a reviewer would want in order to
disagree with us. Everything is Apache 2.0.

## Status

| Design | Target shuttle | State |
| --- | --- | --- |
| — | IHP SG13G2, registration 2026-09-21 | in specification |

Nothing has been fabricated yet. When something has, this table will say so, and
it will say plainly what passed, what did not, and what was never checked.

## How to read this repository

Each design lives under `designs/<name>/` with its own README stating what it is,
what was measured, and what remains unverified. Where a check did not run, that is
recorded as *not run* rather than omitted — an unrun check and a passed check look
identical in a summary table and are entirely different facts about a chip.

## Reproducing

Designs are built with open-source EDA tooling against a pinned PDK revision. Each
design records the exact PDK commit it was built against, and the tool versions
used, so a result can be reproduced rather than taken on trust.

## Authorship

Commits are made by agents under a project identity
(`Principal Engineer Agent <agents@simra.tech>`), which is why they do not resolve
to a GitHub account. Each commit records the role and the model that produced it in
a trailer:

```
Agent-Role: Principal Engineer
Agent-Model: <model id>
```

Tape-out submissions are signed by a human, who takes responsibility for what goes
to the foundry.

## Licence

Apache License 2.0 — see [LICENSE](LICENSE).
