// Unit testbench for g1_seu: fill, pattern selection, fault injection into
// the plain register and into one or two TMR copies by hierarchical
// assignment (bit flips in the flops themselves), counter behaviour, divided
// shifting, static mode, saturation of the 8-bit counter.
// Run: ../../g1_ctrl/sim/run_sim.sh
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps

module tb_g1_seu;
    reg         clk = 0, rst_n = 0;
    reg         scrub_en = 1;
    reg  [1:0]  pattern = 0;
    reg         clr_cnt = 0, inj_plain = 0, inj_tmr = 0;
    wire [15:0] cnt_plain, cnt_corr;
    wire [7:0]  cnt_unc, run_max;
    wire        active, filling;

    g1_seu #(.PLAIN_LEN(1024), .TMR_LEN(256)) dut (
        .clk(clk), .rst_n(rst_n), .scrub_en(scrub_en), .pattern(pattern),
        .clr_cnt(clr_cnt), .inj_plain(inj_plain), .inj_tmr(inj_tmr),
        .cnt_plain(cnt_plain), .cnt_corr(cnt_corr), .cnt_unc(cnt_unc), .run_max(run_max),
        .active(active), .filling(filling));

    always #50 clk = ~clk;

    integer errors = 0, checks = 0, tests_pass = 0, tests_fail = 0, test_err, i;
    reg [8*80-1:0] test_name;
    task begin_test(input [8*80-1:0] name); begin test_name = name; test_err = errors; end endtask
    task end_test; begin
        if (errors == test_err) begin tests_pass = tests_pass + 1; $display("PASS %0s", test_name); end
        else begin tests_fail = tests_fail + 1; $display("FAIL %0s", test_name); end
    end endtask
    task check(input [8*64-1:0] what, input [31:0] got, input [31:0] exp); begin
        checks = checks + 1;
        if (got !== exp) begin errors = errors + 1; $display("  FAIL %0t %0s: got %0d expected %0d", $time, what, got, exp); end
    end endtask
    task cyc(input integer n); begin repeat (n) @(posedge clk); #1; end endtask
    task pulse_clr; begin clr_cnt = 1; cyc(1); clr_cnt = 0; end endtask

    // count how many cycles the plain chain content is a perfect checkerboard
    function chain_is_checkerboard(input dummy);
        integer k; reg ok;
        begin
            ok = 1;
            for (k = 1; k < 1024; k = k + 1) if (dut.u_plain.q[k] == dut.u_plain.q[k-1]) ok = 0;
            chain_is_checkerboard = ok;
        end
    endfunction

    initial begin
        $dumpfile("tb_g1_seu.vcd");
        $dumpvars(0, tb_g1_seu);
        #120 rst_n = 1; cyc(2);

        begin_test("S01 fill then active, no false counts");
        check("filling", filling, 1); check("active", active, 0);
        cyc(1024); cyc(2);
        check("active after 1024 shifts", active, 1);
        check("checkerboard in chain", chain_is_checkerboard(0), 1);
        check("TMR copies agree", dut.disagree, 0);
        cyc(3000);
        check("plain 0", cnt_plain, 0); check("corr 0", cnt_corr, 0); check("unc 0", cnt_unc, 0);
        end_test;

        begin_test("S02 single flip in plain register counts once, run 1");
        dut.u_plain.q[500] = ~dut.u_plain.q[500];
        cyc(1030);
        check("plain 1", cnt_plain, 1); check("corr 0", cnt_corr, 0); check("unc 0", cnt_unc, 0);
        check("run_max 1", run_max, 1);
        end_test;

        begin_test("S03 single flip in one TMR copy: corrected, counted once, no output error");
        dut.u_tmr_b.q[100] = ~dut.u_tmr_b.q[100];
        #1 check("disagree visible", dut.disagree, 1);
        cyc(1);
        check("corrected at next shift", dut.disagree, 0);
        cyc(300);
        check("corr 1", cnt_corr, 1); check("unc 0", cnt_unc, 0); check("plain still 1", cnt_plain, 1);
        end_test;

        begin_test("S04 flip in two copies of the same stage: uncorrectable");
        dut.u_tmr_a.q[200] = ~dut.u_tmr_a.q[200];
        dut.u_tmr_c.q[200] = ~dut.u_tmr_c.q[200];
        cyc(300);
        check("corr 2", cnt_corr, 2); check("unc 1", cnt_unc, 1);
        end_test;

        begin_test("S05 burst of 5 adjacent plain flips: count 5, run 5");
        pulse_clr;
        for (i = 10; i < 15; i = i + 1) dut.u_plain.q[i] = ~dut.u_plain.q[i];
        cyc(1030);
        check("plain 5", cnt_plain, 5); check("run_max 5", run_max, 5);
        end_test;

        begin_test("S06 register-driven injection pulses");
        pulse_clr;
        inj_plain = 1; cyc(1); inj_plain = 0;
        cyc(1030);
        check("plain 1", cnt_plain, 1);
        inj_tmr = 1; cyc(1); inj_tmr = 0;
        cyc(300);
        check("corr 1", cnt_corr, 1); check("unc 0", cnt_unc, 0);
        end_test;

        begin_test("S07 pattern change restarts fill; all-ones and all-zeros");
        pulse_clr;
        pattern = 2; cyc(3);
        check("filling after pattern change", filling, 1);
        cyc(1030);
        check("active", active, 1);
        check("chain all ones", &dut.u_plain.q, 1);
        cyc(500);
        check("no false counts", cnt_plain + cnt_corr + cnt_unc, 0);
        pattern = 1; cyc(1040);
        check("chain all zeros", |dut.u_plain.q, 0);
        dut.u_plain.q[3] = 1;
        cyc(1030);
        check("plain 1 with zeros pattern", cnt_plain, 1);
        pattern = 0; cyc(1040);
        end_test;

        begin_test("S08 constant pattern holds static data: flops do not toggle, upsets counted");
        pulse_clr;
        pattern = 2; cyc(1040);
        check("all ones", &dut.u_plain.q, 1);
        i = dut.u_plain.q[600]; cyc(50);
        check("bit static over 50 clocks", dut.u_plain.q[600], i);
        dut.u_plain.q[600] = ~dut.u_plain.q[600];
        dut.u_tmr_a.q[5]   = ~dut.u_tmr_a.q[5];
        cyc(1030);
        check("plain 1", cnt_plain, 1); check("corr 1", cnt_corr, 1); check("unc 0", cnt_unc, 0);
        pattern = 0; cyc(1040);
        end_test;

        begin_test("S09 300 output-stage flips count 300; run_max saturates at 255");
        pulse_clr;
        for (i = 0; i < 300; i = i + 1) begin dut.u_plain.q[1023] = ~dut.u_plain.q[1023]; cyc(1); end
        check("300 flips at the output stage count 300", cnt_plain, 300);
        check("run_max 255 saturated (8-bit)", run_max, 255);
        end_test;

        begin_test("S10 8-bit uncorrectable counter saturates at 255");
        pulse_clr;
        for (i = 0; i < 260; i = i + 1) begin
            dut.u_tmr_a.q[250] = ~dut.u_tmr_a.q[250];
            dut.u_tmr_b.q[250] = ~dut.u_tmr_b.q[250];
            cyc(8);
        end
        cyc(20);
        check("unc saturated", cnt_unc, 255);
        end_test;

        begin_test("S11 scrub disabled: registers keep shifting, nothing counts; re-enable refills");
        pulse_clr; scrub_en = 0; cyc(5);
        dut.u_plain.q[600] = ~dut.u_plain.q[600];
        cyc(2000);
        check("no count", cnt_plain, 0); check("not active", active, 0);
        scrub_en = 1; cyc(3);
        check("filling after re-enable", filling, 1);
        cyc(1030); check("active", active, 1); check("still no count", cnt_plain, 0);
        end_test;

        $display("SUMMARY tests_pass=%0d tests_fail=%0d checks=%0d errors=%0d", tests_pass, tests_fail, checks, errors);
        if (errors == 0) $display("ALL TESTS PASSED"); else $display("SOME TESTS FAILED");
        $finish;
    end
endmodule
