# Native MIM three-dimensional method-coverage control

This is one isolated native7×7µm PDK cmim coupon, not a SENSE geometry change,
electrical source substitution, capacitance fit or full-macro PEX qualification.
The same pinned KPEX0.3.12 technology/rules and native PCell are used unchanged.
The stock blackbox extraction drops2645µm² of SENSE bottom-plate interior;
the two-terminal cap_cmim model explicitly requires external plate extraction.
Those omissions remain failures regardless of the control outcome.

Build one native cmim with Calculate=C,w=7u,l=7u. Preserve every native polygon;
add only two terminal text labels, verified on Metal5 bottom and TopMetal1 top.
Save and reload with exact native nonannotation XOR0 and49µm² MIM area. Derive
the two-terminal reference directly from those declared native dimensions, not
from extracted capacitance. No MOS, resistor, tap or model-card alteration.

Run the supported whitebox FasterCap three-dimensional mode with the installed
full process stack, all dielectrics and one thread. Native stack includes the
Metal5 bottom,40nm k=6.7 MIM dielectric,150nm top plate and Vmim. This is a
deliberate method alternative, not the known unsupported whitebox2.5D retry.
Bound the complete child at120 seconds plus5-second cleanup and128MiB output,
CPU7, after a fresh global resource gate. Preserve failure/timeout; do not extend
the watchdog or repeat automatically. Bind installed technology/decks/cards.

Record real conductor/plate identities, actual meshed coverage, every warning,
native device dimensions, raw matrix, solver completion and finite entries.
The minimum method gate requires both49µm² plate interiors in the solver geometry
and a finite positive bottom-to-substrate coupling. This tests availability and
coverage, not an electrical error budget or a converged full-SENSE result.
The stock console matrix's numerical print precision must be reported honestly.
No intrinsic plate-to-plate matrix term is adopted alongside the native model;
separating intrinsic versus extrinsic terms, solver/context convergence, tap
contact coverage and source-preserving full-macro mapping remain independent
gates. A successful small coupon does not authorize a full-macro3D extraction.
