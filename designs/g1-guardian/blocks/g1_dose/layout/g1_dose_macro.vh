// G1_DOSE black box for the chip flow (LibreLane MACROS entry, see ../../g1_padring/INTEGRATION.md).
// Analog macro, no timing arcs. Pins are Metal3 stubs on the west edge (layout/g1_dose_macro.lef);
// vss (source, body, p+ rings) is the Metal3 bar on the south edge. D_ELT carries the thick-oxide
// sg13_hv_nmos drain, D_STD the sg13_lv_nmos drain; G_SHARED is the common gate (0 to 3.3 V from the pad).
(* blackbox *)
module g1_dose_macro (
`ifdef USE_POWER_PINS
    inout  vss,      // substrate / source / body
`endif
    inout  D_ELT,     // HV NMOS drain, to pad 21 (pad name kept from the ELT variant)
    input  G_SHARED,  // shared gate, from pad 19
    inout  D_STD     // LV NMOS drain, to pad 20
);
endmodule
