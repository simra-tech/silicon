// R1 full-chip testbench (track T10): the digital side of the chip inside one XSPICE d_cosim instance (Icarus).
//
// Contents:
//  1. u_ctrl: the r1_ctrl revision 0.5 RTL of record (rtl/r1_ctrl_top.v, unchanged, compiled with
//     -DR1_CFG_FLOPS -DR1_CFG_GATED as the r1_ctrl regression).
//  2. Glue that the chip needs but no block owns yet (labelled MODEL, see tb/README.md "What is not covered"):
//     a. ADC sequencer model: turns adc_start / adc_sel / adc_hold / is_smp into the r1_adc5_core timing ports
//        (trk, win, stb, lat) with the r1_adc revision-5 D18 timing (gen_timing_r5.py), and returns adc_valid.
//        The raw decisions come from the ADC netlist (decoded in views/sch.inc), not from this model.
//     b. cur_trk: the ctrl 'soon' window (GUARD ticks before the PWM-centre strobe), taken by hierarchical
//        reference. The shared CDAC top plate must track ISA/ISB before the strobe; no pin carries this today.
//     c. isense auto-zero mapping: azh = az_win, az = az_win stretched by 2 ticks (azh falls first, as the
//        r1_isense block decks).
//  3. Testbench monitors ($display lines parsed by tb/post.py). They read, they do not drive.
// Port order is the d_cosim order (inputs first, then outputs; vectors MSB first).
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module r1_chip_dig (
    input  wire        clk, por_n, tb_rst_n,
    input  wire        cs_n, ma_sclk, sdi, en_pad,
    input  wire [3:0]  cmp,
    input  wire        t2f_clk,
    input  wire        adc_valid_a,
    input  wire [13:0] adc_raw_a,
    input  wire        adc_valid_b,
    input  wire [13:0] adc_raw_b,
    output wire        slo_sdo, fault_n, gate_a, gate_b, gate_c,
    output wire        adc_hold, is_smp, adc_start, adc_sel,
    output wire [31:0] tap_p, tap_n,
    output wire        az_a, azh_a, az_b, azh_b,
    output wire [4:0]  osc_trim,
    output wire [3:0]  pga_c,
    output wire        t2f_en, t2f_mode, bias_en,
    // sequencer model outputs (to the r1_adc sch view through global nodes)
    output wire        trka0, trka1, trkb0, trkb1,
    output reg         win, lat,
    output reg  [13:0] stb,
    output reg         seq_valid,
    output wire        cur_trk
);
`ifndef T10_TEST
`define T10_TEST 1
`endif
`ifndef T10_STALL_TICKS
`define T10_STALL_TICKS 60
`endif
`ifndef T10_SEQ_LAT
`define T10_SEQ_LAT 1.14
`endif
    // Deck 1: the macro reset is the r1_bias por_n (the real path). Decks 2-5 (deviation D2, tb/README.md): the POR delay
    // (about 240 us) does not fit the wall-time budget, so the macro reset is the testbench pulse tb_rst_n only.
    wire por_eff = ((`T10_TEST == 1) ? por_n : 1'b1) & tb_rst_n;
    wire az_win;
    // Finding F22 (open issue O10): the valid pulse of the sequencer model was lost on its way out through the
    // d_cosim output bridge (run t10-diag-hs-f19-b: Verilog seq_valid rose at 3945.6 ns, the analog seq_valid did not),
    // and the ctrl frame then waited for ever. The valid is a MODEL signal (M1) of this macro, so the ctrl now takes it
    // inside the macro. The analog adc_valid_a/b nets stay for observation; -DT10_VALID_BRIDGE restores the old path.
`ifdef T10_VALID_BRIDGE
    wire va_ctrl = adc_valid_a, vb_ctrl = adc_valid_b;
`else
    wire va_ctrl = seq_valid, vb_ctrl = seq_valid;
