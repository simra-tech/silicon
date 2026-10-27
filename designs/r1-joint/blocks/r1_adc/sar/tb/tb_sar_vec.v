// tb_sar_vec.v -- T2j (D21): r1_adc_sar (RTL, or the gate-level netlist with -DGL and SDF) on comparator vectors
// extracted from a behavioural full-core run (sar/tb/vec_extract.py). The ctrl side is a model of the r1_gate
// frame protocol (D18; r1_ctrl/rtl/r1_gate.v): adc_start one tick and adc_hold (encoder) or is_smp (current) from
// the frame start edge, release at the edge on which both valid pulses are seen, cur_trk from 10 ticks before a
// current frame to one tick after its start (model of the missing ctrl port, open issue S1), one bootstrap
// pre-charge hold of 2 ticks (no adc_start) after the reset release, as r1_gate PRE_HOLD.
// All ctrl outputs change CQ ns after the clk edge (default 0.3 ns, the _cq timing of the r5 decks).
// Output: every change of a DUT output is written to OUT as "t_ps hex" (sar/tb/compare.py reads it).
// Defines: CASE (vector case name, quoted path prefix), OUT (output file), GL (gate level: the LibreLane nl.v
// netlist, no supply pins), SDF (sdf file), CQ.
`timescale 1ns/1ps
`ifndef CQ
`define CQ 0.3
`endif

module tb_sar_vec;
    reg  clk = 1'b0, por_n = 1'b0;
    reg  adc_hold = 1'b0, is_smp = 1'b0, adc_start = 1'b0, adc_sel = 1'b0, cur_trk = 1'b0;
    reg  mclk, oap, oan, oanp, oann, obp, obn, obnp, obnn;
    wire adc_valid_a, adc_valid_b;
    wire [13:0] adc_raw_a, adc_raw_b;
    wire clka, clkab, clkna, clknab, clkb, clkbb, clknb, clknbb;
    wire [12:0] cpa, cna, cpb, cnb;
    wire trka0, trka1, trkb0, trkb1;

    r1_adc_sar dut (
        .clk(clk), .por_n(por_n), .adc_hold(adc_hold), .is_smp(is_smp), .adc_start(adc_start), .adc_sel(adc_sel),
        .cur_trk(cur_trk), .adc_valid_a(adc_valid_a), .adc_raw_a(adc_raw_a), .adc_valid_b(adc_valid_b),
        .adc_raw_b(adc_raw_b), .mclk(mclk), .oap(oap), .oan(oan), .oanp(oanp), .oann(oann), .obp(obp), .obn(obn),
        .obnp(obnp), .obnn(obnn), .clka(clka), .clkab(clkab), .clkna(clkna), .clknab(clknab), .clkb(clkb),
        .clkbb(clkbb), .clknb(clknb), .clknbb(clknbb), .cpa(cpa), .cna(cna), .cpb(cpb), .cnb(cnb),
        .trka0(trka0), .trka1(trka1), .trkb0(trkb0), .trkb1(trkb1));

`ifdef SDF
    initial $sdf_annotate(`SDF, dut, , , "MAXIMUM");
`endif

`include `SCHED
`include `STIM

    // clk30 as the r5 timing includes: rising edges at n T (+ 25 ps to the 0.6 V crossing), 50 % duty
    real T = 1000.0 / 30.0;
    integer n = 0;
    initial begin
        #(T + 0.025);
        forever begin clk = 1'b1; n = n + 1; #(T / 2.0); clk = 1'b0; #(T / 2.0); end
    end
    // reset release at 50 ns (before clk edge 2)
    initial #50 por_n = 1'b1;

    // ctrl frame protocol model
    integer f = 0, i;
    reg conv = 1'b0;
    always @(posedge clk) begin
        adc_start <= #(`CQ) 1'b0;
        if (n == 3) adc_hold <= #(`CQ) 1'b1;            // pre-charge hold, 2 ticks
        if (n == 5) adc_hold <= #(`CQ) 1'b0;
        if (conv && adc_valid_a && adc_valid_b) begin
            adc_hold <= #(`CQ) 1'b0; is_smp <= #(`CQ) 1'b0; conv = 1'b0;
        end
        if (f < NFR && n == fr_tick[f]) begin
            adc_start <= #(`CQ) 1'b1; adc_sel <= #(`CQ) fr_type[f];
            if (fr_type[f]) is_smp <= #(`CQ) 1'b1; else adc_hold <= #(`CQ) 1'b1;
            conv = 1'b1; f = f + 1;
        end
        // cur_trk: from 10 ticks before a current frame to one tick after its start
        cur_trk <= #(`CQ) 1'b0;
        for (i = 0; i < NFR; i = i + 1)
            if (fr_type[i] && n >= fr_tick[i] - 10 && n <= fr_tick[i]) cur_trk <= #(`CQ) 1'b1;
    end

    // output log
    wire [93:0] obus = {adc_valid_a, adc_valid_b, adc_raw_a, adc_raw_b, clka, clkab, clkna, clknab, clkb, clkbb, clknb,
                        clknbb, trka0, trka1, trkb0, trkb1, cpa, cna, cpb, cnb};
    integer fo;
    initial begin
        fo = $fopen(`OUT, "w");
        $fdisplay(fo, "# order: va vb raw_a[13:0] raw_b[13:0] clka clkab clkna clknab clkb clkbb clknb clknbb trka0 trka1 trkb0 trkb1 cpa[12:0] cna[12:0] cpb[12:0] cnb[12:0] | ctrl: hold smp start cur");
        #(TEND_PS / 1000.0);
        $fclose(fo);
        $finish;
    end
    always @(obus or adc_hold or is_smp or adc_start or cur_trk)
        $fdisplay(fo, "%0d %b %b%b%b%b", $rtoi($realtime * 1000.0), obus, adc_hold, is_smp, adc_start, cur_trk);
endmodule
