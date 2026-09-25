// ECO 2026-09-25 copy of tb_g1_digital.v (blocks/g1_ctrl/ECO_20260925.md):
// T01-T15 updated to register map 1.2 (each change marked "ECO:"), E1-E8 added
// for the ECO changes. Run: sim/eco_20260925/run_eco.sh eco.
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

module tb_g1_digital_eco;

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

    // ---------------- E6 power-up instances (ECO) ----------------
    // Three macros with por_n tied 1 (as on the chip) and EN low from t = 0, clock running
    // (osc_en is a constant 1 in the ECO). Flop state at power-up: pu_x = simulator X
    // (unknown), pu_s0 / pu_s1 = en_seen deposited 0 / 1 at t = 0 (both silicon cases).
    reg en_pu = 0;
    wire [7:0] pux_ds, pux_dh, pu0_ds, pu0_dh, pu1_ds, pu1_dh;
    wire pux_tripd, pux_clrd, pux_fast, pux_osc, pu0_tripd, pu0_clrd, pu0_fast, pu0_osc, pu1_tripd, pu1_clrd, pu1_fast, pu1_osc;
    wire [3:0] pux_trim, pu0_trim, pu1_trim;
    g1_digital pu_x  (.osc_clk(osc_clk), .por_n(1'b1), .en(en_pu), .sclk(1'b0), .sdi(1'b0), .sdo(),
        .cmp_clk(), .cmp_soft(1'b0), .cmp_hard(1'b0), .dac_soft(pux_ds), .dac_hard(pux_dh), .trip_set_sel(),
        .trip_d(pux_tripd), .clr_d(pux_clrd), .fast_en(pux_fast), .tripped(1'b0), .trip(), .gate_en(), .fault_n(),
        .trip_cause(), .osc_en(pux_osc), .osc_trim(pux_trim), .t2f_en(), .t2f_mode(), .bgr_r4(), .clk_div_out());
    g1_digital pu_s0 (.osc_clk(osc_clk), .por_n(1'b1), .en(en_pu), .sclk(1'b0), .sdi(1'b0), .sdo(),
        .cmp_clk(), .cmp_soft(1'b0), .cmp_hard(1'b0), .dac_soft(pu0_ds), .dac_hard(pu0_dh), .trip_set_sel(),
        .trip_d(pu0_tripd), .clr_d(pu0_clrd), .fast_en(pu0_fast), .tripped(1'b0), .trip(), .gate_en(), .fault_n(),
        .trip_cause(), .osc_en(pu0_osc), .osc_trim(pu0_trim), .t2f_en(), .t2f_mode(), .bgr_r4(), .clk_div_out());
    g1_digital pu_s1 (.osc_clk(osc_clk), .por_n(1'b1), .en(en_pu), .sclk(1'b0), .sdi(1'b0), .sdo(),
        .cmp_clk(), .cmp_soft(1'b0), .cmp_hard(1'b0), .dac_soft(pu1_ds), .dac_hard(pu1_dh), .trip_set_sel(),
        .trip_d(pu1_tripd), .clr_d(pu1_clrd), .fast_en(pu1_fast), .tripped(1'b0), .trip(), .gate_en(), .fault_n(),
        .trip_cause(), .osc_en(pu1_osc), .osc_trim(pu1_trim), .t2f_en(), .t2f_mode(), .bgr_r4(), .clk_div_out());
    initial begin pu_s0.u_core.en_seen = 1'b0; pu_s1.u_core.en_seen = 1'b1; end

    // E3 monitor: every value the soft window takes (RTL hierarchical probe)
    reg        st_mon = 0;
    reg [15:0] st_old, st_new;
    integer    st_bad = 0, st_changes = 0;
    always @(dut.u_regfile.soft_time) if (st_mon) begin
        st_changes = st_changes + 1;
        if (dut.u_regfile.soft_time !== st_old && dut.u_regfile.soft_time !== st_new) begin
            st_bad = st_bad + 1;
            $display("  FAIL %0t SOFT_TIME transient 0x%04h (old 0x%04h new 0x%04h)", $time, dut.u_regfile.soft_time, st_old, st_new);
        end
    end

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
    real        t_trip, t0;
    integer     rst_falls = 0;
    always @(negedge dut.rst_n) rst_falls = rst_falls + 1;

    initial begin
`ifdef GLS
        $dumpfile("tb_g1_digital_gls.vcd");
`else
        $dumpfile("tb_g1_digital.vcd");
`endif
        $dumpvars(0, tb_g1_digital_eco);

        // ------------------------------------------------------------
        begin_test("E6 power-up, EN low, por_n tied 1: reset without POR, osc_en 1");
        #1;
        check("pu_x osc_en = 1 at t = 0 (constant)", pux_osc, 1);
        check("pu_s0 osc_en = 1 at t = 0", pu0_osc, 1);
        check("pu_s1 osc_en = 1 at t = 0", pu1_osc, 1);
        // en_seen = 0: the reset follows EN combinationally, outputs defined before the first clock edge
        check("pu_s0 in reset before the first osc_clk edge", pu_s0.u_core.rs1, 0);
        check("pu_s0 dac_hard 0xFE before the first edge", pu0_dh, 8'hFE);
        check("pu_s0 dac_soft 0x99 before the first edge", pu0_ds, 8'h99);
        check("pu_s0 trip_d, clr_d, fast_en = 0,0,1", {pu0_tripd, pu0_clrd, pu0_fast}, 3'b001);
        // en_seen = 1 or unknown: the 8-sample filter asserts the reset within 2 + 8 + 1 edges
        repeat (11) @(posedge osc_clk); #1;
        check("pu_s1 in reset within 11 edges", pu_s1.u_core.rs1, 0);
        check("pu_x in reset within 11 edges", pu_x.u_core.rs1, 0);
        check("pu_s1 outputs at reset values", {pu1_dh, pu1_ds, pu1_tripd, pu1_clrd, pu1_fast, pu1_trim}, {8'hFE, 8'h99, 3'b001, 4'h8});
        check("pu_x outputs at reset values",  {pux_dh, pux_ds, pux_tripd, pux_clrd, pux_fast, pux_trim}, {8'hFE, 8'h99, 3'b001, 4'h8});
        check("pu_x INRUSH register 0x02", pu_x.u_core.u_regfile.inrush, 8'h02);
        check("pu_x MODE register 0x23", pu_x.u_core.u_regfile.mode, 6'h23);
        // EN rises: reset released in <= 6 edges, en_seen set, and a later EN low of 9 cycles resets again
        en_pu = 1;
        repeat (6) @(posedge osc_clk); #1;
        check("pu_x released within 6 edges of EN rise", pu_x.u_core.rs1, 1);
        check("pu_s0 released within 6 edges of EN rise", pu_s0.u_core.rs1, 1);
        check("pu_s0 en_seen set by EN high", pu_s0.u_core.en_seen, 1);
        end_test;

        do_reset;

        // ------------------------------------------------------------
        begin_test("T01 reset values of every register");
        ser_check(7'h00, 8'h47, "CHIP_ID");
        ser_check(7'h01, 8'h12, "VERSION (ECO: 1.2)");
        ser_check(7'h02, 8'h99, "DAC_SOFT");
        ser_check(7'h03, 8'hFE, "DAC_HARD");
        ser_check(7'h04, 8'h27, "SOFT_TIME_L");
        ser_check(7'h05, 8'h00, "SOFT_TIME_H");
        ser_check(7'h06, 8'h00, "SOFT_CFG");
        ser_check(7'h07, 8'h04, "HARD_N");
        ser_check(7'h08, 8'h02, "INRUSH (ECO: reset 0x02)");
        ser_check(7'h09, 8'h0C, "HOLD_TIME");
        ser_check(7'h0A, 8'h03, "RETRY_MAX");
        ser_check(7'h0B, 8'h23, "MODE (ECO: reset 0x23, FAST_EN)");
        ser_check(7'h0C, 8'h00, "CTRL");
        ser_check(7'h0D, 8'h80, "STATUS (EN=1; ECO: 1024-cycle inrush already over)");
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
        check("fast_en port (ECO: 1)", fast_en, 1);
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
        // ECO: _H is staged and takes effect with the _L write
        ser_write(7'h05, 8'h12); ser_check(7'h05, 8'h00, "SOFT_TIME_H staged, not yet in effect");
        ser_write(7'h04, 8'h34); ser_check(7'h04, 8'h34, "SOFT_TIME_L");
        ser_check(7'h05, 8'h12, "SOFT_TIME_H in effect after the _L write");
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
        ser_write(7'h28, 8'hE5); ser_check(7'h28, 8'h15, "OSC_CTRL: trim written, OSC_EN reads 1 (ECO)");
        check("osc_en port stays 1 (ECO: bit 4 write ignored)", osc_en, 1);
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
        check("osc_en high while EN low", osc_en, 1);
        #(9*OSC_T);                         // ECO: reset needs 8 consecutive low samples
        check("trip low while EN low", trip, 0);
        check("trip_d low while EN low", trip_d, 0);
        en = 1; #(130*OSC_T);
        ser_check(7'h03, 8'hFE, "DAC_HARD back to reset after EN cycle");
        ser_check(7'h0B, 8'h23, "MODE back to reset after EN cycle (ECO: 0x23)");
        end_test;

        // ------------------------------------------------------------
        begin_test("T05 inrush mask after EN, then hard trip");
        // ECO: still within the 1024-cycle default inrush (reset ~15 us ago plus frames);
        // FAST_EN (reset 1) is not inrush-masked, so switch to the digital paths only
        ser_write(7'h0B, 8'h03);
        ser_check(7'h0D, 8'h88, "INRUSH_ACTIVE set");
        over_hard = 1; wait_cycles(50);
        check("no trip during inrush", trip, 0);
        over_hard = 0;
        wait_cycles(1024 + 10);
        ser_check(7'h0D, 8'h80, "INRUSH_ACTIVE cleared after 1024 cycles (ECO)");
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
        #(9*OSC_T);                         // ECO: reset after 8 consecutive low samples
        check("trip_d low in reset", trip_d, 0);
        en = 1; #(130*OSC_T);
        ser_check(7'h0B, 8'h23, "MODE back to reset (ECO: 0x23)");
        end_test;

        // ------------------------------------------------------------
        begin_test("T15 clr_d pulse width and trip_d hold");
        if (clr_pulses < 5) begin errors = errors + 1; $display("  FAIL only %0d clr_d pulses seen", clr_pulses); end
        if (clr_min_width < 199.0) begin errors = errors + 1; $display("  FAIL clr_d min width %0f ns", clr_min_width); end
        $display("  clr_d pulses %0d, minimum width %0f ns (>= 100 ns required)", clr_pulses, clr_min_width);
        checks = checks + 2;
        end_test;

        // ============================================================
        // ECO 2026-09-25 tests (E6 runs first, at power-up)
        // ------------------------------------------------------------
        begin_test("E7 defaults: INRUSH 0x02 = 1024 cycles, FAST_EN 1 not masked");
        en = 0; #(12*OSC_T); en = 1;
        wait (dut.rst_n === 1'b1); t0 = $realtime;
        wait (dut.inrush_active === 1'b0);
        w = ($realtime - t0) / OSC_T;
        $display("  inrush mask after reset release: %0d cycles", w);
        if (w < 1023 || w > 1026) begin errors = errors + 1; $display("  FAIL inrush window %0d cycles", w); end
        checks = checks + 1;
        #(130*OSC_T);
        ser_check(7'h08, 8'h02, "INRUSH reset 0x02");
        ser_check(7'h0B, 8'h23, "MODE reset 0x23");
        check("fast_en port 1", fast_en, 1);
        // hard overload inside the mask window: the analog fast path trips, the core adopts it
        en = 0; #(12*OSC_T); en = 1;
        wait (dut.rst_n === 1'b1); wait_cycles(50);
        check("inrush mask active", dut.inrush_active, 1);
        over_hard = 1; wait_cycles(3);
        check("G1_GATE latch set by the fast path during the mask", tripped, 1);
        wait_trip(1, 10, w);
        check("adopted, cause hard, during the mask", {trip, trip_cause, dut.inrush_active}, {1'b1, 2'd2, 1'b1});
        over_hard = 0;
        en = 0; #(12*OSC_T); en = 1; #(130*OSC_T);
        end_test;

        // ------------------------------------------------------------
        begin_test("E1 OSC_CTRL.OSC_EN writes ignored, osc_en constant 1");
        for (i = 0; i < 5; i = i + 1) begin
            d8 = (i == 0) ? 8'h00 : (i == 1) ? 8'h08 : (i == 2) ? 8'h0F : (i == 3) ? 8'hFF : 8'h13;
            ser_write(7'h28, d8);
            check("osc_en after OSC_CTRL write", osc_en, 1);
            check("osc_trim follows bits 3:0", osc_trim, d8[3:0]);
            ser_check(7'h28, {4'b0001, d8[3:0]}, "OSC_CTRL reads OSC_EN = 1");
        end
        ser_write(7'h28, 8'h08);
        dut.u_regfile.osc_ctrl = ~dut.u_regfile.osc_ctrl; #1;          // upset every trim flop at once
        check("osc_en with all OSC_CTRL flops flipped", osc_en, 1);
        dut.u_regfile.osc_ctrl = 4'h8;
        ser_check(7'h00, 8'h47, "serial alive (CHIP_ID)");
        end_test;

        // ------------------------------------------------------------
        begin_test("E2 INRUSH raise: no re-mask when over, extends when running");
        ser_write(7'h0B, 8'h03);                           // digital paths only: test the digital mask
        ser_write(7'h07, 8'h04);
        wait (dut.inrush_active === 1'b0); #(130*OSC_T);
        ser_read(7'h0D, d8); check("mask of this EN cycle over", d8[3], 0);
        ser_write(7'h08, 8'h01);
        ser_read(7'h0D, d8); check("INRUSH 0x01 write: INRUSH_ACTIVE stays 0", d8[3], 0);
        ser_write(7'h08, 8'hFF);
        ser_read(7'h0D, d8); check("INRUSH 0xFF write: INRUSH_ACTIVE stays 0", d8[3], 0);
        over_hard = 1; wait_trip(1, 20, w);
        check("hard trip after the live INRUSH raise", trip, 1);
        if (w < 9 || w > 12) begin errors = errors + 1; $display("  FAIL hard trip latency %0d cycles", w); end
        checks = checks + 1;
        over_hard = 0; ser_write(7'h0C, 8'h01); wait_cycles(5);
        check("cleared", trip, 0);
        // a raise while the window is still running extends it (window uses the current value)
        en = 0; #(12*OSC_T); en = 1;
        wait (dut.rst_n === 1'b1); t0 = $realtime;
        #(130*OSC_T);
        ser_write(7'h08, 8'h04);                           // 2048 cycles, written at ~170 cycles
        wait (dut.inrush_active === 1'b0);
        w = ($realtime - t0) / OSC_T;
        $display("  extended mask: %0d cycles", w);
        if (w < 2047 || w > 2050) begin errors = errors + 1; $display("  FAIL extended mask %0d cycles", w); end
        checks = checks + 1;
        // and a re-enable in retrigger mode starts a fresh window with the current value (T09 covers timing)
        end_test;

        // ------------------------------------------------------------
        begin_test("E3 SOFT_TIME atomic on the _L write, no transient, no 0x0000");
        ser_write(7'h0B, 8'h00);
        ser_write(7'h05, 8'h01); ser_write(7'h04, 8'h00);
        check("SOFT_TIME = 0x0100", dut.u_regfile.soft_time, 16'h0100);
        st_old = 16'h0100; st_new = 16'h00FF; st_changes = 0; st_bad = 0; st_mon = 1;
        ser_write(7'h05, 8'h00);
        check("after _H write: unchanged 0x0100", dut.u_regfile.soft_time, 16'h0100);
        ser_write(7'h04, 8'hFF);
        check("after _L write: 0x00FF", dut.u_regfile.soft_time, 16'h00FF);
        st_old = 16'h00FF; st_new = 16'h0100;
        ser_write(7'h05, 8'h01);
        check("after _H write: unchanged 0x00FF", dut.u_regfile.soft_time, 16'h00FF);
        ser_write(7'h04, 8'h00);
        check("after _L write: 0x0100", dut.u_regfile.soft_time, 16'h0100);
        st_mon = 0;
        check("exactly two changes, one per _L write", st_changes, 2);
        check("no transient value", st_bad, 0);
        // R5 scenario under load: continuous soft overload, window shortened 0x0100 -> 0x00FF
        ser_write(7'h08, 8'h00); ser_write(7'h0B, 8'h01);
        over_soft = 1; wait_cycles(2000);
        ser_write(7'h05, 8'h00); ser_write(7'h04, 8'hFF);
        check("no soft trip while the window changes", trip, 0);
        over_soft = 0; wait_cycles(10);
        ser_write(7'h0B, 8'h03); ser_write(7'h04, 8'h27);   // back to 0x0027
        end_test;

        // ------------------------------------------------------------
        begin_test("E4 EN low < 8 samples: no reset, latched trip kept");
        ser_write(7'h03, 8'h11); ser_write(7'h07, 8'h04);
        over_hard = 1; wait_trip(1, 20, w); over_hard = 0;
        check("latched hard trip before the glitches", {trip, tripped}, 2'b11);
        rst_falls = 0;
        @(posedge osc_clk); #37;                           // arbitrary phase
        en = 0; #(1*OSC_T);   check("gate_en low during the glitch", gate_en, 0); en = 1; wait_cycles(20);
        en = 0; #(4*OSC_T);   en = 1; wait_cycles(20);
        en = 0; #(6.5*OSC_T); en = 1; wait_cycles(20);
        // a train: 6.5 cycles low, 1.5 high, five times (every high sample restarts the count)
        for (i = 0; i < 5; i = i + 1) begin en = 0; #(6.5*OSC_T); en = 1; #(1.5*OSC_T); end
        wait_cycles(20);
        check("no core reset from any glitch", rst_falls, 0);
        check("digital trip kept", {trip, trip_d, trip_cause}, {1'b1, 1'b1, 2'd2});
        check("G1_GATE latch set again by trip_d after EN returns", tripped, 1);
        #(130*OSC_T);
        ser_check(7'h03, 8'h11, "DAC_HARD kept");
        ser_check(7'h0B, 8'h03, "MODE kept");
        end_test;

        // ------------------------------------------------------------
        begin_test("E5 EN low >= 8 samples resets; latencies (E8 release)");
        rst_falls = 0;
        @(posedge osc_clk); #37;
        en = 0; t0 = $realtime; #(9*OSC_T); en = 1;
        wait_cycles(10);
        check("one core reset from a 9-cycle EN low", rst_falls, 1);
        // EN returned high before the core reset (10 cycles): the G1_GATE latch was set again
        // by the still-high trip_d, and the core re-adopts it after release (safe side)
        check("9-cycle EN low: latched trip re-adopted (cause hard)", {trip, tripped, trip_cause}, {1'b1, 1'b1, 2'd2});
        #(130*OSC_T);
        ser_check(7'h03, 8'hFE, "DAC_HARD back to reset");
        ser_check(7'h0B, 8'h23, "MODE back to reset");
        // EN low 20 cycles (> 11): trip_d falls while EN is still low, both latches clear
        en = 0; #(20*OSC_T); en = 1; wait_cycles(10);
        check("20-cycle EN low: both latches clear", {trip, tripped}, 2'b00);
        #(130*OSC_T);
        // latency EN fall -> rst_n fall, and EN rise -> rst_n rise
        @(posedge osc_clk); #37;
        en = 0; t0 = $realtime;
        wait (dut.rst_n === 1'b0); w = ($realtime - t0) / OSC_T;
        $display("  EN fall -> core reset: %0d cycles (filter 8 samples + 2 sync + 1)", w);
        if (w < 9 || w > 11) begin errors = errors + 1; $display("  FAIL reset latency %0d", w); end
        checks = checks + 1;
        #(20*OSC_T);
        @(posedge osc_clk); #37;
        en = 1; t0 = $realtime;
        wait (dut.rst_n === 1'b1); w = ($realtime - t0) / OSC_T;
        $display("  E8 EN rise -> core release: %0d cycles (was 2; host rule 128 unchanged)", w);
        if (w > 6) begin errors = errors + 1; $display("  FAIL release latency %0d", w); end
        checks = checks + 1;
        #(130*OSC_T);
        ser_check(7'h00, 8'h47, "CHIP_ID after release");
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