`endif
    r1_ctrl_top u_ctrl (
        .clk(clk), .por_n(por_eff), .cs_n(cs_n), .ma_sclk(ma_sclk), .sdi(sdi), .slo_sdo(slo_sdo),
        .en_pad(en_pad), .fault_n(fault_n), .gate_a(gate_a), .gate_b(gate_b), .gate_c(gate_c),
        .adc_hold(adc_hold), .is_smp(is_smp), .adc_start(adc_start), .adc_sel(adc_sel),
        .adc_valid_a(va_ctrl), .adc_raw_a(adc_raw_a), .adc_valid_b(vb_ctrl), .adc_raw_b(adc_raw_b),
        .cmp(cmp), .tap_p(tap_p), .tap_n(tap_n), .az_win(az_win), .t2f_clk(t2f_clk),
        .osc_trim(osc_trim), .pga_c(pga_c), .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bias_en(bias_en));

    // ---- 2c. isense auto-zero mapping (MODEL) ----
    reg [1:0] azd;
    always @(posedge clk or negedge por_eff)
        if (!por_eff) azd <= 2'b00; else azd <= {azd[0], az_win};
    assign azh_a = az_win;
    assign azh_b = az_win;
    assign az_a  = az_win | azd[0] | azd[1];
    assign az_b  = az_a;

    // ---- 2b. current-frame track request (MODEL of a missing port) ----
    reg cur_q;
    always @(posedge clk or negedge por_eff)
        if (!por_eff) cur_q <= 1'b0; else cur_q <= u_ctrl.u_gate.soon;
    assign cur_trk = cur_q;

    // ---- 2a. ADC sequencer model (MODEL), r1_adc revision-5 D18 timing ----
    real per, lastt, t0;
    initial begin per = 33.333; lastt = 0.0; win = 1'b0; lat = 1'b0; stb = 14'd0; seq_valid = 1'b0; end
`ifdef T10_SEQ_F19
    // reproduction only (O10): the reverted F19 change (period filter, delays clamped at zero)
    always @(posedge clk) begin if ($realtime - lastt > 20.0) per = $realtime - lastt; lastt = $realtime; end
    function real nn; input real x; nn = (x > 0.0) ? x : 0.0; endfunction
