# Exact 34-HBT worst-row pilot — prospective preparation contract

Source586 and pack SHA2663805a are fixed. Select only HBT slots in rows7/11:
24 XQ75 units, eight XQ76 units and two XQ74 units. Retain original positions,
orientations and native/contact geometry by instancing the exact passed HBT
prototype03/04 GDS cells. Mapping is explicit: prototype03=c2/vbe/dvbe/vss;
prototype04=vd1/vd1/vd2/vss. No additional native devices or dummy HBTs.

Six ports: c2, dvbe, vbe, vd1, vd2, vss. M1 base/collector/guard landings,
M2 terminal escapes and six bank-side trunks, segmented M3 row collectors.
Base contacts escape below the row; emitter/collector/guard contacts above.
This avoids taking a base M2 escape through the native M2 emitter pad.
Every added Via1/Via2 transition uses two0.19um cuts on0.42um pitch, with
0.055um metal enclosure. Redundancy is geometric; no current-sharing credit.

Before any stock run, require source subset/ports, unchanged prototype polygons
and native Activ/GatPoly, materialized physical metal/via connected components,
all136 terminal incidences assigned to exactly their six expected components,
via enclosure, no cross-net component, and source-pinned obstruction checks
against all1002 non-pilot devices. Neighbor HBT/MOS contact geometry comes from
the exact passed prototypes; resistor native PCells retain source dimensions.
Future whole-macro guards, feeds and fill are NOT RUN, not assumed clear.
Use0.3um conservative same-layer route-to-known-neighbor clearance screening;
this is an additional diagnostic, not a substitute for unchanged stock rules.

One CPU0 process,180s preparation bound,.10GiB output bound after fresh resource
gate. Preserve failed output and exceptions. No automatic routing ladder,
stock checks, analog simulation, source changes or full-macro adoption.
After preparation, send frozen source/GDS/CDL/graph hashes and a separate
prospective stock contract to root for review before DRC/LVS execution.
