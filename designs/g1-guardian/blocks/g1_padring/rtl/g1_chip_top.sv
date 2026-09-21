// SPDX-License-Identifier: Apache-2.0
// G1 chip top: pad ring for the 24-pin G1 radiation-aware node guardian.
//
// One sg13g2_io cell per pin, instantiated flat with the pin number in the
// instance name; these instance names are the placement handles used by the
// PAD_SOUTH/EAST/NORTH/WEST lists in flow/config.yaml. Pin numbers, cell types
// and side assignment follow specification/G1_TOP_LEVEL_SPECIFICATION.md
// section 3. The pad idiom (power pins under USE_POWER_PINS, (* keep *) on
// supply pads) follows iic-jku/ihp-sg13g2-ams-chip-template rtl/chip_top.sv
// and ChipDesign-BV/pad-ring-ihp src/chip_top.v.
//
// The core is a separate module (g1_core_placeholder) so that the analog and
// digital macros can replace it without touching the ring.
//
// sg13g2_io port convention (libs.ref/sg13g2_io/verilog/sg13g2_io.v):
//   pad     bond pad (chip pin)            p2c  pad -> core (inputs)
//   c2p     core -> pad (outputs)           padres  analog terminal behind the
//   vdd/vss core rails (1.2 V)                      587 ohm series resistor
//   iovdd/iovss IO rails (3.3 V)           padbare analog terminal in front of it
// `padbare` exists only in ip/sg13g2_io_padbare (views derived from the PDK
// files; the core-side geometry of the stock `pad` pin renamed, same conductor,
// GDS unchanged). Kelvin-sense and device pins use padbare so no resistor sits
// in the measurement path; TRIP_SET and VREF use padres (high-impedance
// comparator input / bandgap monitor output, the resistor is harmless there and
// keeps the secondary protection). Pin 7 VDDA is an analog pad whose padbare
// terminal is the 3.3 V analog supply net of the core (D14).

`default_nettype none

module g1_chip_top (
`ifdef USE_POWER_PINS
    inout wire VDD,      // 1.2 V core
    inout wire VSS,      // core ground / substrate, also analog ground
    inout wire IOVDD,    // 3.3 V IO ring
    inout wire IOVSS,    // IO ground
