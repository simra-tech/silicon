# IO-powered buffer candidate — not adopted

This isolated schematic candidate replaces the GATE digital output pad with an IO-powered, deliberately skewed HV receiver, an HV output inverter, and the unchanged `sg13g2_IOPadAnalog` connected through its protected `padres` terminal. It retains the existing GATE core logic. The goal is to avoid dependence on core-powered pad level shifting while the core rail is missing.

The receiver uses PMOS W/L=1/2µm and NMOS10/0.45µm; output devices are PMOS80/0.45µm and NMOS40/0.45µm, with a100kΩ input return. These are schematic devices using unchanged pinned IHP model wrappers, without new layout parasitics. Static receiver current, switching threshold/margins, output timing, layout legality, EM, ESD, temperature and mismatch still require qualification.

[IHP pin documentation](https://ihp-open-pdk-docs.readthedocs.io/en/latest/contents/io_library/04_pin_interface.html) identifies `padres` as the resistor/diode protected terminal. [IHP's IO-cell review](https://ieee-cas.org/files/ieeecass/2025-12/io-cells-sg13g2_0.pdf) describes the analog cell as bidirectional. Those documents do not qualify this custom gate driver or establish the protection resistor's permissible repeated drive energy.

Initial six cases failed parsing because primitive-M instances were used for PDK subcircuit wrappers. Original source snapshots and failures remain in `campaigns/20260921T170826Z_71b9f639` and `...170827Z_55c0abac`. Corrected X instances then complete six nominal EN-low sequences: IO-first/missing-core/simultaneous (`...170949Z_1a3bf692`) and core-first/core-off-first/IO-off-first (`...170950Z_0ea16c6f`). Maximum positive GATE excursion is about70.4µV. These are only nominal startup/shutdown checks with the5nF fixture.

Tight-tolerance late-EN tests (`...171148Z_1bab10f8`) **fail numerically** near9.05389µs at `vh#branch` or `vf#branch`; arming acceptance is not run to completion. The nominal4A vendor-FET test (`fet_20260921T171147Z_a602296e`) **fails numerically** at5.82444µs at `xfet.10`. Thus no completed active-load timing or qualified arming evidence exists for this candidate. Do not adopt it from the EN-low passes.

No candidate layout, DRC, LVS, extracted parasitics, mismatch campaign, EM/ESD or full integrated verification has run. Delivered padframe and GATE design remain unchanged. `run_power_campaign.py --pad buffered_analog` and `run_fet_campaign.py --pad buffered_analog` preserve a per-run candidate source snapshot. Default `--pad out` continues to use the original output pad.

See [2026-09-22 diagnostics](DIAGNOSTICS_20260922.md) for the isolated driver passes, unchanged single-diode reproducer and retained failures. Candidate remains unadopted.
