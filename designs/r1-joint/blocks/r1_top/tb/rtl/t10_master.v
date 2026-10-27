// R1 full-chip testbench (track T10): host and bench master model. TESTBENCH ONLY, not chip logic.
// It drives the pads CS_N, MA/SCLK, SDI, EN/STO_IN (through dac_bridge at 3.3 V and the board resistors) and the
// stimulus selector of the shunt sources; it reads SLO/SDO, FAULT_N and GATE_A at the pads (adc_bridge, 1.65 V).
// One test per compile: -DT10_TEST=<n> (1 power-up, 2 encoder, 3 current, 4 safety, 5 thermal + oscillator).
// Result lines "T10RES <key> t=<ns> ..." are parsed by tb/post_tb.py. Procedures follow R1_REGISTER_MAP.md 0.5.
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
`ifndef T10_SETTLE_NS
`define T10_SETTLE_NS 14000.0
`endif
`ifndef T10_TEST
`define T10_TEST 1
`endif
module t10_master (
    input  wire       slo_pad, fault_pad, gate_a_pad, por_obs,
    output reg        m_cs_n, m_sclk, m_sdi, m_en, tb_rst_n,
    output reg  [2:0] sel_a, sel_b
);
    real sck_half;                  // SPI half period, ns
    real ma_half;                   // BiSS half period, ns
    initial begin
        m_cs_n = 1'b1; m_sclk = 1'b1; m_sdi = 1'b0; m_en = 1'b1; sel_a = 3'd0; sel_b = 3'd0;
`ifdef T10_SCK_HALF_NS
        sck_half = `T10_SCK_HALF_NS; // fifth budget: slower SCLK moves the SPI edges against the clk30 edges
