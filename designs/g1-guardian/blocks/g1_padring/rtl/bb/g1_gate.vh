// SPDX-License-Identifier: Apache-2.0
// Black box of blocks/g1_gate (pins from layout/g1_gate.lef and its README);
// the block ships no .vh of its own.
(* blackbox *)
module g1_gate (
`ifdef USE_POWER_PINS
    inout  vdd,        // 1.2 V (level shifters)
    inout  vdda,       // 3.3 V, IOVDD (north bar)
    inout  vss,        // VSS/IOVSS, substrate (south bar)
`endif
    input  trip_d,     // 1.2 V, from g1_digital
    input  clr_d,
    input  en_core,    // EN pad p2c
    input  hard_cmp,   // from g1_trip cmp_hard
    input  fast_en,
    output gate_core,  // to GATE pad c2p
    output tripped,    // to g1_digital
    output fault_core  // to FAULT_N pad c2p
);
endmodule
