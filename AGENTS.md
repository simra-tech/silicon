# Agent conventions for simra-tech/silicon

This repository is public. It holds chip designs and the evidence needed to
reproduce and verify them, nothing else.

## What goes in, what stays out

Commit:

- sources: schematics (`.sch`), netlists, layout (`.gds`, `.lef`, `.mag`), RTL,
  scripts, decks, constraints
- specifications and design records: what a block must do, what was simulated
  or measured, with the exact command, tool version and PDK revision
- verification evidence: DRC/LVS/PEX reports, simulation logs, measurement data
- pad maps, package and bonding information, bench and test plans

Never commit:

- strategy, market, pricing, customers, partners, competitors, negotiations
- anything received under NDA or from a foundry outside its public PDK
- credentials, machine-specific absolute paths, or private contact details
- draft claims that no run supports (see "not run" below)

Working notes that fall in the second list live under `.private/` at the repo
root. That directory is gitignored. A session should read `.private/CONTEXT.md`
if it exists and treat it as the current non-public context. Do not copy its
contents into tracked files, commit messages or issues.

## Reporting rule

A check that did not run is recorded as **not run**, never omitted. Status tables
distinguish *passed*, *failed*, *not run* and *not applicable*. A simulated number
is labelled simulated; a measured number names the instrument and the sample.

## Layout of a design

```
designs/<name>/
  README.md                 what it is, state, built-against, what was measured
  specification/            top-level spec, block breakdown, pin map, parameter
                            classification (specified / assumed / unknown)
  blocks/                   one directory per block: sources, sims, layout, reports
  padframe/                 IO ring, pad map, package and bonding notes
  measurement/              bench plan, fixtures, results (or "not run")
```

Every design README carries a "Built against" table: PDK commit, ngspice,
xschem/KLayout, and any flow (LibreLane, CACE) versions, with how each version
was established.

## Process and tools

- PDK: IHP SG13G2 open PDK only. Pin the commit in each design README.
- Simulation: ngspice with the PDK's pinned model libraries.
- Layout and checks: KLayout with the PDK's DRC and LVS decks; digital blocks
  through LibreLane; the IO ring uses the PDK's `sg13g2_io` cells.
- Do not modify rule decks or model cards. A failing rule is a design problem.

## Commits

Author identity is the project identity, with role and model trailers:

```
Principal Engineer Agent <agents@simra.tech>

Agent-Role: Principal Engineer
Agent-Model: <model id>
```

Commit messages state what changed and what evidence supports it. Do not push;
a human pushes and signs tape-out submissions.
