// Testbench for g1_digital_top: serial protocol, every register, trip timer
// through the register interface, SEU self-test bits, reset behaviour, and the
// G1_TRIP / G1_GATE interface (blocks/g1_trip/INTERFACE.md): the comparators
// are modelled as latched decisions on the cmp_clk edges (soft: rising, hard:
// falling), the G1_GATE trip latch as a reset-dominant SR latch.
// Run: sim/run_sim.sh (iverilog -g2005). Each test prints PASS/FAIL; the
// final line is the summary the README quotes.
// Structure of the serial tasks follows tb_spi_slave.v from
// ChipDesign-BV/spi-slave-ihp (Apache-2.0), adapted to the 3-wire framing.
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module tb_g1_digital;
initial begin $sdf_annotate("/work/designs/g1-guardian/blocks/g1_ctrl/sim/campaigns/sdf_20260921T141228Z_6a81b6d5/input.sdf",dut); $display("SDF_ANNOTATION_RETURNED"); end

    // 10 MHz oscillator, 5 MHz serial clock (f_SCLK <= f_OSC)
    localparam real OSC_T  = 100.0;
    real            SCLK_T = 200.0;

    reg        osc_clk = 0;
    reg        por_n   = 0;
    reg        en      = 0;
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

    // ---------------- analog models ----------------
    // Comparators (G1_TRIP): the shunt-above-threshold conditions over_soft /
    // over_hard are latched at the rising (soft) and falling (hard) cmp_clk
    // edge, valid 1 ns after the edge, held until the next decision.
    reg over_soft = 0, over_hard = 0;
    always @(posedge cmp_clk) cmp_soft <= #1 over_soft;
    always @(negedge cmp_clk) cmp_hard <= #1 over_hard;
    // G1_GATE latch: set = trip_d | (cmp_hard & fast_en), reset = !en | clr_d, reset wins.
    reg  latch_a = 0;
    wire set_a = trip_d | (cmp_hard & fast_en);
    wire rst_a = ~en | clr_d;
    always @* begin
        if (rst_a)      latch_a = 1'b0;
        else if (set_a) latch_a = 1'b1;
    end
    wire tripped = latch_a;

