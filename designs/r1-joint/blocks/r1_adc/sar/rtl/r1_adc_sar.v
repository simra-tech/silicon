// r1_adc_sar: SAR logic and frame sequencer of r1_adc, standard-cell sub-macro (PLAN.md decision D21, track T2j).
//
// Function (sar/README.md "Specification"): the silicon form of the behavioural XSPICE cell r1_sar5_logic
// (schematic/r1_adc_r5.spice) plus the frame sequencer that the r5 decks take from ideal sources
// (sim/r5/gen_timing_r5.py) and the full-chip testbench takes from a model (r1_top/tb/rtl/r1_chip_dig.v, 2a).
// Inputs from r1_ctrl (D18 frame protocol, r1_gate): adc_hold / is_smp (hold while high), adc_start (one-tick
// pulse), adc_sel (not needed: the input is chosen at track time), cur_trk (new, open issue S1: the next frame is
// a current frame, track ISA/ISB). Outputs to r1_ctrl: 14 raw decisions per slice (raw[13] = first decision)
// and a one-tick valid pulse per slice.
// South side: comparator outputs (oap/obp: r1_cmp4, decisions 1-13; oanp/obnp: r1_cmp5n, decision 0), the
// comparator one-shot mclk (r1_cmp4_clkgen, low = reset for 0.9-2.3 ns after each clk rising edge), comparator
// clocks, 13 P and 13 N CDAC driver lines per slice, track switches in0 (SIN/COS) and in1 (ISA/ISB).
//
// Timing (E0 = the clk edge at which r1_ctrl raises adc_start and adc_hold or is_smp; En = E0 + n ticks):
//   * the CDAC holds when adc_hold / is_smp rises (combinational, about E0 + ctrl clock-to-q);
//   * decision 0 is evaluated in tick 0 (win opens on the delayed hold), decision k in tick k;
//   * decision k is taken at E(k+1): a level latch per comparator, transparent while its comparator clock
//     evaluates, closes when the comparator clock falls (the one-shot at E(k+1)), and the decision flip-flops
//     load the latch output at E(k+1); the CDAC lines of decision k switch at E(k+1) + clock-to-output;
//   * decision 13 (no CDAC line) at E14: valid high for one tick (E14..E15), win closes, the CDAC lines return
//     to 0 and the track switch of the selected input closes (early release, as the behavioural decks);
//   * raw holds the decisions until E16; the flags clear at E16 (r1_ctrl samples raw with valid at E15).
// Rule of the behavioural model kept: P <= comparator output at the decision, N = V AND NOT P; a comparator
// with no output (both outputs below the logic threshold) gives P = 0, so the N side switches.
// No glitch on a CDAC line: every line is a flip-flop output ANDed with busy, and at every edge at most one of
// the two inputs of each AND changes, or both change in the same direction (README "Glitch analysis").
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module r1_adc_sar (
    // north edge: r1_ctrl
    input  wire        clk,            // oscillator clock (the same net as r1_ctrl clk and the ADC clkgen)
    input  wire        por_n,          // power-on reset, low = reset (asynchronous assert, synchronised release)
    input  wire        adc_hold,       // SIN/COS hold request (high = hold)
    input  wire        is_smp,         // ISA/ISB hold request (high = hold)
    input  wire        adc_start,      // one-tick pulse: both slices convert
    input  wire        adc_sel,        // frame type (not used inside; dummy load only)
    input  wire        cur_trk,        // 1: track in1 (ISA/ISB) while idle; 0: track in0 (SIN/COS)
    output wire        adc_valid_a,
    output wire [13:0] adc_raw_a,
    output wire        adc_valid_b,
    output wire [13:0] adc_raw_b,
    // south edge: ADC slices
    input  wire        mclk,           // comparator one-shot, low = reset
    input  wire        oap, oan,       // slice A r1_cmp4 outputs (oan: dummy load)
    input  wire        oanp, oann,     // slice A r1_cmp5n outputs (oann: dummy load)
    input  wire        obp, obn,       // slice B r1_cmp4 outputs (obn: dummy load)
    input  wire        obnp, obnn,     // slice B r1_cmp5n outputs (obnn: dummy load)
    output wire        clka, clkab, clkna, clknab,
    output wire        clkb, clkbb, clknb, clknbb,
    output wire [12:0] cpa, cna, cpb, cnb,
    output wire        trka0, trka1, trkb0, trkb1
);
    // ---------------- reset synchroniser ----------------
    reg [1:0] rs;
    always @(posedge clk or negedge por_n)
        if (!por_n) rs <= 2'b00; else rs <= {rs[0], 1'b1};
    wire rst_n = rs[1];

    // ---------------- sequencer (shared by both slices; D18: both slices on one adc_start) ----------------
    wire       hs = adc_hold | is_smp;
    reg        busy;                   // decisions 1..13 pending; also enables the CDAC lines
    reg  [3:0] step;                   // next decision to take (1..13)
    reg        done_q;                 // conversion complete, hold not yet released by r1_ctrl
    reg        va, vb;                 // valid pulses
    reg        vd;                     // valid delayed by one tick: clears the flags at E16
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy <= 1'b0; step <= 4'd0; done_q <= 1'b0; va <= 1'b0; vb <= 1'b0; vd <= 1'b0;
        end else begin
            va <= 1'b0; vb <= 1'b0; vd <= va;
            if (adc_start) begin
                busy <= 1'b1; step <= 4'd1; done_q <= 1'b0;
            end else if (busy) begin
                step <= step + 4'd1;
                if (step == 4'd13) begin busy <= 1'b0; done_q <= 1'b1; va <= 1'b1; vb <= 1'b1; end
            end else if (!hs) begin
                done_q <= 1'b0;
            end
        end
    end
    assign adc_valid_a = va;
    assign adc_valid_b = vb;

    // input selection, break before make (one tick with neither input selected)
    reg sel0, sel1;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin sel0 <= 1'b1; sel1 <= 1'b0; end
        else begin sel0 <= ~cur_trk & ~sel1; sel1 <= cur_trk & ~sel0; end

    // CDAC hold: from the request edge (combinational) until the last decision; then early release
    wire hold_int = busy | (hs & ~done_q);
    assign trka0 = ~hold_int & sel0;
    assign trka1 = ~hold_int & sel1;
    assign trkb0 = ~hold_int & sel0;
    assign trkb1 = ~hold_int & sel1;

    // comparator window: opens on the delayed hold request of a conversion (adc_start), after the track switch has
    // opened; held by busy from E1; closes at E14. A hold without adc_start (bootstrap pre-charge) opens no window.
    // At E1 adc_start falls and busy rises; a gap between them is masked while mclk is low (the one-shot reset),
    // which holds if clk -> busy is shorter than the one-shot width, the same bound as the CDAC lines (README).
    wire hsd;
`ifdef SYNTHESIS
    wire hsd1;
    sg13g2_dlygate4sd3_1 u_dly_hs1 (.A(hs),   .X(hsd1));
    sg13g2_dlygate4sd3_1 u_dly_hs2 (.A(hsd1), .X(hsd));
`else
    assign #0.8 hsd = hs;
`endif
    // Window-gate flip-flops (T2j, run t2j-sta-e-b): the comparator clock gates must see busy and the decision-0
    // flag change before mclk rises again (one-shot width after the edge, 0.91 ns at ff). busy and the flags
    // drive large fan-outs, so the gates take dedicated copies: wq = next busy, fv0 = next (P0 | N0) (equal for
    // both slices). Instantiated (keep) so that synthesis does not merge them with busy and the flags.
    wire wq, fv0;
    wire wq_d  = adc_start | (busy & (step != 4'd13));
    wire fv0_d = adc_start | (fv0 & ~vd);
`ifdef SYNTHESIS
    (* keep *) sg13g2_dfrbpq_2 u_wq  (.CLK(clk), .RESET_B(rst_n), .D(wq_d),  .Q(wq));
    (* keep *) sg13g2_dfrbpq_2 u_fv0 (.CLK(clk), .RESET_B(rst_n), .D(fv0_d), .Q(fv0));
`else
    reg wq_r, fv0_r;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin wq_r <= 1'b0; fv0_r <= 1'b0; end
        else begin wq_r <= wq_d; fv0_r <= fv0_d; end
    assign wq = wq_r; assign fv0 = fv0_r;
`endif
    wire win = hsd & (adc_start | wq);

    // ---------------- decision flags, one set per slice ----------------
    reg  [13:0] fpa, fpb;              // P flags of decisions 0..13 (13: raw only)
    reg  [12:0] fna, fnb;              // N flags of decisions 0..12

    // comparator clocks (evaluate while high); decision 0 comparator only until decision 0 is taken
    wire clka_i  = mclk & win;
    wire clkb_i  = mclk & win;
    wire clkna_i = mclk & win & ~fv0;
    wire clknb_i = mclk & win & ~fv0;
    assign clka  = clka_i;   assign clkab  = ~clka_i;
    assign clkb  = clkb_i;   assign clkbb  = ~clkb_i;
    assign clkna = clkna_i;  assign clknab = ~clkna_i;
    assign clknb = clknb_i;  assign clknbb = ~clknb_i;

    // decision latches: transparent while the comparator evaluates, closed from the clock fall (comparator reset)
    wire lpa, lpb, lna, lnb;
`ifdef SYNTHESIS
    sg13g2_dlhq_1 u_lat_pa (.D(oap),  .GATE(clka_i),  .Q(lpa));
    sg13g2_dlhq_1 u_lat_pb (.D(obp),  .GATE(clkb_i),  .Q(lpb));
    sg13g2_dlhq_1 u_lat_na (.D(oanp), .GATE(clkna_i), .Q(lna));
    sg13g2_dlhq_1 u_lat_nb (.D(obnp), .GATE(clknb_i), .Q(lnb));
`else
    reg lpa_r, lpb_r, lna_r, lnb_r;
    always @* if (clka_i)  lpa_r = oap;
    always @* if (clkb_i)  lpb_r = obp;
    always @* if (clkna_i) lna_r = oanp;
    always @* if (clknb_i) lnb_r = obnp;
    assign lpa = lpa_r; assign lpb = lpb_r; assign lna = lna_r; assign lnb = lnb_r;
`endif

    // next state per flag: load at its decision edge, clear at E16 (vd), hold otherwise. Decision 0 loads when
    // adc_start is seen. The other flags are not cleared by adc_start: they are 0 since E16 of the previous
    // conversion (r1_gate starts the next frame at E16 at the earliest, seen here at E17); clearing them at E1
    // would also race with busy on the CDAC lines.
    wire [13:0] cap;
    assign cap[0] = adc_start;
    genvar g;
    generate for (g = 1; g <= 13; g = g + 1) begin : g_cap
        assign cap[g] = busy & (step == g);
    end endgenerate
    wire [13:0] dpa = {{13{lpa}}, lna}, dpb = {{13{lpb}}, lnb};
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fpa <= 14'd0; fna <= 13'd0; fpb <= 14'd0; fnb <= 13'd0;
        end else begin
            fpa <= (cap & dpa) | (~cap & fpa & {14{~vd}});
            fpb <= (cap & dpb) | (~cap & fpb & {14{~vd}});
            fna <= (cap[12:0] & ~dpa[12:0]) | (~cap[12:0] & fna & {13{~vd}});
            fnb <= (cap[12:0] & ~dpb[12:0]) | (~cap[12:0] & fnb & {13{~vd}});
        end
    end

    // CDAC lines: decision k drives bottom plate 12 - k (cp12 = first decision), enabled while busy. Lines 11..0:
    // the flag rises at its decision edge while busy is already high, and busy falls at E14 after the last
    // decision, so only flag -> line is timing-critical. Line 12: flag 0 and busy rise at the same edge (E1), so
    // it takes the low-fan-out copy wq (= busy) for its enable.
    assign cpa[12] = fpa[0] & wq;
    assign cna[12] = fna[0] & wq;
    assign cpb[12] = fpb[0] & wq;
    assign cnb[12] = fnb[0] & wq;
    generate for (g = 1; g <= 12; g = g + 1) begin : g_cdac
        assign cpa[12 - g] = fpa[g] & busy;
        assign cna[12 - g] = fna[g] & busy;
        assign cpb[12 - g] = fpb[g] & busy;
        assign cnb[12 - g] = fnb[g] & busy;
    end endgenerate

    // raw decisions: raw[13] = decision 0 ... raw[0] = decision 13
    generate for (g = 0; g <= 13; g = g + 1) begin : g_raw
        assign adc_raw_a[13 - g] = fpa[g];
        assign adc_raw_b[13 - g] = fpb[g];
    end endgenerate

    // ---------------- dummy loads: the complementary comparator outputs see the same input as the used ones ----------------
`ifdef SYNTHESIS
    (* keep *) wire nc_oan, nc_oann, nc_obn, nc_obnn, nc_sel;
    (* keep *) sg13g2_buf_1 u_ld_oan  (.A(oan),     .X(nc_oan));
    (* keep *) sg13g2_buf_1 u_ld_oann (.A(oann),    .X(nc_oann));
    (* keep *) sg13g2_buf_1 u_ld_obn  (.A(obn),     .X(nc_obn));
    (* keep *) sg13g2_buf_1 u_ld_obnn (.A(obnn),    .X(nc_obnn));
    (* keep *) sg13g2_buf_1 u_ld_sel  (.A(adc_sel), .X(nc_sel));
`endif
endmodule