`else
    always @(posedge clk) begin per = $realtime - lastt; lastt = $realtime; end
    function real nn; input real x; nn = x; endfunction
`endif
    reg enc_busy = 1'b0, cur_busy = 1'b0, released = 1'b1;
    integer nseq = 0;
    real pc;
    real ckt [0:7];
    real ck8 = 0.0;
    integer cki = 0;
    // time of the oldest of the last 8 clock edges, 7 periods before the newest (F23b)
    always @(posedge clk) begin ckt[cki] = $realtime; cki = (cki + 1) % 8; ck8 = (ckt[cki] > 0.0) ? ckt[cki] : 0.0; end
    function real nn2; input real x; nn2 = (x > 0.0) ? x : 0.0; endfunction
    integer k;
    integer nclkbad = 0;
    real lastc = 0.0;
    // monitor (F23): a clk period outside 30..37 ns means that the shim delivered a clock edge twice, late or not at all
    always @(posedge clk) begin
        if (lastc > 0.0 && ($realtime - lastc < 30.0 || $realtime - lastc > 37.0) && nclkbad < 20) begin
            nclkbad = nclkbad + 1;
            $display("T10MON CLKPER t=%0.3f per=%0.3f n=%0d", $realtime, $realtime - lastc, nclkbad); $fflush;
        end
        lastc = $realtime;
    end
    always @(posedge adc_start) begin : seq
        #0.01;
        t0 = $realtime - 0.01;
        // F23: the period is frozen at the start of the conversion and limited to 20..50 ns, and every delay is
        // limited at zero in nn2. A clock edge that the shim delivers twice or late changed per inside the loop;
        // a negative delay is a very long delay in Icarus, and the sequencer then stopped (run t10-t4-safe-vb-a).
        // F23b: mean of the last 7 clock periods (8 stored edges); one clock edge that the shim delivers late (0.34 ns seen in the
        // subset decks) moved all 14 strobes by up to 4.7 ns when one period was used (t10-t5-sub-27-vb-b)
        pc = (ck8 > 0.0) ? ($realtime - 0.01 - ck8) / 7.0 : per;
        pc = (pc > 20.0 && pc < 50.0) ? pc : 33.333;
        nseq = nseq + 1;
        $display("T10HS SEQ t0=%0.3f per=%0.3f sel=%0d n=%0d", t0, per, adc_sel, nseq); $fflush;
        if (adc_sel) cur_busy = 1'b1; else enc_busy = 1'b1;
        released = 1'b0;
        #(nn2(t0 + 1.0 - $realtime)) win = 1'b1;
        // The strobes must reach the ADC 0.6 ns before the clk30 edge. adc_start (and every output of this
        // macro) reaches the analog side about `T10_SEQ_LAT ns after the clk30 edge (d_cosim output latency plus
        // the clock-to-adc_start path; measured in run t10-diag-t2enc-a: 1.14 ns). Without this correction the
        // strobes came 0.54 ns after the edge and the SAR did not converge (finding R2, testbench bug).
        for (k = 0; k < 14; k = k + 1) begin
            #(nn2(t0 + (k + 1) * pc - 0.6 - `T10_SEQ_LAT - $realtime)) stb[k] = 1'b1;
            #0.3 stb[k] = 1'b0;
        end
        #(nn2(t0 + 14 * pc + 0.5 - `T10_SEQ_LAT - $realtime)) lat = 1'b1;
        released = 1'b1; enc_busy = 1'b0; cur_busy = 1'b0;
        #0.5 win = 1'b0;
        #0.5 lat = 1'b0;
        #(nn2(t0 + 14 * pc + 5.0 - $realtime)) seq_valid = 1'b1;
        $display("T10HS SVAL1 t=%0.3f per=%0.3f n=%0d", $realtime, per, nseq); $fflush;
        #(pc) seq_valid = 1'b0;
        $display("T10HS SVAL0 t=%0.3f", $realtime); $fflush;
    end
    // a hold that is not a conversion (bootstrap pre-charge, 2 ticks) keeps the inputs in hold
    always @(negedge adc_hold or negedge is_smp) if (!adc_hold && !is_smp && !enc_busy && !cur_busy) released = 1'b1;
    always @(posedge adc_hold) if (!adc_start) released = 1'b0;     // pre-charge hold (no adc_start)
    wire hold_act = (adc_hold | is_smp) & ~released;
    wire t0_on = ~hold_act & ~enc_busy & ~cur_busy & ~cur_q;
    wire t1_on = ~hold_act & ~enc_busy & ~cur_busy &  cur_q;
    // rise / fall delays as gen_timing_r5.py: track rises 6 ns after the event (slice B +1.5 ns), falls 0.3 ns
    // after the clock edge (clock-to-q); in1 rises 1 ns after in0 falls (break before make)
    assign #(6.0, 0.3) trka0 = t0_on;
    assign #(7.5, 0.3) trkb0 = t0_on;
    assign #(6.0, 0.3) trka1 = t1_on;
    assign #(7.5, 0.3) trkb1 = t1_on;


    // ---- 3b. ADC handshake monitors (open issue O10) ----
    // Per conversion: the ctrl start, the valid pulses as the ctrl macro sees them (after the bridges), the clock
    // edges on which the ctrl samples them, and the frame end. A frame that stays open for more than STALL_TICKS
    // ticks prints T10MON STALL; run_tb.py --stall-abort stops ngspice when it reads that line.
    integer nva = 0, nvb = 0, nfr = 0, open_t = 0;
    reg stall_done = 1'b0;
    always @(posedge adc_valid_a) begin nva = nva + 1; $display("T10HS VA1 t=%0.3f n=%0d raw=%0d", $realtime, nva, adc_raw_a); $fflush; end
    always @(negedge adc_valid_a) begin $display("T10HS VA0 t=%0.3f", $realtime); $fflush; end
    always @(posedge adc_valid_b) begin nvb = nvb + 1; $display("T10HS VB1 t=%0.3f n=%0d raw=%0d", $realtime, nvb, adc_raw_b); $fflush; end
    always @(negedge adc_valid_b) begin $display("T10HS VB0 t=%0.3f", $realtime); $fflush; end
    always @(posedge clk) begin
        if (u_ctrl.u_gate.adc_start) begin
            nfr = nfr + 1;
            $display("T10HS CSTART t=%0.3f sel=%0d frame=%0d", $realtime, u_ctrl.u_gate.adc_sel, nfr); $fflush;
        end
        if (u_ctrl.u_gate.conv && (u_ctrl.u_gate.adc_valid_a || u_ctrl.u_gate.adc_valid_b))
            begin $display("T10HS CSEEN t=%0.3f va=%0d vb=%0d got_a=%0d got_b=%0d", $realtime,
                     u_ctrl.u_gate.adc_valid_a, u_ctrl.u_gate.adc_valid_b, u_ctrl.u_gate.got_a, u_ctrl.u_gate.got_b); $fflush; end
        if (u_ctrl.u_gate.conv) open_t = open_t + 1; else open_t = 0;
        if (open_t == `T10_STALL_TICKS && !stall_done) begin
            stall_done = 1'b1;
            $display("T10MON STALL t=%0.3f frame=%0d open=%0d ticks got_a=%0d got_b=%0d nva=%0d nvb=%0d nseq=%0d seq_valid=%0d va_in=%0d vb_in=%0d",
                     $realtime, nfr, open_t, u_ctrl.u_gate.got_a, u_ctrl.u_gate.got_b, nva, nvb, nseq, seq_valid, adc_valid_a, adc_valid_b);
            $fflush;
        end
    end
    // lost-event detector: a valid pulse of the model that does not come back through the analog path within 20 ns
    integer nlost = 0;
    always @(posedge seq_valid) begin : lostchk
        integer na0; na0 = nva;
        #20.0;
        if (nva == na0) begin nlost = nlost + 1; $display("T10MON LOSTEV t=%0.3f signal=seq_valid n=%0d", $realtime - 20.0, nlost); $fflush; end
    end
    // ---- 3. monitors ----
    always @(posedge clk) begin
        if (u_ctrl.u_gate.smp_valid)
            $display("T10MON ENC t=%0.1f sin=%0d cos=%0d pos=%0d meas=%0d turns=%0d vel=%0d valid=%0d",
                     $realtime, u_ctrl.u_gate.sin_code, u_ctrl.u_gate.cos_code, u_ctrl.pos_out,
                     u_ctrl.meas_angle, $signed(u_ctrl.turns), $signed(u_ctrl.velocity), u_ctrl.pos_valid);
        if (u_ctrl.u_gate.adc_valid_a && u_ctrl.u_gate.adc_sel)
            $display("T10MON CURRAW t=%0.1f rawa=%0d rawb=%0d", $realtime, adc_raw_a, adc_raw_b);
        if (u_ctrl.u_gate.u_wa.code_valid && u_ctrl.u_gate.tag_a)
            $display("T10MON CUR t=%0.1f code_a=%0d", $realtime, u_ctrl.u_gate.u_wa.code);
    end
    always @(posedge clk) begin
        if (u_ctrl.meas_stb)
            $display("T10MON MEAS t=%0.3f meas=%0d pos=%0d valid=%0d", $realtime, u_ctrl.meas_angle, u_ctrl.pos_out, u_ctrl.pos_valid);
        if (adc_start)
            $display("T10MON START t=%0.3f sel=%0d", $realtime, adc_sel);
    end
    integer nt2f = 0, nt2fs = 0;
    always @(posedge t2f_clk) nt2f = nt2f + 1;
    always @(posedge u_ctrl.u_safe.t2f_s) nt2fs = nt2fs + 1;
    // progress, 1 us; with the T2F edges seen at the macro input and after the ctrl synchroniser (test 5 check)
    initial forever begin #1000; $display("T10MON PROGRESS t=%0.0f t2f_in=%0d t2f_sync=%0d temp=%0d", $realtime, nt2f, nt2fs, u_ctrl.u_safe.temp); $fflush; end
    reg fault_d = 1'b0;
    always @(posedge clk) begin
        if (fault_n === 1'b0 && fault_d == 1'b0) $display("T10MON FAULT t=%0.1f cause=%h", $realtime, u_ctrl.cause);
        fault_d <= (fault_n === 1'b0);
    end
    always @(posedge por_eff) $display("T10MON RESET_RELEASE t=%0.1f", $realtime);
    always @(negedge u_ctrl.rst_n) $display("T10MON RESET_ASSERT t=%0.1f", $realtime);
    always @(posedge u_ctrl.rst_n) $display("T10MON CORE_OUT_OF_RESET t=%0.1f", $realtime);
    always @(posedge u_ctrl.u_regs.wr) $display("T10MON REGWR t=%0.1f addr=%h data=%h", $realtime, u_ctrl.u_regs.addr, u_ctrl.u_regs.wdata);
endmodule