`else
        sck_half = 25.0;            // 20 MHz SPI (README: SCLK choice)
`endif
        ma_half = 50.0;             // 10 MHz BiSS MA (S2 maximum)
        tb_rst_n = (`T10_TEST == 1) ? 1'b1 : 1'b0;
    end

    // ---------------- SPI host (mode 0, 24-bit frames; R1_REGISTER_MAP 2.1) ----------------
    reg [23:0] mi; reg [15:0] rd_val; reg [7:0] rd_stat; real t_cs;
    task spi_x; input [23:0] mo; input integer nbits; integer i; begin
        m_sclk = 1'b0; #(sck_half); m_cs_n = 1'b0; #(sck_half); mi = 24'd0;
        for (i = nbits - 1; i >= 0; i = i - 1) begin
            m_sdi = mo[i]; #(sck_half); m_sclk = 1'b1; mi[i] = slo_pad; #(sck_half); m_sclk = 1'b0;
        end
        #(sck_half); m_cs_n = 1'b1; t_cs = $realtime;
        #(300.0);                   // CS_N high >= 8 ticks (267 ns at 30 MHz, 2.1)
    end endtask
    task spi_wr; input [6:0] a; input [15:0] d; begin
        spi_x({1'b0, a, d}, 24); shadow_wr(a, d);
        $display("T10RES SPIWR t=%0.1f addr=%02h data=%04h", t_cs, a, d);
    end endtask
    // read with the pipelined reply: the command frame, then a frame that returns the data
    real t_rd;
    task spi_rd; input [6:0] a; begin
        spi_x({1'b1, a, 16'd0}, 24); t_rd = t_cs; spi_x({1'b1, 7'h00, 16'd0}, 24);
        rd_val = mi[15:0]; rd_stat = mi[23:16];
        $display("T10RES SPIRD t=%0.1f addr=%02h data=%04h status=%02h", t_rd, a, rd_val, rd_stat);
    end endtask

    // ---------------- CAL_CRC from a host shadow of the 43 covered words (4.4) ----------------
    // reset values as they read back (R1_REGISTER_MAP 4.4, 4.10, 4.11); the RTL-only helper rtl/tb_crc_reset.v read the
    // same words over SPI and got 0xBA (run crc-reset); the master checks its own value against it at start.
    reg [15:0] sh [0:127];
    integer k;
    initial begin
        for (k = 0; k < 128; k = k + 1) sh[k] = 16'd0;
        sh[7'h12] = 16'h4000; sh[7'h14] = 16'h4000; sh[7'h17] = 16'h0164;
        sh[7'h36] = 16'h3F3F; sh[7'h37] = 16'h3F3F; sh[7'h39] = 16'h4E00; sh[7'h3A] = 16'h2020; sh[7'h3B] = 16'h2020;
        sh[7'h3C] = 16'h3748;
`ifdef T10_CTRL07
        // ctrl 0.7: CMP_THR_A/B reset 0x003F (was 0x3F3F); the CAL_CRC shadow must follow, or CAL_VALID stays 0
        sh[7'h36] = 16'h003F; sh[7'h37] = 16'h003F;
`endif
        sh[7'h50] = 1; sh[7'h51] = 2; sh[7'h52] = 5; sh[7'h53] = 10; sh[7'h54] = 20; sh[7'h55] = 39; sh[7'h56] = 79;
        sh[7'h57] = 158; sh[7'h58] = 315; sh[7'h59] = 508; sh[7'h5A] = 1016; sh[7'h5B] = 2032; sh[7'h5C] = 4065;
        sh[7'h5D] = 8130;
        for (k = 0; k < 14; k = k + 1) sh[7'h60 + k] = sh[7'h50 + k];
    end
    task shadow_wr; input [6:0] a; input [15:0] d; begin sh[a] = d; end endtask
    reg [7:0] crc_r;
    task crc_word; input [15:0] w; integer j; begin
        crc_r = crc_r ^ w[15:8]; for (j = 0; j < 8; j = j + 1) crc_r = crc_r[7] ? ({crc_r[6:0], 1'b0} ^ 8'h07) : {crc_r[6:0], 1'b0};
        crc_r = crc_r ^ w[7:0];  for (j = 0; j < 8; j = j + 1) crc_r = crc_r[7] ? ({crc_r[6:0], 1'b0} ^ 8'h07) : {crc_r[6:0], 1'b0};
    end endtask
    task calc_crc; integer a; begin
        crc_r = 8'hFF;
        for (a = 8'h10; a <= 8'h17; a = a + 1) crc_word(sh[a]);
        for (a = 8'h36; a <= 8'h3C; a = a + 1) crc_word(sh[a]);
        for (a = 8'h50; a <= 8'h5D; a = a + 1) crc_word(sh[a]);
        for (a = 8'h60; a <= 8'h6D; a = a + 1) crc_word(sh[a]);
    end endtask
    task write_crc; begin calc_crc; spi_wr(7'h18, {8'd0, crc_r}); end endtask

    // ---------------- BiSS-C master (copied from r1_ctrl tb/tb_top.v biss_frame, event waits) ----------------
    reg [63:0] b_bits; integer b_start_edge; reg b_ack_ok, b_stop_ok, b_cds; reg [35:0] b_data;
    reg [5:0] b_crc_wire, b_crc_calc; real b_lat_t;
    function [5:0] crc6; input [35:0] d; input integer n; integer i; reg [5:0] c; reg fb; begin
        c = 6'd0;
        for (i = n - 1; i >= 0; i = i - 1) begin fb = c[5] ^ d[i]; c = {c[4:0], 1'b0}; if (fb) c = c ^ 6'h03; end
        crc6 = c;
    end endfunction
    task biss_frame; input integer ndata; integer kk, got, need, j; reg s; begin
        kk = 0; got = 0; b_start_edge = 0; b_bits = 64'd0; b_ack_ok = 0; b_stop_ok = 0; need = 1 + ndata + 6;
        wait (slo_pad === 1'b1);
        m_sclk = 1'b0; #(ma_half);
        while ((b_start_edge == 0 || got < need + 1) && kk < 200) begin
            m_sclk = 1'b1; kk = kk + 1; if (kk == 1) b_lat_t = $realtime;
            #(ma_half); s = slo_pad; m_sclk = 1'b0;
            if (kk == 2) b_ack_ok = (s == 1'b0);
            else if (kk >= 3 && b_start_edge == 0) begin if (s) b_start_edge = kk; end
            else if (b_start_edge != 0) begin if (got < need) b_bits[63 - got] = s; else b_stop_ok = (s == 1'b0); got = got + 1; end
            #(ma_half);
        end
        m_sclk = 1'b1;              // CDM = 0
        b_cds = b_bits[63]; b_data = 36'd0;
        for (j = 0; j < ndata; j = j + 1) b_data[ndata - 1 - j] = b_bits[62 - j];
        for (j = 0; j < 6; j = j + 1) b_crc_wire[5 - j] = b_bits[62 - ndata - j];
        b_crc_calc = ~crc6(b_data, ndata);   // sent inverted (3.1)
        $display("T10RES BISS t_lat=%0.1f ack=%0d start_edge=%0d stop=%0d cds=%0d data=%09h crc_wire=%02h crc_calc=%02h",
                 b_lat_t, b_ack_ok, b_start_edge, b_stop_ok, b_cds, b_data, b_crc_wire, b_crc_calc);
    end endtask

    // OSC_COUNT reference: n SCLK periods at period p (ns) inside one CS_N-low frame (counted as an SPI error, 4.3)
    task ref_clocks; input integer n; input real p; integer i; begin
        m_sclk = 1'b0; #(p); m_cs_n = 1'b0; #(p);
        for (i = 0; i < n; i = i + 1) begin #(p / 2); m_sclk = 1'b1; #(p / 2); m_sclk = 1'b0; end
        #(p); m_cs_n = 1'b1; #(400.0);
        $display("T10RES REFCLK t=%0.1f n=%0d period_ns=%0.3f", $realtime, n, p);
    end endtask

    // testbench reset pulse for the decks that start from the operating point (tests 2-5)
    task tb_reset; begin
        tb_rst_n = 1'b0; #(200.0); tb_rst_n = 1'b1;
        $display("T10RES TBRESET t=%0.1f", $realtime);
        #(1000.0);                  // reset release (2 ticks), pre-charge hold, first frames (4.11)
    end endtask

    integer n, cnt; real t0, t1;
    integer ga_rises = 0;
    always @(posedge gate_a_pad) ga_rises = ga_rises + 1;
    initial begin
        #1;
        calc_crc; $display("T10RES CRC_RESET value=%02h", crc_r);
        if (`T10_TEST == 1) begin
            // ---- test 1: power-up. The board ramps the supplies (deck). Host waits, then reads ID. ----
            wait (por_obs === 1'b1);
            $display("T10RES POR_RELEASE t=%0.1f", $realtime);
            #(2000.0);
            spi_rd(7'h00);          // ID
            spi_rd(7'h01);          // STATUS
            spi_rd(7'h02);          // FAULT (POR bit 12 expected)
            $display("T10RES DONE t=%0.1f", $realtime);
        end
        if (`T10_TEST == 2) begin
            // ---- test 2: encoder path, SPI reads (POS, MEAS_ANGLE, STATUS, ID), one BiSS-C frame ----
            #(`T10_SETTLE_NS); tb_reset;
            spi_wr(7'h07, 16'd64);  // TIMEOUT_TICKS 64 (about 2.1 us; deviation D3)
            write_crc;              // CAL_VALID = 1 so that nW = 1 in the frame
`ifdef T10_T2_WAIT_NS
            // fourth budget: wait until the tracking loop has locked (POS_VALID: 16 pairs with |e| < 11.25 deg
            // after the acquisition, about 21 us after the reset at the reset loop gains) before the reads
            #(`T10_T2_WAIT_NS);
`endif
`ifndef T10_T2_NO_CLR
            // fifth budget: register map section 4 step 4, CTRL.CLR after CAL_CRC; without it POR (bit 12) stays
            // latched, STATUS.FAULT = 1 and the BiSS frame has nW = 0 (t10-t2-fast-h, -07-g/h: STATUS 0x01D0)
            spi_wr(7'h04, 16'h0001);
`endif
            // pipelined reads: each frame returns the register named in the previous frame
            spi_x({1'b1, 7'h19, 16'd0}, 24); t0 = t_cs;
            spi_x({1'b1, 7'h1F, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=19 data=%04h status=%02h", t0, mi[15:0], mi[23:16]); t0 = t_cs;
            spi_x({1'b1, 7'h19, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=1f data=%04h status=%02h", t0, mi[15:0], mi[23:16]); t0 = t_cs;
            spi_x({1'b1, 7'h01, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=19 data=%04h status=%02h", t0, mi[15:0], mi[23:16]); t0 = t_cs;
            spi_x({1'b1, 7'h00, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=01 data=%04h status=%02h", t0, mi[15:0], mi[23:16]);
            // mode switch to BiSS (register map 1, steps 5-6): CS_N is high, MA high, wait one timeout
            m_sclk = 1'b1; #(2500.0);
            biss_frame(36);         // MT 16 + ST 18 + nE + nW
            #(500.0);
            $display("T10RES DONE t=%0.1f", $realtime);
        end
        if (`T10_TEST == 3) begin
            // ---- test 3: DC shunt levels (deck), current frame at the PWM centre strobe, no auto-zero (AZ_LEN 0) ----
            #(`T10_SETTLE_NS); tb_reset;
            spi_wr(7'h20, 16'd64);            // PWM_PERIOD 64 ticks (2.13 us; compressed, D7)
            spi_wr(7'h21, 16'd40);            // DUTY_A 40: strobe at tick 20 (DUTY_A >= 2 DEAD + 2)
            for (n = 0; n < 2; n = n + 1) begin   // levels 0 and 1 (D7)
                sel_a = n; sel_b = n;
                $display("T10RES SEL t=%0.1f sel=%0d", $realtime, n);
                #(2300.0);                    // one PWM period: one current frame after the level change
                spi_x({1'b1, 7'h29, 16'd0}, 24); t0 = t_cs;
                spi_x({1'b1, 7'h2A, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=29 data=%04h status=%02h", t0, mi[15:0], mi[23:16]); t0 = t_cs;
                spi_x({1'b1, 7'h00, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=2a data=%04h status=%02h", t0, mi[15:0], mi[23:16]);
            end
            $display("T10RES DONE t=%0.1f", $realtime);
        end
        if (`T10_TEST == 4) begin
            // ---- test 4: PWM 160 ticks, all three windows 0..120 (on 90 ticks = 3 us), OC_A threshold 44 ----
            #(`T10_SETTLE_NS); tb_reset;
            // CMP_THR: THR_NEG 0 (cell code c = 63: NEG never trips). The reset value THR_NEG 63 (c = 0) trips NEG at
            // zero current, and CLR does not clear an active source (finding R4; the first sequence wrote 63, F20)
            spi_wr(7'h36, 16'h002C);          // CMP_THR_A: THR_OC_A 44, THR_NEG_A 0
            spi_wr(7'h37, 16'h003F);          // CMP_THR_B: THR_OC_B 63, THR_NEG_B 0
            write_crc;                        // CRC check runs (<= 174 ticks) during the next writes
            spi_wr(7'h20, 16'd100);           // PWM_PERIOD 100 ticks (3.3 us; compressed, D7)
            spi_wr(7'h21, 16'd75); spi_wr(7'h22, 16'd75); spi_wr(7'h23, 16'd75);      // DUTY_A/B/C
            spi_wr(7'h03, 16'h000E);          // FAULT_MASK: only OC_A latches
            spi_wr(7'h04, 16'h0003);          // CLR and GATE_EN in one write (D7)
            sel_a = 3'd1;                     // ISA 30 mV while A is on (below the threshold)
            @(posedge gate_a_pad); #(800.0);
            sel_a = 3'd3;                     // step to 100 mV inside the on-window
            $display("T10RES OCSTEP t=%0.1f", $realtime);
            #(1500.0);
            sel_a = 3'd1;
            spi_wr(7'h04, 16'h0003);          // CLR (source inactive: gates off), GATE_EN kept
            cnt = ga_rises; #(3600.0);
            $display("T10RES RESUME1 t=%0.1f gate_a_rises=%0d", $realtime, ga_rises - cnt);
            @(posedge gate_a_pad); #(800.0);
            m_en = 1'b0;                      // EN/STO_IN low inside the on-window
            $display("T10RES ENLOW t=%0.1f", $realtime);
            #(1200.0);
            spi_rd(7'h02);                    // FAULT: STO (bit 8)
            m_en = 1'b1; #(300.0);
            $display("T10RES ENHIGH t=%0.1f", $realtime);
            spi_wr(7'h04, 16'h0003);          // CLR, GATE_EN kept
            cnt = ga_rises; #(3600.0);
            $display("T10RES RESUME2 t=%0.1f gate_a_rises=%0d", $realtime, ga_rises - cnt);
            $display("T10RES DONE t=%0.1f", $realtime);
        end
        if (`T10_TEST == 5) begin
            // ---- test 5: T2F count in TEMP (window 2^8 ticks, the minimum) ----
            #(`T10_SETTLE_NS); tb_reset;
            spi_wr(7'h34, 16'd8);             // T2F_WIN 2^8 ticks (8.5 us at 30 MHz; wall-time budget)
            t1 = $realtime;
            #(18000.0);                       // two complete windows after the write
            spi_rd(7'h2B);                    // TEMP
            $display("T10RES DONE t=%0.1f", $realtime);
        end
        if (`T10_TEST == 6) begin
            // ---- test 6: OSC_COUNT against the transistor-level r1_osc (reference 4 MHz on SCLK) ----
            #(`T10_SETTLE_NS); tb_reset;
            spi_wr(7'h08, 16'h0116);          // OSC_CFG: MEAS, trim 22
            ref_clocks(24, 100.0);            // 24 periods at 10 MHz (16 counted; compressed, D7)
            #(600.0);
            spi_x({1'b1, 7'h01, 16'd0}, 24);
            spi_x({1'b1, 7'h09, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=01 data=%04h status=%02h", t_cs, mi[15:0], mi[23:16]);
            spi_x({1'b1, 7'h00, 16'd0}, 24); $display("T10RES SPIRD t=%0.1f addr=09 data=%04h status=%02h", t_cs, mi[15:0], mi[23:16]);
            $display("T10RES DONE t=%0.1f", $realtime);
        end
    end
endmodule