`endif
    // east (pins 7-12); pin 7 VDDA: 3.3 V analog supply through the bare
    // terminal of an analog pad (PLAN.md D14), a supply net inside the core
    inout wire VDDA,
    inout wire SENSE_P,
    inout wire SENSE_N,
    inout wire GATE,
    inout wire FAULT_N,
    inout wire EN,
    // north (pins 13-18)
    inout wire TRIP_SET,
    inout wire SCLK,
    inout wire SDI,
    inout wire SDO,
    inout wire TEMP_OUT,
    inout wire VREF,
    // west (pins 19-24)
    inout wire G_SHARED,
    inout wire D_STD,
    inout wire D_ELT,
    inout wire HBT_E,
    inout wire HBT_B,
    inout wire HBT_C
);

    // ---- core-side nets --------------------------------------------------
    logic en_i, sclk_i, sdi_i;                   // pad -> core
    logic gate_o, fault_n_o, sdo_o, temp_out_o;  // core -> pad
    wire  trip_set_res, vref_res;                              // analog, padres
    wire  sense_p_bare, sense_n_bare;                          // analog, padbare
    wire  g_shared_bare, d_std_bare, d_elt_bare;
    wire  hbt_e_bare, hbt_b_bare, hbt_c_bare;

    // ---- south: pins 1-6, left to right -----------------------------------
    (* keep *) sg13g2_IOPadVdd   pad01_vdd   (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );
    (* keep *) sg13g2_IOPadVss   pad02_vss   (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );
    (* keep *) sg13g2_IOPadIOVdd pad03_iovdd (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );
    (* keep *) sg13g2_IOPadIOVss pad04_iovss (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );
    (* keep *) sg13g2_IOPadVss   pad05_vss   (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );
    (* keep *) sg13g2_IOPadIOVss pad06_iovss (`ifdef USE_POWER_PINS .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS) `endif );

    // ---- east: pins 7-12, bottom to top -----------------------------------
    // pin 7 VDDA (D14): analog pad, bare terminal = the VDDA supply net
    (* keep *) sg13g2_IOPadAnalog pad07_vdda (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(VDDA), .padres(), .padbare(VDDA));

    (* keep *) sg13g2_IOPadAnalog pad08_sense_p (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(SENSE_P), .padres(), .padbare(sense_p_bare));

    (* keep *) sg13g2_IOPadAnalog pad09_sense_n (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(SENSE_N), .padres(), .padbare(sense_n_bare));

    sg13g2_IOPadOut30mA pad10_gate (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .c2p(gate_o), .pad(GATE));

    sg13g2_IOPadOut4mA pad11_fault_n (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .c2p(fault_n_o), .pad(FAULT_N));

    sg13g2_IOPadIn pad12_en (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .p2c(en_i), .pad(EN));

    // ---- north: pins 13-18, left to right ---------------------------------
    (* keep *) sg13g2_IOPadAnalog pad13_trip_set (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(TRIP_SET), .padres(trip_set_res), .padbare());

    sg13g2_IOPadIn pad14_sclk (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .p2c(sclk_i), .pad(SCLK));

    sg13g2_IOPadIn pad15_sdi (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .p2c(sdi_i), .pad(SDI));

    sg13g2_IOPadOut4mA pad16_sdo (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .c2p(sdo_o), .pad(SDO));

    sg13g2_IOPadOut16mA pad17_temp_out (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .c2p(temp_out_o), .pad(TEMP_OUT));

    (* keep *) sg13g2_IOPadAnalog pad18_vref (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(VREF), .padres(vref_res), .padbare());

    // ---- west: pins 19-24, bottom to top ----------------------------------
    (* keep *) sg13g2_IOPadAnalog pad19_g_shared (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(G_SHARED), .padres(), .padbare(g_shared_bare));

    (* keep *) sg13g2_IOPadAnalog pad20_d_std (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(D_STD), .padres(), .padbare(d_std_bare));

    (* keep *) sg13g2_IOPadAnalog pad21_d_elt (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(D_ELT), .padres(), .padbare(d_elt_bare));

    (* keep *) sg13g2_IOPadAnalog pad22_hbt_e (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(HBT_E), .padres(), .padbare(hbt_e_bare));

    (* keep *) sg13g2_IOPadAnalog pad23_hbt_b (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(HBT_B), .padres(), .padbare(hbt_b_bare));

    (* keep *) sg13g2_IOPadAnalog pad24_hbt_c (
`ifdef USE_POWER_PINS
        .vdd(VDD), .vss(VSS), .iovdd(IOVDD), .iovss(IOVSS),
`endif
        .pad(HBT_C), .padres(), .padbare(hbt_c_bare));

    // ---- core (placeholder; replaced by the G1 macros later) -------------
    g1_core_placeholder i_core (
`ifdef USE_POWER_PINS
        .VDD(VDD), .VSS(VSS), .VDDA(VDDA),
`endif
        .en_i(en_i), .sclk_i(sclk_i), .sdi_i(sdi_i),
        .gate_o(gate_o), .fault_n_o(fault_n_o), .sdo_o(sdo_o), .temp_out_o(temp_out_o),
        .sense_p(sense_p_bare), .sense_n(sense_n_bare), .trip_set(trip_set_res), .vref(vref_res),
        .g_shared(g_shared_bare), .d_std(d_std_bare), .d_elt(d_elt_bare),
        .hbt_e(hbt_e_bare), .hbt_b(hbt_b_bare), .hbt_c(hbt_c_bare));

endmodule

`default_nettype wire
