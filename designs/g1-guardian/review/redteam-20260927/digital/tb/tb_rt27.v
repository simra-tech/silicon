// Red-team 2026-09-27 (designs/g1-guardian/review/redteam-20260927/digital/FINDINGS.md).
// Environment copied from blocks/g1_ctrl/sim/eco_20260925/tb_redteam_eco.v (G1_GATE latch model,
// dynamic comparators, por_n tied 1). New tests U1-U4: single-event upsets of one flop of the
// serial write hand-over (wr_tog_d, osc_clk side) and of the reset synchroniser (rs0).
// Upset model: the flop output is inverted from a time between two osc_clk edges until just
// after the next rising edge (at which the flop reloads its D input), exactly the lifetime of a
// flipped state bit. RTL: procedural write of the reg; gate level: force/release of the Q net.
// A FAIL line is a reproduced hazard (the register map promises otherwise).
`timescale 1ns/1ps


module tb_rt27;
    localparam real OSC_T  = 100.0;
    real            SCLK_T = 200.0;

    reg        osc_clk = 0;
    reg        en      = 0;          // R1 (map 1.2): EN low from power-up, contract P4/P6
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
`ifdef GLS
    wire p_rs1 = dut.\u_core.rs1 ;     // flat netlist keeps the flop net name
`else
    wire p_rs1 = dut.u_core.rs1;
`endif
    // R1 monitor: gate_core must never be 1 (or unknown) while EN is low
    integer gate_bad = 0;
    always @(gate_pad or en) if (en === 1'b0 && gate_pad !== 1'b0) gate_bad = gate_bad + 1;

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


    reg  [7:0] d8;
    integer    w;
    task upset_wr_tog_d;
        begin
            @(negedge osc_clk);
`ifdef GLS
            force dut.\u_core.u_serial.wr_tog_d  = ~dut.\u_core.u_serial.wr_tog_d ;
            @(posedge osc_clk); #1; release dut.\u_core.u_serial.wr_tog_d ;
`else
            dut.u_core.u_serial.wr_tog_d = ~dut.u_core.u_serial.wr_tog_d;
`endif
            $display("  (upset: wr_tog_d inverted for one osc_clk cycle at %0d ns)", $time);
            wait_cycles(10);
        end
    endtask
    task upset_chain_input;    // one upset entering the plain SEU register (stands in for a real SEU)
        begin
            @(negedge osc_clk);
`ifdef GLS
            force dut.\u_core.u_seu.u_plain.d[0]  = ~dut.\u_core.u_seu.u_plain.d[0] ;
            @(posedge osc_clk); #1; release dut.\u_core.u_seu.u_plain.d[0] ;
`else
            @(posedge osc_clk); #1; dut.u_core.u_seu.u_plain.q[0] = ~dut.u_core.u_seu.u_plain.q[0];
`endif
        end
    endtask
    task upset_rs0;
        begin
            @(negedge osc_clk);
`ifdef GLS
            force dut.\u_core.rs0  = 1'b0; @(posedge osc_clk); #1; release dut.\u_core.rs0 ;
`else
            dut.u_core.rs0 = 1'b0;
`endif
            $display("  (upset: rs0 0 for one osc_clk cycle at %0d ns)", $time);
            wait_cycles(10);
        end
    endtask

    initial begin
        en = 0; #(20*OSC_T); en = 1; #(150*OSC_T);
        ser_read(7'h01, d8); check("VERSION 0x12", d8, 8'h12);
        idle_resync; ser_write(7'h08, 8'h00);   // INRUSH 0 (window over anyway: 1024 cycles pass below)
        wait_cycles(1100);

        // ============================================================
        begin_test("U1 latched trip, host's last write was CTRL.CLEAR; one upset of wr_tog_d");
        over_hard = 1; wait_trip(200, w); over_hard = 0;
        check("hard trip latched", trip, 1);
        idle_resync; ser_write(7'h0C, 8'h01);  // CLEAR
        wait_cycles(20);
        check("CLEAR cleared the trip", trip, 0);
        over_hard = 1; wait_trip(200, w); over_hard = 0;     // second fault, latched mode (RETRIG 0)
        wait_cycles(20);
        check("second fault latched (trip)", trip, 1);
        check("second fault latched (G1_GATE latch)", tripped, 1);
        upset_wr_tog_d;
        check("latched trip survives a single upset (map: holds until CLEAR or EN)", trip, 1);
        check("G1_GATE latch still set (GATE off)", tripped, 1);
        idle_resync; ser_read(7'h0D, d8); observe("STATUS after upset", d8);
        end_test;

        // ============================================================
        begin_test("U2 same, but the host follows CLEAR with a no-op write CTRL = 0x00 (host mitigation)");
        idle_resync; ser_write(7'h0C, 8'h01); wait_cycles(20);
        idle_resync; ser_write(7'h0C, 8'h00); wait_cycles(20);
        over_hard = 1; wait_trip(200, w); over_hard = 0; wait_cycles(20);
        check("fault latched", trip, 1);
        upset_wr_tog_d;
        check("latched trip survives the upset", trip, 1);
        check("G1_GATE latch still set", tripped, 1);
        end_test;

        // ============================================================
        begin_test("U3 SEU counters: host's last write was SEU_CMD.CLR_CNT (start of a run); one upset of wr_tog_d");
        idle_resync; ser_write(7'h0C, 8'h01); wait_cycles(20);      // clear trip
        idle_resync; ser_write(7'h19, 8'h01); wait_cycles(20);      // CLR_CNT: last host write
        upset_chain_input; wait_cycles(300);                        // one upset during the run
        idle_resync; ser_read(7'h1B, d8); check("SEU_PLAIN_L = 1 after one upset in the chain", d8, 8'h01);
        upset_wr_tog_d; wait_cycles(20);                            // replays CLR_CNT?
        idle_resync; ser_read(7'h1B, d8); check("SEU_PLAIN_L kept (counts are the measurement)", d8, 8'h01);
        end_test;

        // ============================================================
        begin_test("U4 one upset of the reset synchroniser flop rs0 while armed with host settings");
        idle_resync; ser_write(7'h0C, 8'h01); wait_cycles(20);
        idle_resync; ser_write(7'h03, 8'hC8);                       // DAC_HARD 200
        idle_resync; ser_write(7'h0B, 8'h23);                       // MODE: FAST_EN
        wait_cycles(20);
        check("DAC_HARD 200 before", dac_hard, 8'hC8);
        check("fast_en 1 before", fast_en, 1);
        upset_rs0;
        check("DAC_HARD kept after one rs0 upset", dac_hard, 8'hC8);
        check("fast_en kept after one rs0 upset", fast_en, 1);
        idle_resync; ser_read(7'h0D, d8); observe("STATUS after rs0 upset (bit 3 = INRUSH_ACTIVE)", d8);
        end_test;

        $display("RT27 DONE: %0d tests passed, %0d failed (FAIL = hazard reproduced), %0d checks, %0d failed checks",
                 tests_pass, tests_fail, checks, errors);
        $finish;
    end
endmodule
