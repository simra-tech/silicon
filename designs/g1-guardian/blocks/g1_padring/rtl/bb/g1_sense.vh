// SPDX-License-Identifier: Apache-2.0
// Black box of blocks/g1_sense (pins from layout/g1_sense.lef and its README);
// the block ships no .vh of its own.
(* blackbox *)
module g1_sense (
`ifdef USE_POWER_PINS
    inout  vdd,       // 3.3 V, IOVDD (north bar)
    inout  vss,       // IOVSS, substrate (south bar)
`endif
    inout  sense_p,   // SENSE_P pad, bare
    inout  sense_n,   // SENSE_N pad, bare
    inout  iptat,     // from g1_bgr
    inout  vref,      // from g1_bgr
    inout  isense,    // to g1_trip
    inout  vref_buf,  // to g1_trip
    inout  vped       // pedestal monitor
);
endmodule
