// Red-team review 2026-09-25: targeted hazard tests for g1_digital (RTL or
// gate-level netlist). Written for designs/g1-guardian/review/redteam-20260925/DIGITAL.md.
// Nothing here modifies the design or the existing testbenches.
//
// Environment models follow tb_g1_digital.v (blocks/g1_trip/INTERFACE.md):
//   comparators latch over_soft / over_hard on the rising / falling cmp_clk edge,
//   dynamic: no cmp_clk edge = no decision, output held;
//   G1_GATE latch: set = trip_d | (cmp_hard & fast_en), reset = !en | clr_d.
// Difference: the oscillator model runs only while osc_en === 1 (G1_OSC en pin),
// and por_n is tied 1 as on the chip (canonical CDL: sg13g2_tiehi).
//
// Result convention: "check" lines state the behaviour the register map or the
// top-level specification promises. A FAIL line is therefore evidence that the
// hazard is real. "OBSERVE" lines report behaviour outside the documented
// operating contract without judging it.
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module tb_redteam;
    localparam real OSC_T  = 100.0;
    real            SCLK_T = 200.0;

    reg        osc_clk = 0;
    reg        en      = 1;          // worst case for R1: EN high from power-up
    reg        sclk    = 0;
    reg        sdi     = 0;
    wire       sdo;
    reg        cmp_soft = 0;
    reg        cmp_hard = 0;
    wire       cmp_clk, trip_d, clr_d, fast_en;
    wire [7:0] dac_soft, dac_hard;
    wire       trip_set_sel, trip, gate_en, fault_n, clk_div_out;
    wire [1:0] trip_cause;
    wire       osc_en, t2f_en, t2f_mode, bgr_r4;
    wire [3:0] osc_trim;

    reg over_soft = 0, over_hard = 0;
    always @(posedge cmp_clk) cmp_soft <= #1 over_soft;
    always @(negedge cmp_clk) cmp_hard <= #1 over_hard;
    reg  latch_a = 0;
    wire set_a = trip_d | (cmp_hard & fast_en);
    wire rst_a = ~en | clr_d;
    always @* begin
        if (rst_a)           latch_a = 1'b0;
        else if (set_a === 1'b1) latch_a = 1'b1;
    end
    wire tripped = latch_a;
    wire gate_pad = en & ~latch_a;   // G1_GATE: gate_core = en_core & !tripped

    g1_digital dut (
        .osc_clk(osc_clk), .por_n(1'b1), .en(en),
        .sclk(sclk), .sdi(sdi), .sdo(sdo),
        .cmp_clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(dac_soft), .dac_hard(dac_hard), .trip_set_sel(trip_set_sel),
        .trip_d(trip_d), .clr_d(clr_d), .fast_en(fast_en), .tripped(tripped),
        .trip(trip), .gate_en(gate_en), .fault_n(fault_n), .trip_cause(trip_cause),
        .osc_en(osc_en), .osc_trim(osc_trim),
        .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bgr_r4(bgr_r4),
        .clk_div_out(clk_div_out));

    // G1_OSC: runs only while enabled (stops low)
    always #(OSC_T/2) osc_clk = (osc_en === 1'b1) ? ~osc_clk : 1'b0;

    integer errors = 0, checks = 0, tests_pass = 0, tests_fail = 0, test_err;
    reg [8*96-1:0] test_name;
    task begin_test(input [8*96-1:0] name); begin test_name = name; test_err = errors; $display("---- %0s", name); end endtask
    task end_test;
        begin
            if (errors == test_err) begin tests_pass = tests_pass + 1; $display("PASS %0s", test_name); end
            else begin tests_fail = tests_fail + 1; $display("FAIL %0s  (FAIL = hazard reproduced)", test_name); end
        end
    endtask
    task check(input [8*80-1:0] what, input [31:0] got, input [31:0] exp);
        begin
            checks = checks + 1;
            if (got !== exp) begin errors = errors + 1; $display("  FAIL %0d us %0s: got 0x%0h expected 0x%0h", $time/1000, what, got, exp); end
            else $display("  ok   %0d us %0s = 0x%0h", $time/1000, what, got);
        end
    endtask
    task observe(input [8*80-1:0] what, input [63:0] v);
        $display("  OBSERVE %0d us %0s = %0b", $time/1000, what, v);
    endtask

    task sclk_pulse; begin #(SCLK_T/2) sclk = 1; #(SCLK_T/2) sclk = 0; end endtask
    task send_byte(input [7:0] b);
        integer k;
        begin for (k = 7; k >= 0; k = k - 1) begin sdi = b[k]; sclk_pulse; end sdi = 0; end
    endtask
    task ser_write(input [6:0] addr, input [7:0] data);
        begin send_byte({1'b0, addr}); send_byte(data); #(2000); end
    endtask
    task ser_read(input [6:0] addr, output [7:0] data);
        integer k;
        begin
            send_byte({1'b1, addr}); send_byte(8'h00);
            for (k = 7; k >= 0; k = k - 1) begin #(SCLK_T/2) sclk = 1; data[k] = sdo; #(SCLK_T/2) sclk = 0; end
            #(2000);
        end
    endtask
    task idle_resync; #(150*OSC_T); endtask          // > 128 osc cycles (register map 1.2)
    task wait_cycles(input integer n); begin repeat (n) @(posedge osc_clk); #1; end endtask
    task wait_trip(input integer max_cycles, output integer waited);
        begin waited = 0; while (trip !== 1'b1 && waited < max_cycles) begin @(posedge osc_clk); #1; waited = waited + 1; end end
    endtask
    task en_cycle; begin en = 0; #(10*OSC_T); en = 1; #(130*OSC_T); end endtask

    reg  [7:0] d8, st_before;
    integer    w;

    initial begin
        // ============================================================
        begin_test("R1 reset: EN is the only reset; outputs defined before the first osc_clk edge");
        #(200);
        // EN high from power-up (outside contract P4): the reset synchroniser is never cleared
        observe("EN high at power-up: osc_en", osc_en);
        observe("EN high at power-up: dac_hard", dac_hard);
        observe("EN high at power-up: trip_d, clr_d, fast_en", {trip_d, clr_d, fast_en});
        observe("EN high at power-up: osc_clk edges seen (0 = oscillator never enabled)", osc_clk);
        // EN low (contract P4): every analog-facing output must be defined with no clock edge yet
        en = 0; #1;
        check("osc_en defined 1 before any clock",   osc_en,   1);
        check("osc_trim 8",                          osc_trim, 8);
        check("dac_soft 0x99",                       dac_soft, 8'h99);
        check("dac_hard 0xFE",                       dac_hard, 8'hFE);
        check("trip_d 0",                            trip_d,   0);
        check("clr_d 0",                             clr_d,    0);
        check("fast_en 0",                           fast_en,  0);
        check("cmp_clk 0",                           cmp_clk,  0);
        check("trip_set_sel 0",                      trip_set_sel, 0);
        check("t2f_en,t2f_mode,bgr_r4 = 1,0,0",      {t2f_en, t2f_mode, bgr_r4}, 3'b100);
        check("sdo 0",                               sdo,      0);
        check("gate_en 0 while EN low",              gate_en,  0);
        #(10*OSC_T); en = 1;
        // first rst_n release edge: count osc_clk edges until STATUS is readable
        #(130*OSC_T);
        ser_read(7'h00, d8); check("CHIP_ID after EN release", d8, 8'h47);
        end_test;

        // ============================================================
        begin_test("R2 INRUSH write after the mask expired must not re-open the mask (hard path)");
        en_cycle;
        ser_write(7'h08, 8'h01);                   // INRUSH = 512 cycles
        ser_write(7'h0B, 8'h02);                   // hard path only
        wait_cycles(700);
        ser_read(7'h0D, d8); check("STATUS.INRUSH_ACTIVE = 0 after 512 cycles", d8[3], 0);
        // host now reconfigures INRUSH for the next EN cycle (live write, breaker armed)
        ser_write(7'h08, 8'h14);
        ser_read(7'h0D, d8); check("STATUS.INRUSH_ACTIVE after live INRUSH write (spec: only after reset/re-enable)", d8[3], 0);
        over_hard = 1;
        wait_trip(12000, w);
        $display("  MEASURED hard-trip latency after live INRUSH write: %0d osc_clk cycles (spec 9..12)", w);
        check("hard trip within 20 cycles", (w <= 20), 1);
        over_hard = 0;
        ser_write(7'h0C, 8'h01);
        end_test;

        // ============================================================
        begin_test("R3 serial framing: one SCLK glitch or one mid-frame stall redirects writes silently");
        en_cycle;
        // (a) back-to-back frames (legal, register map 1.2) with one spurious rising edge before them
        sdi = 0; sclk = 1; #5; sclk = 0; #(SCLK_T/2);          // 5 ns glitch
        send_byte({1'b0, 7'h02}); send_byte(8'h50);            // host: DAC_SOFT = 0x50
        send_byte({1'b0, 7'h0B}); send_byte(8'h07);            // host: MODE = 0x07 (retrigger), back-to-back
        idle_resync;
        ser_read(7'h02, d8); check("DAC_SOFT as the host wrote it", d8, 8'h50);
        ser_read(7'h0B, d8); check("MODE as the host wrote it", d8, 8'h07);
        ser_read(7'h05, d8); check("SOFT_TIME_H untouched by the host", d8, 8'h00);
        observe("resulting soft window SOFT_TIME = {H,0x27} (units 25.6 us)", {d8, 8'h27});
        idle_resync;
        // (b) bit-banged host stalls 100 osc cycles (10 us) with SCLK low after the command byte
        en_cycle;
        send_byte({1'b0, 7'h03}); #(100*OSC_T); send_byte(8'h0B);  // host: DAC_HARD = 0x0B
        #(2000);
        send_byte({1'b0, 7'h02}); send_byte(8'h40);                // host: DAC_SOFT = 0x40
        idle_resync;
        ser_read(7'h03, d8); check("DAC_HARD as the host wrote it", d8, 8'h0B);
        ser_read(7'h0B, d8); check("MODE untouched by the host (0x03)", d8, 8'h03);
        end_test;

        // ============================================================
        begin_test("R4 OSC_EN = 0 (write or upset): FAST_EN path and serial status under a stopped clock");
        en_cycle;
        ser_write(7'h08, 8'h00);                   // no inrush mask
        ser_write(7'h0B, 8'h23);                   // soft + hard + FAST_EN
        ser_read(7'h00, d8); check("CHIP_ID", d8, 8'h47);
        ser_read(7'h0D, st_before); check("STATUS before", st_before, 8'h80);
        ser_write(7'h28, 8'h08);                   // OSC_EN = 0 (same effect as an upset of OSC_CTRL[4])
        #(1000);
        observe("osc_en", osc_en);
        observe("cmp_clk frozen at", cmp_clk);
        over_hard = 1;                             // hard overcurrent, far above threshold
        #(10000);                                  // 10 us: the top-level target
        check("G1_GATE latch set within 10 us (FAST_EN=1)", tripped, 1);
        check("GATE pad off within 10 us", gate_pad, 0);
        ser_read(7'h00, d8); check("CHIP_ID read under stopped clock", d8, 8'h47);
        ser_read(7'h0D, d8); observe("STATUS read under stopped clock (stale if = STATUS before)", d8);
        ser_write(7'h28, 8'h18);                   // host tries to restart the oscillator (map 4.6: not possible)
        #(2000); observe("osc_en after serial restart attempt (map 4.6 documents 0)", osc_en);
        en = 0; #(1); check("EN low restores osc_en asynchronously", osc_en, 1);
        #(10*OSC_T); en = 1; over_hard = 0; #(130*OSC_T);
        ser_read(7'h00, d8); check("CHIP_ID after EN cycle", d8, 8'h47);
        end_test;

        // ============================================================
        begin_test("R5 SOFT_TIME update in the documented byte order (_H then _L) under load");
        en_cycle;
        ser_write(7'h08, 8'h00);                   // no inrush mask
        ser_write(7'h0B, 8'h00);                   // paths off while setting the window
        ser_write(7'h05, 8'h01); ser_write(7'h04, 8'h00);  // SOFT_TIME = 0x0100 = 65536 cycles (6.6 ms)
        ser_write(7'h0B, 8'h01);                   // soft path only
        over_soft = 1;                             // continuous overload above the soft threshold
        wait_cycles(2000);                         // accumulator ~2000 << 0x00FF*256 = 65280
        // host shortens the window to 0x00FF (65280 cycles) following "write _H then _L"
        ser_write(7'h05, 8'h00);
        ser_write(7'h04, 8'hFF);
        check("no soft trip: accumulator (~2100) far below old and new window", trip, 0);
        observe("trip_cause", trip_cause);
        over_soft = 0;
        ser_write(7'h0C, 8'h01);
        end_test;

        $display("SUMMARY tests_pass=%0d tests_fail=%0d checks=%0d errors=%0d", tests_pass, tests_fail, checks, errors);
        $display("RED-TEAM RUN COMPLETE (FAIL lines are reproduced hazards, see DIGITAL.md)");
        $finish;
    end
endmodule
