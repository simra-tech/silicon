// g1_ls_up: 1.2 V -> 3.3 V level shifter (g1_ls library), black box for the chip-level flow.
// out follows in; vdd = 1.2 V core, vdda = 3.3 V IOVDD, vss = common ground. See ../README.md.
(* blackbox *)
module g1_ls_up (
    input  wire in,
    output wire out
`ifdef USE_POWER_PINS
    , inout wire vdd,
    inout wire vdda,
    inout wire vss
`endif
);
endmodule