`ifdef GLS
    // gate-level: the hardened macro netlist (same ports as g1_digital_top)
    g1_digital dut (
`else
    g1_digital_top dut (
`endif
        .osc_clk(osc_clk), .por_n(por_n), .en(en),
        .sclk(sclk), .sdi(sdi), .sdo(sdo),
        .cmp_clk(cmp_clk), .cmp_soft(cmp_soft), .cmp_hard(cmp_hard),
        .dac_soft(dac_soft), .dac_hard(dac_hard), .trip_set_sel(trip_set_sel),
        .trip_d(trip_d), .clr_d(clr_d), .fast_en(fast_en), .tripped(tripped),
        .trip(trip), .gate_en(gate_en), .fault_n(fault_n), .trip_cause(trip_cause),
        .osc_en(osc_en), .osc_trim(osc_trim),
        .t2f_en(t2f_en), .t2f_mode(t2f_mode), .bgr_r4(bgr_r4),
        .clk_div_out(clk_div_out));

    always #(OSC_T/2) osc_clk = ~osc_clk;

    // clr_d pulse width monitor (must be >= 100 ns for the G1_GATE latch)
    real    t_clr_rise = 0.0, clr_min_width = 1.0e9;
    integer clr_pulses = 0;
    always @(posedge clr_d) t_clr_rise = $realtime;
    always @(negedge clr_d) if (t_clr_rise > 0.0) begin      // skip the x -> 0 edge at time 0
        clr_pulses = clr_pulses + 1;
        if ($realtime - t_clr_rise < clr_min_width) clr_min_width = $realtime - t_clr_rise;
    end

    // ---------------- bookkeeping ----------------
    integer errors = 0, checks = 0, tests_pass = 0, tests_fail = 0, test_err;
    reg [8*80-1:0] test_name;

    task begin_test(input [8*80-1:0] name);
        begin test_name = name; test_err = errors; end
    endtask
    task end_test;
        begin
            if (errors == test_err) begin tests_pass = tests_pass + 1; $display("PASS %0s", test_name); end
            else begin tests_fail = tests_fail + 1; $display("FAIL %0s", test_name); end
        end
    endtask
    task check(input [8*64-1:0] what, input [31:0] got, input [31:0] exp);
        begin
            checks = checks + 1;
            if (got !== exp) begin
                errors = errors + 1;
                $display("  FAIL %0t %0s: got 0x%0h expected 0x%0h", $time, what, got, exp);
            end
        end
    endtask

    // ---------------- serial tasks ----------------
    task sclk_pulse;
        begin #(SCLK_T/2) sclk = 1; #(SCLK_T/2) sclk = 0; end
    endtask

    task send_byte(input [7:0] b);
        integer i;
        begin for (i = 7; i >= 0; i = i - 1) begin sdi = b[i]; sclk_pulse; end sdi = 0; end
    endtask

    task ser_write(input [6:0] addr, input [7:0] data);
        begin
            send_byte({1'b0, addr});
            send_byte(data);
            #(2000);                       // inter-frame gap, well below the 64-cycle idle timeout
        end
    endtask

    task ser_read(input [6:0] addr, output [7:0] data);
        integer i;
        begin
            send_byte({1'b1, addr});
            send_byte(8'h00);              // turnaround
            for (i = 7; i >= 0; i = i - 1) begin
                #(SCLK_T/2) sclk = 1; data[i] = sdo; #(SCLK_T/2) sclk = 0;
            end
            #(2000);
        end
    endtask

    task ser_read16(input [6:0] addr_l, output [15:0] data);
        reg [7:0] l, h;
        begin ser_read(addr_l, l); ser_read(addr_l + 7'd1, h); data = {h, l}; end
    endtask

    task ser_check(input [6:0] addr, input [7:0] exp, input [8*32-1:0] what);
        reg [7:0] d;
        begin ser_read(addr, d); check(what, d, exp); end
    endtask

    task do_reset;
        begin
            por_n = 0; en = 0; sclk = 0; sdi = 0; over_soft = 0; over_hard = 0;
            #(5*OSC_T); por_n = 1; #(5*OSC_T); en = 1;
            #(130*OSC_T);                  // > 128 osc cycles before the first frame
        end
    endtask

    task wait_cycles(input integer n);
        begin repeat (n) @(posedge osc_clk); #1; end
    endtask

    // wait until trip == v or timeout (cycles); returns cycles waited
    task wait_trip(input v, input integer max_cycles, output integer waited);
        begin
            waited = 0;
            while (trip !== v && waited < max_cycles) begin @(posedge osc_clk); #1; waited = waited + 1; end
        end
    endtask

    reg  [7:0]  d8;
    reg  [15:0] d16, d16b;
    integer     w, i;
    real        t_trip;

    initial begin
`ifdef GLS
        $dumpfile("tb_g1_digital_gls.vcd");
`else
        $dumpfile("tb_g1_digital.vcd");
`endif
        $dumpvars(0, tb_g1_digital);
        do_reset;

        // ------------------------------------------------------------
        begin_test("T01 reset values of every register");
        ser_check(7'h00, 8'h47, "CHIP_ID");
        ser_check(7'h01, 8'h11, "VERSION");
        ser_check(7'h02, 8'h99, "DAC_SOFT");
        ser_check(7'h03, 8'hFE, "DAC_HARD");
        ser_check(7'h04, 8'h27, "SOFT_TIME_L");
        ser_check(7'h05, 8'h00, "SOFT_TIME_H");
        ser_check(7'h06, 8'h00, "SOFT_CFG");
        ser_check(7'h07, 8'h04, "HARD_N");
        ser_check(7'h08, 8'h14, "INRUSH");
        ser_check(7'h09, 8'h0C, "HOLD_TIME");
        ser_check(7'h0A, 8'h03, "RETRY_MAX");
        ser_check(7'h0B, 8'h03, "MODE");
        ser_check(7'h0C, 8'h00, "CTRL");
        ser_check(7'h0D, 8'h88, "STATUS (EN=1, INRUSH_ACTIVE=1)");
        ser_check(7'h0E, 8'h04, "STATUS2 (GATE_EN)");
        ser_check(7'h0F, 8'h00, "TRIP_CNT_L");
        ser_check(7'h10, 8'h00, "TRIP_CNT_H");
        ser_check(7'h11, 8'h00, "SOFT_PEAK_L");
        ser_check(7'h12, 8'h00, "SOFT_PEAK_H");
        ser_check(7'h18, 8'h01, "SEU_CTRL");
        ser_check(7'h19, 8'h00, "SEU_CMD");
        ser_check(7'h1B, 8'h00, "SEU_PLAIN_L");
        ser_check(7'h1C, 8'h00, "SEU_PLAIN_H");
        ser_check(7'h1D, 8'h00, "SEU_CORR_L");
        ser_check(7'h1E, 8'h00, "SEU_CORR_H");
        ser_check(7'h1F, 8'h00, "SEU_UNC");
        ser_check(7'h20, 8'h00, "SEU_RUN");
        ser_check(7'h26, 8'h00, "OSC_DIV");
        ser_check(7'h27, 8'h00, "SENSE_OFS");
        ser_check(7'h28, 8'h18, "OSC_CTRL (OSC_EN, trim 8)");
        ser_check(7'h29, 8'h01, "TEMP_CTRL (T2F_EN)");
        ser_check(7'h2A, 8'h99, "DAC_SOFT_EFF");
        ser_check(7'h2B, 8'hFE, "DAC_HARD_EFF");
        ser_check(7'h2C, 8'h00, "unmapped 0x2C");
        ser_check(7'h7F, 8'h00, "unmapped 0x7F");
        check("dac_soft port", dac_soft, 8'h99);
        check("dac_hard port", dac_hard, 8'hFE);
        check("gate_en port", gate_en, 1);
        check("fault_n port", fault_n, 1);
        check("trip port", trip, 0);
        check("trip_d port", trip_d, 0);
        check("clr_d port", clr_d, 0);
        check("fast_en port", fast_en, 0);
        check("osc_en port", osc_en, 1);
        check("osc_trim port", osc_trim, 8);
        check("t2f_en port", t2f_en, 1);
        check("t2f_mode port", t2f_mode, 0);
        check("bgr_r4 port", bgr_r4, 0);
        // cmp_clk = osc_clk / 2: exactly 10 periods in 20 osc_clk cycles
        w = 0; for (i = 0; i < 20; i = i + 1) begin @(posedge osc_clk); #1; if (cmp_clk) w = w + 1; end
        check("cmp_clk high 10 of 20 cycles", w, 10);
        end_test;

        // ------------------------------------------------------------
        begin_test("T02 write/read-back of every RW register");
        ser_write(7'h02, 8'hA5); ser_check(7'h02, 8'hA5, "DAC_SOFT");
        check("dac_soft port follows", dac_soft, 8'hA5);
        ser_write(7'h03, 8'h5A); ser_check(7'h03, 8'h5A, "DAC_HARD");
        check("dac_hard port follows", dac_hard, 8'h5A);
        ser_write(7'h04, 8'h34); ser_check(7'h04, 8'h34, "SOFT_TIME_L");
        ser_write(7'h05, 8'h12); ser_check(7'h05, 8'h12, "SOFT_TIME_H");
        ser_write(7'h06, 8'hFF); ser_check(7'h06, 8'h0F, "SOFT_CFG masks to 4 bits");
        ser_write(7'h07, 8'h7E); ser_check(7'h07, 8'h7E, "HARD_N");
        ser_write(7'h08, 8'h55); ser_check(7'h08, 8'h55, "INRUSH");
        ser_write(7'h09, 8'hAA); ser_check(7'h09, 8'hAA, "HOLD_TIME");
        ser_write(7'h0A, 8'h0F); ser_check(7'h0A, 8'h0F, "RETRY_MAX");
        ser_write(7'h0B, 8'h0B); ser_check(7'h0B, 8'h0B, "MODE");
        check("trip_set_sel port follows MODE[3]", trip_set_sel, 1);
        ser_write(7'h0B, 8'hE3); ser_check(7'h0B, 8'h23, "MODE masks to 6 bits");
        check("fast_en port follows MODE[5]", fast_en, 1);
        ser_write(7'h0B, 8'h03);
        ser_write(7'h27, 8'h7F); ser_check(7'h27, 8'h7F, "SENSE_OFS");
        ser_write(7'h27, 8'h00);
        ser_write(7'h28, 8'hE5); ser_check(7'h28, 8'h05, "OSC_CTRL masks to 5 bits");
        check("osc_en port follows OSC_CTRL[4]", osc_en, 0);
        check("osc_trim port follows OSC_CTRL[3:0]", osc_trim, 5);
        ser_write(7'h28, 8'h18);
        ser_write(7'h29, 8'hFE); ser_check(7'h29, 8'h06, "TEMP_CTRL masks to 3 bits");
        check("t2f_en port follows", t2f_en, 0);
        check("t2f_mode port follows", t2f_mode, 1);
        check("bgr_r4 port follows", bgr_r4, 1);
        ser_write(7'h29, 8'h01);
        ser_write(7'h2A, 8'h00); ser_write(7'h2B, 8'h00);
        ser_check(7'h2A, 8'hA5, "DAC_SOFT_EFF read-only, = DAC_SOFT");
        ser_check(7'h2B, 8'h5A, "DAC_HARD_EFF read-only, = DAC_HARD");
        ser_write(7'h18, 8'h3E); ser_check(7'h18, 8'h06, "SEU_CTRL masks to 3 bits");
        ser_write(7'h26, 8'hFF); ser_check(7'h26, 8'h07, "OSC_DIV masks to 3 bits");
        ser_write(7'h0C, 8'h00); ser_check(7'h0C, 8'h00, "CTRL reads 0");
        ser_write(7'h00, 8'hFF); ser_check(7'h00, 8'h47, "CHIP_ID read-only");
        ser_write(7'h7E, 8'hFF); ser_check(7'h7E, 8'h00, "unmapped write ignored");
        end_test;

        // ------------------------------------------------------------
        begin_test("T03 serial at f_SCLK = f_OSC (10 MHz) and idle-timeout resync");
        SCLK_T = 100.0;
        ser_write(7'h02, 8'h3C); ser_check(7'h02, 8'h3C, "write/read at 10 MHz SCLK");
        ser_check(7'h00, 8'h47, "CHIP_ID at 10 MHz SCLK");
        SCLK_T = 200.0;
        // abort a frame after 5 clocks, idle > 128 cycles, then a normal frame must work
        sdi = 1; repeat (5) sclk_pulse; sdi = 0;
        #(140*OSC_T);
        ser_check(7'h02, 8'h3C, "read after resync");
        ser_write(7'h02, 8'h99); ser_check(7'h02, 8'h99, "write after resync");
        end_test;

        // ------------------------------------------------------------
        begin_test("T04 EN low resets configuration; STATUS.EN");
        ser_write(7'h03, 8'h11);
        en = 0; #(3*OSC_T);
        check("gate_en low while EN low", gate_en, 0);
        check("trip low while EN low", trip, 0);
        check("trip_d low while EN low", trip_d, 0);
        check("osc_en high while EN low", osc_en, 1);
        en = 1; #(130*OSC_T);
        ser_check(7'h03, 8'hFE, "DAC_HARD back to reset after EN cycle");
        ser_check(7'h0B, 8'h03, "MODE back to reset after EN cycle");
        end_test;

        // ------------------------------------------------------------
        begin_test("T05 inrush mask after EN, then hard trip");
        // still within the 1 ms default inrush (reset ~15 us ago plus frames)
        ser_check(7'h0D, 8'h88, "INRUSH_ACTIVE set");
        over_hard = 1; wait_cycles(50);
        check("no trip during inrush", trip, 0);
        over_hard = 0;
        wait_cycles(10240 + 10);
        ser_check(7'h0D, 8'h80, "INRUSH_ACTIVE cleared after ~1 ms");
        over_hard = 1;
        wait_trip(1, 20, w);
        check("hard trip after inrush", trip, 1);
        // 0..2 cycles to the next falling cmp_clk edge, 2 sync, 4 decisions x 2 cycles, 1 register
        if (w < 9 || w > 12) begin errors = errors + 1; $display("  FAIL hard trip latency %0d cycles", w); end
        check("cause hard", trip_cause, 2);
        check("fault_n low", fault_n, 0);
        check("gate_en low", gate_en, 0);
        check("trip_d set", trip_d, 1);
        check("G1_GATE latch set by trip_d", tripped, 1);
        over_hard = 0;
        ser_check(7'h0D, 8'h85, "STATUS tripped, cause hard");
        ser_check(7'h0E, 8'h08, "STATUS2: TRIPPED_A, gate off");
        ser_read16(7'h0F, d16); check("TRIP_CNT = 1", d16, 1);
        wait_cycles(1000);
        check("latched: still tripped", trip, 1);
        ser_write(7'h0C, 8'h01);            // CLEAR
        wait_cycles(5);
        check("cleared", trip, 0);
        check("G1_GATE latch cleared by clr_d", tripped, 0);
        check("clr_d back low", clr_d, 0);
        ser_check(7'h0D, 8'h80, "STATUS clear");
        ser_check(7'h0E, 8'h04, "STATUS2: latch clear, gate on");
        end_test;

        // ------------------------------------------------------------
        begin_test("T06 hard path: N-1 consecutive decisions do not trip, N do; gap resets");
        ser_write(7'h08, 8'h00);            // no inrush for the rest
        ser_write(7'h07, 8'h0A);            // HARD_N = 10 comparator decisions (cmp_clk periods)
        @(posedge osc_clk); #1;
        // one decision per 2 osc_clk: an 18-cycle window holds exactly 9 falling cmp_clk edges
        over_hard = 1; wait_cycles(18); over_hard = 0; wait_cycles(20);
        check("9 decisions: no trip", trip, 0);
        over_hard = 1; wait_cycles(12); over_hard = 0; wait_cycles(4);
        over_hard = 1; wait_cycles(12); over_hard = 0; wait_cycles(20);
        check("6 + gap + 6: no trip (clear-on-low)", trip, 0);
        over_hard = 1; wait_cycles(20); over_hard = 0; wait_cycles(6);
        check("10 decisions: trip", trip, 1);
        check("cause hard", trip_cause, 2);
        ser_write(7'h0C, 8'h01); wait_cycles(5);
        check("cleared", trip, 0);
        ser_read16(7'h0F, d16); check("TRIP_CNT = 2", d16, 2);
        end_test;

        // ------------------------------------------------------------
        begin_test("T07 soft path: short pulse no trip, long trips, decay, peak, hysteresis");
        ser_write(7'h02, 8'h60);                            // soft code 0x60 for the hysteresis checks
        ser_write(7'h04, 8'h02); ser_write(7'h05, 8'h00);   // window 2 x 256 = 512 cycles
        ser_write(7'h06, 8'h04);                            // HYST_EN, 1 LSB
        ser_write(7'h0B, 8'h01);                            // soft only
        @(posedge osc_clk); #1;
        over_soft = 1; wait_cycles(300);                    // cmp_soft high for 300 +/- 2 cycles
        check("dac_soft lowered by 1 LSB while armed", dac_soft, 8'h5F);
        ser_check(7'h0D, 8'hC0, "SOFT_ARMED");
        over_soft = 0; wait_cycles(400);                    // symmetric decay empties the counter
        check("300 < 512: no trip", trip, 0);
        check("dac_soft back to nominal", dac_soft, 8'h60);
        ser_read16(7'h11, d16); check("SOFT_PEAK ~ 300/256 = 1", d16, 1);
        over_soft = 1; wait_trip(1, 700, w); over_soft = 0;
        check("continuous > 512: trip", trip, 1);
        check("cause soft", trip_cause, 1);
        // 0..2 cycles to the rising cmp_clk edge, 2 sync, 512 counts, 1 register
        if (w < 512 || w > 520) begin errors = errors + 1; $display("  FAIL soft trip latency %0d cycles", w); end
        ser_write(7'h0C, 8'h05); wait_cycles(5);            // CLEAR + CLR_PEAK
        check("cleared", trip, 0);
        // intermittent: 400 high, 100 low (decay 100), 250 high -> 550 >= 512 trips
        over_soft = 1; wait_cycles(400); over_soft = 0; wait_cycles(100);
        check("no trip yet", trip, 0);
        over_soft = 1; wait_trip(1, 400, w); over_soft = 0;
        check("intermittent accumulates to trip", trip, 1);
        if (w < 205 || w > 225) begin errors = errors + 1; $display("  FAIL intermittent latency %0d cycles", w); end
        ser_write(7'h0C, 8'h01); wait_cycles(5);
        // decay 1/16: 400 high, 100 low decays only ~6 -> 118 more highs trip
        ser_write(7'h06, 8'h02);
        over_soft = 1; wait_cycles(400); over_soft = 0; wait_cycles(100);
        over_soft = 1; wait_trip(1, 400, w); over_soft = 0;
        check("slow decay trips sooner", trip, 1);
        if (w < 110 || w > 130) begin errors = errors + 1; $display("  FAIL slow-decay latency %0d cycles", w); end
        ser_write(7'h0C, 8'h01); wait_cycles(5);
        ser_write(7'h06, 8'h00);
        ser_write(7'h02, 8'h99);
        ser_read16(7'h0F, d16); check("TRIP_CNT = 5", d16, 5);
        end_test;

        // ------------------------------------------------------------
        begin_test("T08 force trip, path enables");
        ser_write(7'h0B, 8'h00);                            // both paths off
        over_hard = 1; over_soft = 1; wait_cycles(1000);
        check("paths disabled: no trip", trip, 0);
        check("paths disabled: G1_GATE latch clear (fast_en = 0)", tripped, 0);
        over_hard = 0; over_soft = 0;
        ser_write(7'h0B, 8'h10);                            // FORCE_TRIP
        wait_cycles(5);
        check("forced trip", trip, 1);
        check("cause forced", trip_cause, 3);
        check("G1_GATE latch set", tripped, 1);
        ser_write(7'h0C, 8'h01); wait_cycles(5);
        check("clear while forced re-trips", trip, 1);
        check("G1_GATE latch set again after the clear pulse", tripped, 1);
        ser_write(7'h0B, 8'h03); ser_write(7'h0C, 8'h01); wait_cycles(5);
        check("cleared after force released", trip, 0);
        check("G1_GATE latch cleared", tripped, 0);
        end_test;

        // ------------------------------------------------------------
        begin_test("T09 retrigger mode: hold, re-enable, inrush restart, give-up");
        ser_write(7'h07, 8'h04);            // HARD_N 4
        ser_write(7'h08, 8'h01);            // inrush 512 cycles
        ser_write(7'h09, 8'h01);            // hold 8192 cycles
        ser_write(7'h0A, 8'h02);            // 2 retries
        ser_write(7'h0B, 8'h06);            // hard + retrig
        ser_write(7'h0C, 8'h02);            // clear trip count
        wait_cycles(600);                   // inrush from the register write does not restart; fine
        over_hard = 1;
        wait_trip(1, 20, w);   check("trip 1", trip, 1);
        t_trip = $realtime;
        ser_check(7'h0D, 8'h95, "STATUS tripped+hard+holding");
        wait_trip(0, 9000, w); check("re-enable 1", trip, 0);
        w = ($realtime - t_trip) / OSC_T;
        if (w < 8185 || w > 8200) begin errors = errors + 1; $display("  FAIL hold time %0d cycles", w); end
        check("G1_GATE latch cleared at re-enable", tripped, 0);
        wait_trip(1, 700, w);  check("trip 2 after inrush", trip, 1);
        if (w < 505 || w > 535) begin errors = errors + 1; $display("  FAIL inrush after re-enable %0d cycles", w); end
        wait_trip(0, 9000, w); check("re-enable 2", trip, 0);
        wait_trip(1, 700, w);  check("trip 3", trip, 1);
        wait_trip(0, 9000, w); check("gave up: stays tripped", trip, 1);
        ser_check(7'h0D, 8'hA5, "STATUS tripped+hard+GAVE_UP");
        ser_read(7'h0E, d8); check("RETRY_CNT = 2", d8[7:4], 2);
        ser_read16(7'h0F, d16); check("TRIP_CNT = 3", d16, 3);
        over_hard = 0;
        ser_write(7'h0C, 8'h01); wait_cycles(5);
        check("cleared", trip, 0);
        ser_check(7'h0D, 8'h80, "STATUS clear");
        // cool-down: one trip, re-enable, no re-trip for a hold time -> retry count back to 0
        over_hard = 1; wait_trip(1, 20, w); over_hard = 0;
        wait_trip(0, 9000, w);
        ser_read(7'h0E, d8); check("RETRY_CNT = 1 after re-enable", d8[7:4], 1);
        wait_cycles(8192 + 600);
        ser_read(7'h0E, d8); check("RETRY_CNT = 0 after cool-down", d8[7:4], 0);
        ser_write(7'h0B, 8'h03);
        end_test;

        // ------------------------------------------------------------
        begin_test("T10 SEU self-test injection through registers");
        // scrubber running since reset (T04) -> filled long ago
        ser_check(7'h1A, 8'h01, "SEU_STATUS active");
        ser_write(7'h19, 8'h02);            // INJ_PLAIN
        wait_cycles(1030);
        ser_read16(7'h1B, d16); check("SEU_PLAIN = 1", d16, 1);
        ser_read16(7'h1D, d16); check("SEU_CORR = 0", d16, 0);
        ser_check(7'h1F, 8'h00, "SEU_UNC = 0");
        ser_check(7'h20, 8'h01, "SEU_RUN = 1");
        ser_write(7'h19, 8'h04);            // INJ_TMR
        wait_cycles(300);
        ser_read16(7'h1D, d16); check("SEU_CORR = 1", d16, 1);
        ser_check(7'h1F, 8'h00, "SEU_UNC still 0");
        ser_read16(7'h1B, d16); check("SEU_PLAIN still 1", d16, 1);
        ser_write(7'h19, 8'h01);            // CLR_CNT
        ser_read16(7'h1B, d16); check("SEU_PLAIN cleared", d16, 0);
        ser_read16(7'h1D, d16); check("SEU_CORR cleared", d16, 0);
        ser_check(7'h20, 8'h00, "SEU_RUN cleared");
        end_test;

`ifndef GLS
        // T11 and T12 use hierarchical references into the RTL; skipped at gate level
        // ------------------------------------------------------------
        begin_test("T11 SEU constant pattern (static data): upsets by hierarchical flip");
        ser_write(7'h18, 8'h05);            // all-ones pattern, enabled (restarts the fill)
        wait_cycles(1100);
        ser_check(7'h1A, 8'h01, "active after refill");
        check("plain chain all ones", &dut.u_seu.u_plain.q, 1);
        check("TMR chain all ones", &dut.u_seu.vote, 1);
        ser_read16(7'h1B, d16); check("no false plain counts", d16, 0);
        ser_read16(7'h1D, d16); check("no false corr counts", d16, 0);
        dut.u_seu.u_plain.q[100] = ~dut.u_seu.u_plain.q[100];
        dut.u_seu.u_tmr_a.q[77]  = ~dut.u_seu.u_tmr_a.q[77];
        wait_cycles(1100);
        ser_read16(7'h1B, d16); check("SEU_PLAIN = 1", d16, 1);
        ser_read16(7'h1D, d16); check("SEU_CORR = 1", d16, 1);
        ser_check(7'h1F, 8'h00, "SEU_UNC = 0");
        ser_write(7'h18, 8'h01);            // back to checkerboard
        ser_write(7'h19, 8'h01);
        end_test;

        // ------------------------------------------------------------
        begin_test("T12 OSC_CNT L/H consistency and OSC_DIV");
        ser_write(7'h0C, 8'h08);            // CLR_OSC_CNT
        ser_read16(7'h24, d16);
        wait_cycles(256 * 300);
        ser_read16(7'h24, d16b);
        // 76800 cycles + serial overhead -> about 300..310 ticks of 256
        if (d16b - d16 < 300 || d16b - d16 > 312) begin errors = errors + 1; $display("  FAIL OSC_CNT delta %0d", d16b - d16); end
        ser_write(7'h26, 8'h02);            // /1024
        ser_read16(7'h24, d16);
        wait_cycles(1024 * 50);
        ser_read16(7'h24, d16b);
        if (d16b - d16 < 50 || d16b - d16 > 53) begin errors = errors + 1; $display("  FAIL OSC_CNT /1024 delta %0d", d16b - d16); end
        // high byte captured with the low byte: force a boundary crossing
        ser_write(7'h26, 8'h00); ser_write(7'h0C, 8'h08);
        wait (dut.u_regfile.osc_cnt == 16'h00FF);   // read L within the 256-cycle tick
        ser_read(7'h24, d8);               // L = 0xFF, H latched 0x00
        wait (dut.u_regfile.osc_cnt == 16'h0100);
        wait_cycles(10);
        ser_read(7'h25, d16b[7:0]);
        check("OSC_CNT_L", d8, 8'hFF);
        check("OSC_CNT_H latched with L", d16b[7:0], 8'h00);
        ser_read16(7'h24, d16); check("fresh read sees 0x01xx", d16[15:8], 8'h01);
        ser_write(7'h26, 8'h00);
        end_test;
`endif

        // ------------------------------------------------------------
        begin_test("T13 sense offset: signed add to both DAC codes, saturation, hysteresis stacking");
        ser_write(7'h02, 8'h99); ser_write(7'h03, 8'hFE); ser_write(7'h06, 8'h00);
        ser_write(7'h27, 8'h0A);                            // +10
        check("dac_soft + 10", dac_soft, 8'hA3);
        check("dac_hard saturates at 255", dac_hard, 8'hFF);
        ser_check(7'h2A, 8'hA3, "DAC_SOFT_EFF");
        ser_check(7'h2B, 8'hFF, "DAC_HARD_EFF");
        ser_write(7'h27, 8'hEC);                            // -20
        check("dac_soft - 20", dac_soft, 8'h85);
        check("dac_hard - 20", dac_hard, 8'hEA);
        ser_write(7'h02, 8'h05);
        check("dac_soft saturates at 0", dac_soft, 8'h00);
        ser_write(7'h27, 8'h80);                            // -128
        check("dac_hard - 128", dac_hard, 8'h7E);
        ser_write(7'h27, 8'h7F); ser_write(7'h02, 8'h80);   // +127
        check("dac_soft 0x80 + 127 saturates", dac_soft, 8'hFF);
        ser_write(7'h02, 8'h60); ser_write(7'h27, 8'hFB);   // -5
        ser_write(7'h06, 8'h0C);                            // HYST_EN, 2 LSB
        ser_write(7'h0B, 8'h01);                            // soft only
        over_soft = 1; wait_cycles(20);
        check("armed: 0x60 - 2 (hyst) - 5 (ofs) = 0x59", dac_soft, 8'h59);
        // idle so far since the last frame: 20 + 20 cycles; wait past the 64..80-cycle
        // frame-reset window (register map 1.2) before the next frame
        over_soft = 0; wait_cycles(100);
        check("disarmed: 0x60 - 5 = 0x5B", dac_soft, 8'h5B);
        ser_write(7'h06, 8'h00); ser_write(7'h27, 8'h00); ser_write(7'h0B, 8'h03);
        ser_write(7'h02, 8'h99); ser_write(7'h03, 8'hFE);
        check("offset 0 restores the codes", {dac_soft, dac_hard}, 16'h99FE);
        end_test;

        // ------------------------------------------------------------
        begin_test("T14 G1_GATE fast path: analog trip adopted, clr_d clears it, no re-trip");
        ser_write(7'h08, 8'h00);            // no inrush
        ser_write(7'h0B, 8'h21);            // FAST_EN, soft only (digital hard path off)
        ser_write(7'h0C, 8'h02);            // clear trip count
        wait_cycles(10);
        check("latch clear before", tripped, 0);
        over_hard = 1;                      // one hard decision sets the analog latch directly
        wait_cycles(3); over_hard = 0;
        check("analog latch set by cmp_hard & fast_en", tripped, 1);
        wait_trip(1, 10, w);
        check("digital latch follows the analog latch", trip, 1);
        if (w > 6) begin errors = errors + 1; $display("  FAIL adoption latency %0d cycles", w); end
        check("cause hard", trip_cause, 2);
        ser_check(7'h0D, 8'h85, "STATUS tripped, cause hard");
        ser_check(7'h0E, 8'h08, "STATUS2 TRIPPED_A");
        ser_read16(7'h0F, d16); check("TRIP_CNT = 1", d16, 1);
        wait_cycles(1000);
        check("still tripped (latched mode)", trip, 1);
        ser_write(7'h0C, 8'h01);            // CLEAR -> clr_d pulse
        wait_cycles(10);
        check("digital cleared", trip, 0);
        check("analog latch cleared", tripped, 0);
        check("no re-trip from the stale synchronised state", trip, 0);
        ser_read16(7'h0F, d16); check("TRIP_CNT still 1", d16, 1);
        // retrigger with the analog fast path: the re-enable pulse clears the analog latch
        ser_write(7'h09, 8'h01); ser_write(7'h0A, 8'hFF); ser_write(7'h0B, 8'h25);   // hold 8192, unlimited, retrig
        over_hard = 1; wait_cycles(3); over_hard = 0;
        wait_trip(1, 10, w); check("trip via fast path", trip, 1);
        wait_trip(0, 9000, w); check("re-enabled after hold", trip, 0);
        wait_cycles(10);
        check("analog latch cleared at re-enable", tripped, 0);
        ser_write(7'h0B, 8'h03); ser_write(7'h0C, 8'h01);
        // the analog latch is also cleared by EN low
        ser_write(7'h0B, 8'h20); over_hard = 1; wait_cycles(3); over_hard = 0;
        check("latch set", tripped, 1);
        en = 0; #(3*OSC_T);
        check("EN low clears the analog latch", tripped, 0);
        check("trip_d low in reset", trip_d, 0);
        en = 1; #(130*OSC_T);
        ser_check(7'h0B, 8'h03, "MODE back to reset");
        end_test;

        // ------------------------------------------------------------
        begin_test("T15 clr_d pulse width and trip_d hold");
        if (clr_pulses < 5) begin errors = errors + 1; $display("  FAIL only %0d clr_d pulses seen", clr_pulses); end
        if (clr_min_width < 199.0) begin errors = errors + 1; $display("  FAIL clr_d min width %0f ns", clr_min_width); end
        $display("  clr_d pulses %0d, minimum width %0f ns (>= 100 ns required)", clr_pulses, clr_min_width);
        checks = checks + 2;
        end_test;

        // ------------------------------------------------------------
        $display("SUMMARY tests_pass=%0d tests_fail=%0d checks=%0d errors=%0d", tests_pass, tests_fail, checks, errors);
        if (errors == 0) $display("ALL TESTS PASSED"); else $display("SOME TESTS FAILED");
        $finish;
    end

    initial begin
        #(200_000_000);                     // 200 ms guard
        $display("TIMEOUT");
        $finish;
    end

endmodule
