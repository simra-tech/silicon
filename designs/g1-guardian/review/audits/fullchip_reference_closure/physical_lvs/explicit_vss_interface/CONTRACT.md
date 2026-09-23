# Explicit I/O substrate interface — authorized source derivative

The owner authorized a separate source-interface change connecting the current
I/O substrate to external VSS. This is an intentional circuit declaration, not
inference from the `SUB!` suffix or a claim that the original source matched.
Original source `f4ce6848bd7dd179d2ef4cbd8a4ea6bf9788bcfa1ff4b93fabae8bf18b6378f9`
and every original failure remain unchanged.

Propagate a fresh explicit body pin through only the affected reachable I/O
hierarchy. Replace original local `SUB!` terminal references by that pin; connect
the topmost affected instances to the existing top VSS pin. Preserve all original
external signal/supply pins, device instances, model names, parameters and all
other terminal partitions. VDD, IOVDD and IOVSS remain distinct from VSS.
No `.GLOBAL`, name-forced layout connections, model or rule edits are allowed.

Prospective checks: exact reverse byte restoration; complete flattened primitive
and terminal correspondence; only originally local SUB! incidences change to VSS;
all 386 reachable taps and original A/P preserved; wrong-domain, missing-device
and altered-parameter controls rejected. A separately reversible tap-prefix
adapter exposes the existing primitives to the pinned reader, not a new tap model.

The complete literal source contains 245 local substrate domains and 941 terminal
incidences. Of these, 243 domains/889 incidences belong to the previously audited
PTAP-WELL partitions; two further resistor-only domains contain 52 RPPD substrate
terminals. CDL `$SUB=...` annotations are electrical terminals, not ignored
comments. The first two preparation attempts failed the narrower 889/243
assertion; both sources and failure receipts are retained. The corrected control
requires both the complete inventory and the independently identified subsets.

Then compare against the unchanged native saved extraction with actual physical
22-port binding and stock comparison semantics. Report every remaining mismatch;
the separately proven dummy exception, if used, must remain explicitly separate.
One bounded engine comparison may run on CPU0 after a fresh coordinated resource
gate, at most 900 seconds,
16 GiB RAM reservation and 2 GiB bulk growth. No original source overwrite.

The owner subsequently authorized 60% of otherwise available CPU prospectively;
the separate V2 launch wrapper uses that coordinator-tested gate and current
56-CPU allocation. Original 50% wrappers and failed prelaunch receipts remain
unchanged. No existing valid child is interrupted by a later resource dip.

The first native comparison attempt failed in source parsing, before comparison:
an unused library definition called a modified child with its original pin count.
The next source revision keeps every original library definition byte-identical
and adds distinctly namespaced design-local clones for the affected hierarchy.
Only top calls select those clones. Full-library call signatures and exact
original-definition retention are additional mandatory checks; the intended
reachable device/terminal change remains exactly the same.

Tap A/P applicability, physical/electrical tap interpretation, power sequencing,
latch-up and ESD qualification remain unresolved/not run. A matched topology or
strict comparison is not an electrical/ESD qualification. This derivative alone
does not change native geometry or complete fullchip acceptance.
