# Source-held TRIP feed and internal-access gate

The existing native source retains VDD M3 header y941–943, VDDA M3 header
y938–939.5 and VSS M3 header y736–738 µm. Source-PNL/OpenDB binds these to
VDD, VDDA and VSS, respectively. The actual connected-net inventory proves
the header identities; names alone do not authorize contact.

Initial external screening uses VDD TM2 y942 to root VDD TM1 at(750,942),
VSS TM2 y737 to root VSS TM1 at(1039.2,737), and separate VDDA TM2 y934.5
to the existing shared bus x1060. Root landings use TopVia2 only; no new
lower stack crosses the east core-VDD ring. Three VDD, five VDDA and three
VSS source-side stacks distribute access along the retained native headers.
Candidate M3 widening of VDDA/VSS to3.2 µm is additive only and must pass the
same foreign-metal/cut and stock rules. This is a proposal, not saved geometry.
The first screen failed upper-metal landing proximity and VSS-neighbor spacing.
The second screen rotates VDD/VDDA TopVia2 pairs to two horizontal cuts,
widens VSS only downward to y734.8–738.0, and moves its last source stack
from x968 to x972 to avoid the actual core-VDD spine. Earlier failures remain.

Exploratory external targets are2 mA VDD,8 mA VDDA and9 mA VSS. None is a
qualified current envelope or assurance of actual branch sharing. The shared
pad's10 mA assumption remains a total, not a per-block allocation. Historical
TRIP sampled VDDA6.32035 mA/VDD1.81295 mA peaks come from the older nominal
fixture and are neither internal rail partitions nor hot-lifetime limits.

The native source contains0.6 µm M4 DAC feed rails at x778.5/893.5 for VDD
and840.5/955.5 for VDDA, from y746.3 to their headers. Their lower Via2/Via3
and M2 accesses remain separate bottlenecks. Read-only1.2/2.2/4.2 µm additive
M4 widening screens are independent diagnostics; they are not silently added
to the external recipe. Passing parallel external stacks does not qualify
these internal rails, native contacts or actual transient division.

Any accepted internal remedy must preserve all original source primitives,
placement, parameters, source pin map and model/rule bytes. It requires exact
native additive proof, flattened no-other-net contact, stock DRC and the
unchanged source-derived TRIP LVS reference. Intrinsic/extrinsic PEX changes,
actual rail partition, IR/current crowding/PVT/EM and final signal context
remain separate required gates. No source/deck/golden tuning or adoption.
