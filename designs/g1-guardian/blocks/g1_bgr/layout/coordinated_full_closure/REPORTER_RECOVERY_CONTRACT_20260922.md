# Output-only CC reporter recovery

The original full representation timed out at 300 and 900 seconds. The exact-
union representation subsequently failed with SIGSEGV after 502.101 seconds;
the last native trace was diagnostic report shape output. That establishes a
failure location, not an OOM diagnosis. The 4 GiB setting was an unenforced
reservation; observed RSS reached approximately 4.07 GiB.

The new experiment preserves the installed KPEX 0.3.12 CC numerical engine,
KLayout 0.30.9, technology, models, rule decks, union LVSDB and extraction options.
CLI default `blackbox_devices=False` is retained. The native engine API omits
CSV/SPICE output paths, exposing binary64 fF values before rounded serialization.
Raw `VSUBS` remains a distinct, unbound node.

An output-only `ExtractionReporter` subclass overrides exactly overlap,
sidewall, side-overlap and debug edge-neighborhood output. Each increments a
counter without retaining geometry. Original constructor and RDB save remain.
Installed source inspection confirms numerical result accumulation precedes
these callbacks and their return values are unused. The module's reporter
factory is restored afterward; no installed file is edited. Numerical result
methods, geometry operations, technology values and models are not overridden.

The prospective small control requires all 21 net pairs and all binary64 fF
values identical between original reporter and adapter, identical database,
technology, package hashes and material inventory, callback exercise, and parity
with the historical rounded CSV. No tolerance or capacitor pruning is allowed.
This control passed; original and adapted exact JSON hashes are identical.

The full experiment is one 900-second, single-thread CPU 0 run with five-second
kill grace, fresh 50%-policy resource gate, 8 GiB RAM reservation (not enforced),
and 2 GiB external output bound. The passed small-control receipt and exact
worker hash are launch preconditions. Each failure keeps its unique directory.

| Check | Status at preparation |
|---|---|
| Original 300/900-second full attempts | failed: timeouts retained |
| Exact-union full attempt | failed: SIGSEGV retained |
| Small 21-value binary64 reporter parity | passed |
| Full native CC recovery | not run to completion |
| Actual material coverage | not run to completion; separate gate |
| Source-derived replacement of historical 329 Cext | not run |
| Electrical qualification / adoption | not run |
| Extracted resistance | not applicable to this CC-only experiment |

Successful raw generation alone does not establish material completeness,
substrate binding, signoff, electrical fidelity or source adoption. The canonical
1036-device source, including all nine grounded HBT models, remains unchanged.
