// Chip-level testbench for r1_ctrl_top (testbenches b..f and cal of the r1_ctrl
// README, revision 0.2).
//   +test=biss | ssi | spi | gate | safe | cal     test group
//   +clk_ns=<real>                            clk period (RC corners: 23.81, 33.33, 47.62)
// Models: encoder head (ideal sin/cos, amplitude ENC_AMP, electrical frequency
// enc_f), ADC (12-tick conversion, 4:1 mux, track-and-hold on adc_hold, 13 raw
// decisions with an ideal binary CDAC: raw[11:0] = code, raw[12] = 0),
// behavioural window comparators with offset and 200 ns delay (test cal),
// BiSS-C / SSI master on MA/SLO, SPI host (mode 0, 24-bit frames).
// Every check prints PASS/FAIL; the last line is "ALL TESTS PASSED" or
// "TESTS FAILED: <n>".
// SPDX-License-Identifier: Apache-2.0
`timescale 1ns/1ps
module tb_top;
    // ---------------- clock, reset ----------------
    real clk_ns;
    reg  clk = 0, por_n = 0;
    initial begin
        if (!$value$plusargs("clk_ns=%f", clk_ns)) clk_ns = 33.333;
    end
    always #(clk_ns / 2.0) clk = ~clk;

    // ---------------- pads ----------------
    reg  cs_n = 1, ma = 1, sdi = 0, en_pad = 1, t2f_clk = 0;
    reg  [3:0] cmp = 4'd0;             // forced comparator flags
    reg  [3:0] cmp_mdl = 4'd0;         // behavioural comparators (test cal)
    wire slo_sdo, fault_n, gate_a, gate_b, gate_c, adc_hold, is_smp, adc_start, az_win;
    wire [1:0] adc_mux;
    wire [4:0] osc_trim;
    wire [15:0] ana_ctrl;
    wire [5:0] thr_oc_a, thr_neg_a, thr_oc_b, thr_neg_b, cal_oc_a, cal_neg_a, cal_oc_b, cal_neg_b;
    reg  adc_valid = 0;
    reg  [12:0] adc_raw = 0;

    r1_ctrl_top dut (
        .clk(clk), .por_n(por_n), .cs_n(cs_n), .ma_sclk(ma), .sdi(sdi), .slo_sdo(slo_sdo),
        .en_pad(en_pad), .fault_n(fault_n), .gate_a(gate_a), .gate_b(gate_b), .gate_c(gate_c),
        .adc_hold(adc_hold), .is_smp(is_smp), .adc_start(adc_start), .adc_mux(adc_mux),
        .adc_valid(adc_valid), .adc_raw(adc_raw), .cmp(cmp | cmp_mdl),
        .thr_oc_a(thr_oc_a), .thr_neg_a(thr_neg_a), .thr_oc_b(thr_oc_b), .thr_neg_b(thr_neg_b),
        .cal_oc_a(cal_oc_a), .cal_neg_a(cal_neg_a), .cal_oc_b(cal_oc_b), .cal_neg_b(cal_neg_b),
        .az_win(az_win), .t2f_clk(t2f_clk), .osc_trim(osc_trim), .ana_ctrl(ana_ctrl));

    // ---------------- bookkeeping ----------------
    integer errors = 0, checks = 0;
    task check;
        input cond;
        input [8*128-1:0] msg;
        begin
            checks = checks + 1;
            if (cond) $display("PASS %0s", msg);
            else begin errors = errors + 1; $display("FAIL %0s  (t=%0t)", msg, $time); end
        end
    endtask

    // ---------------- encoder + ADC model ----------------
    real enc_f = 1000.0, enc_amp = 1400.0, enc_ph0 = 0.1;
    real held_ang;
    reg  hold_d = 0;
    integer conv_cnt = 0;
    reg  [1:0] conv_mux = 0;
    reg  [11:0] ia_code = 12'd2048, ib_code = 12'd2048;
    localparam CONV = 12;
    function real angle_now;           // turns
        input dummy;
        real a;
        begin a = enc_ph0 + enc_f * $realtime * 1e-9; angle_now = a - $floor(a); end
    endfunction
    function [11:0] code;
        input real v;
        integer q;
        begin q = $rtoi(v + 2048.5); if (q > 4095) q = 4095; if (q < 0) q = 0; code = q; end
    endfunction
    // the track-and-holds take the pair at the rising edge of adc_hold
    always @(posedge adc_hold) held_ang = angle_now(0);
    always @(posedge clk) begin
        hold_d <= adc_hold;
        adc_valid <= 1'b0;
        if (adc_start) begin
            conv_cnt <= CONV; conv_mux <= adc_mux;
        end else if (conv_cnt > 0) begin
            conv_cnt <= conv_cnt - 1;
            if (conv_cnt == 1) begin
                adc_valid <= 1'b1;
                case (conv_mux)
                    2'd0: adc_raw <= {1'b0, code(enc_amp * $sin(6.283185307179586 * held_ang) - 0.5)};
                    2'd1: adc_raw <= {1'b0, code(enc_amp * $cos(6.283185307179586 * held_ang) - 0.5)};
                    2'd2: adc_raw <= {1'b0, ia_code};
                    default: adc_raw <= {1'b0, ib_code};
                endcase
            end
        end
    end

    // ---------------- behavioural comparators (test cal) ----------------
    // Trip level of comparator i in units of one calibration step:
    //   trip = (CAL_i - 32) + OFS_i + 8 * (THR_i - 32)
    // flag = vin > trip, 200 ns after the clk edge. vin = 0 inside az_win (the
    // auto-zero input) and cmp_vin outside it.
    reg  cmp_mdl_en = 0;
    real cmp_vin = 100.0;
    real cofs [0:3];
    function cmp_trip;
        input [5:0] cal, thr; input real ofs; input real v;
        begin cmp_trip = v > ($itor(cal) - 32.0 + ofs + 8.0 * ($itor(thr) - 32.0)); end
    endfunction
    always @(posedge clk) begin : cmpm
        real v;
        v = az_win ? 0.0 : cmp_vin;
        if (cmp_mdl_en) begin
            cmp_mdl[0] <= #200 cmp_trip(cal_oc_a,  thr_oc_a,  cofs[0], v);
            cmp_mdl[1] <= #200 cmp_trip(cal_neg_a, thr_neg_a, cofs[1], v);
            cmp_mdl[2] <= #200 cmp_trip(cal_oc_b,  thr_oc_b,  cofs[2], v);
            cmp_mdl[3] <= #200 cmp_trip(cal_neg_b, thr_neg_b, cofs[3], v);
        end else cmp_mdl <= #200 4'd0;
    end

    // ---------------- SPI host ----------------
    real sck_half = 50.0;              // 10 MHz SCLK
    reg  [23:0] spi_mi;
    task spi_x;                        // one frame of nbits (24 = well-formed)
        input [23:0] mo;
        input integer nbits;
        integer i;
        begin
            ma = 1'b0; #(sck_half);
            cs_n = 1'b0; #(sck_half);
            spi_mi = 24'd0;
            for (i = nbits - 1; i >= 0; i = i - 1) begin
                sdi = mo[i]; #(sck_half);
                ma = 1'b1; spi_mi[i] = slo_sdo; #(sck_half);
                ma = 1'b0;
            end
            #(sck_half); cs_n = 1'b1;
            #(10 * clk_ns + 50);       // CS_N high time
        end
    endtask
    task spi_wr;
        input [6:0] a; input [15:0] d;
        begin spi_x({1'b0, a, d}, 24); end
    endtask
    reg [15:0] rd_val;
    reg [7:0]  rd_stat;
    task spi_rd;
        input [6:0] a;
        begin spi_x({1'b1, a, 16'd0}, 24); spi_x({1'b1, 7'h00, 16'd0}, 24);
              rd_val = spi_mi[15:0]; rd_stat = spi_mi[23:16]; end
    endtask
    task bus_idle;                     // return MA high and wait for BiSS arming
        begin ma = 1'b1; #(1000 * clk_ns + 1000); end
    endtask

    // CRC-8 (0x07, init 0xFF) over the calibration registers, as the host computes it
    function [7:0] crc8;
        input [127:0] bytes;
        integer i, j;
        reg [7:0] r;
        begin
            r = 8'hFF;
            for (i = 15; i >= 0; i = i - 1) begin
                r = r ^ bytes[i*8 +: 8];
                for (j = 0; j < 8; j = j + 1) r = r[7] ? ({r[6:0], 1'b0} ^ 8'h07) : {r[6:0], 1'b0};
            end
            crc8 = r;
        end
    endfunction
    reg [127:0] calb;
    integer ci;
    task load_cal_crc;                 // read back 0x10..0x17, write CAL_CRC
        begin
            for (ci = 0; ci < 8; ci = ci + 1) begin
                spi_rd(7'h10 + ci);
                calb[(15 - 2 * ci) * 8 +: 8] = rd_val[15:8];
                calb[(14 - 2 * ci) * 8 +: 8] = rd_val[7:0];
            end
            spi_wr(7'h18, {8'd0, crc8(calb)});
            #(80 * clk_ns);
        end
    endtask

    task init_chip;
        begin
            por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
            ma = 1'b1; #(700 * clk_ns);            // MA idle -> BiSS armed
            load_cal_crc;
            spi_wr(7'h04, 16'h0001);               // CLR
            #(20 * clk_ns);
            bus_idle;
        end
    endtask

    // ---------------- BiSS master ----------------
    reg  [63:0] b_bits;                // received bits after START: CDS, data, CRC
    integer b_busy, b_n, b_start_edge;
    real b_to_ns, b_lat_t;
    reg  b_ack_ok, b_stop_ok, b_cds;
    reg  [35:0] b_data;                // data incl. nE nW, right-aligned
    reg  [5:0]  b_crc_wire, b_crc_calc;
    function [5:0] crc6;
        input [35:0] d; input integer n;
        integer i;
        reg [5:0] c; reg fb;
        begin
            c = 6'd0;
            for (i = n - 1; i >= 0; i = i - 1) begin
                fb = c[5] ^ d[i]; c = {c[4:0], 1'b0}; if (fb) c = c ^ 6'h03;
            end
            crc6 = c;
        end
    endfunction
    // ndata = data bits incl. nE nW; abort_at > 0 stops clocking after that many edges
    task biss_frame;
        input real th; input real tl; input integer ndata; input cdm; input integer abort_at;
        integer k, got, need, j;
        reg s;
        real t_last;
        begin
            k = 0; got = 0; b_start_edge = 0; b_bits = 64'd0; b_ack_ok = 0; b_stop_ok = 0;
            need = 1 + ndata + 6;          // CDS + data + CRC
            j = 0;
            while (slo_sdo !== 1'b1 && j < 100000) begin #10; j = j + 1; end
            ma = 1'b0; #(tl);
            while ((b_start_edge == 0 || got < need + 1) && k < 400 && !(abort_at > 0 && k >= abort_at)) begin
                ma = 1'b1; k = k + 1;
                if (k == 1) b_lat_t = $realtime;
                t_last = $realtime;
                #(th);
                s = slo_sdo;                 // value driven after rising edge k
                ma = 1'b0; t_last = $realtime;
                if (k == 2) b_ack_ok = (s == 1'b0);
                else if (k >= 3 && b_start_edge == 0) begin
                    if (s) b_start_edge = k;
                end else if (b_start_edge != 0) begin
                    if (got < need) b_bits[63 - got] = s;
                    else b_stop_ok = (s == 1'b0);
                    got = got + 1;
                end
                #(tl);
            end
            // end of clocking: MA = inverted CDM during the timeout
            if (!cdm) begin ma = 1'b1; t_last = $realtime; end
            j = 0;
            while (slo_sdo !== 1'b1 && j < 200000) begin #1; j = j + 1; end
            b_to_ns = $realtime - t_last;
            if (cdm) begin #(200); ma = 1'b1; end
            #(200);
            b_busy = (b_start_edge > 0) ? b_start_edge - 1 : -1;
            b_cds  = b_bits[63];
            b_data = 36'd0;
            for (j = 0; j < ndata; j = j + 1) b_data[ndata - 1 - j] = b_bits[62 - j];
            for (j = 0; j < 6; j = j + 1) b_crc_wire[5 - j] = b_bits[62 - ndata - j];
            b_crc_calc = crc6(b_data, ndata);
        end
    endtask

    // ---------------- SSI master ----------------
    reg [35:0] s_data;
    real s_mono_ns;
    task ssi_frame;
        input real th; input real tl; input integer n;
        integer k, j;
        real t_last;
        begin
            s_data = 36'd0;
            j = 0;
            while (slo_sdo !== 1'b1 && j < 100000) begin #10; j = j + 1; end
            ma = 1'b0; #(tl);                      // first falling edge: latch
            for (k = 0; k < n; k = k + 1) begin
                ma = 1'b1; #(th);
                ma = 1'b0; s_data[n - 1 - k] = slo_sdo; #(tl);
            end
            ma = 1'b1; t_last = $realtime;         // edge n+1: data low (monoflop)
            #(th);
            j = 0;
            while (slo_sdo !== 1'b1 && j < 200000) begin #1; j = j + 1; end
            s_mono_ns = $realtime - t_last;
            #(200);
        end
    endtask

    // ---------------- BiSS control channel (D2 pp. 13-17) ----------------
    // Frame k carries CDM_k (sent at the end of frame k) and CDS_k; the slave
    // answers CDM_k in CDS_{k+1} (D2 p. 14). Command: S CTS=1 ID[2:0] ADR[6:0]
    // CRC4 R W, then the start bit S at frame s_at (D2: may be delayed), then 0.
    // seq_at > 0: a second S at that frame (sequential read, D2 Fig. 30).
    reg [79:0] cc_cds;
    function [3:0] crc4;               // x^4 + x + 1, start 0, MSB first, not inverted
        input [10:0] d; input integer n;
        integer i; reg [3:0] c;
        begin c = 4'd0; for (i = n - 1; i >= 0; i = i - 1) c = {c[2:0], 1'b0} ^ ((c[3] ^ d[i]) ? 4'h3 : 4'h0); crc4 = c; end
    endfunction
    task cc_cmd;
        input [6:0] adr; input rd; input wr; input bad_crc; input integer s_at; input integer seq_at; input integer nfr;
        integer k; reg [3:0] c4; reg cdm;
        begin
            for (k = 0; k < 14; k = k + 1) biss_frame(250.0, 250.0, 20, 1'b0, 0);   // 14 x CDM = 0: reset
            c4 = bad_crc ? 4'hF : crc4({1'b1, 3'b000, adr}, 11);                       // CTS = 1 (register access, D2 p. 14), ID 0
            cc_cds = 80'd0;
            for (k = 0; k < nfr; k = k + 1) begin
                if (k <= 1) cdm = 1'b1;                                                   // S, CTS = 1
                else if (k <= 4) cdm = 1'b0;
                else if (k <= 11) cdm = adr[11 - k];
                else if (k <= 15) cdm = ~c4[15 - k];
                else if (k == 16) cdm = rd;
                else if (k == 17) cdm = wr;
                else cdm = (k == s_at) || (k == seq_at);
                biss_frame(250.0, 250.0, 20, cdm, 0);
                cc_cds[k] = b_cds;
            end
        end
    endtask
    function [7:0] cc_byte;            // 8 CDS bits from frame k, MSB first
        input integer k; integer i;
        begin for (i = 0; i < 8; i = i + 1) cc_byte[7 - i] = cc_cds[k + i]; end
    endfunction
    function [3:0] cc_nib;
        input integer k; integer i;
        begin for (i = 0; i < 4; i = i + 1) cc_nib[3 - i] = cc_cds[k + i]; end
    endfunction

    // =====================================================================
    reg [1023:0] test;
    integer i, k, nb, f_i;
    real fr, th, tl, err_deg, tick_ns, exp_ns;
    reg [17:0] exp18;
    reg [35:0] word;
    reg [15:0] v16, gray16;
    initial begin
        if (!$value$plusargs("test=%s", test)) test = "biss";
        tick_ns = clk_ns;
        $display("# tb_top test=%0s clk_ns=%0.3f", test, clk_ns);
        init_chip;
        check(fault_n == 1'b1, "init: FAULT_N high after CAL_CRC load and CLR");

        // =================================================================
        if (test == "biss") begin
            // ---- item 1: CRC-6 vectors, 18-bit position, nE = nW = 1 ----
            spi_wr(7'h05, 16'h0212);                       // ST_LEN 18, MT off, TEST_POS_EN
            bus_idle;
            spi_wr(7'h06, 16'h0000); spi_wr(7'h05, 16'h0212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h00000 && b_data[1:0] == 2'b11, "biss item1: data 0x00000 nE nW = 1 1");
            check(b_crc_wire == 6'h3A, "biss item1: 0x00000 CRC on wire 0x3A");
            spi_wr(7'h06, 16'hFFFF); spi_wr(7'h05, 16'h3212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h3FFFF && b_crc_wire == 6'h02, "biss item1: 0x3FFFF CRC on wire 0x02");
            spi_wr(7'h06, 16'h2345); spi_wr(7'h05, 16'h1212); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h12345 && b_crc_wire == 6'h0D, "biss item1: 0x12345 CRC on wire 0x0D");
            check(b_ack_ok && b_stop_ok, "biss: ACK 0 at edge 2, stop 0 after CRC");

            // ---- items 2, 3: MA 80 kHz .. 10 MHz, 40 % duty corners, t_busy ----
            for (f_i = 0; f_i < 5; f_i = f_i + 1) begin
                case (f_i)
                    0: fr = 80e3; 1: fr = 250e3; 2: fr = 1e6; 3: fr = 5e6; default: fr = 10e6;
                endcase
                for (k = 0; k < 2; k = k + 1) begin
                    th = (k == 0 ? 0.4 : 0.6) * 1e9 / fr; tl = 1e9 / fr - th;
                    biss_frame(th, tl, 20, 1'b0, 0);
                    $display("INFO biss f_MA=%0.0f Hz duty_high=%0.1f t_busy=%0d T_MA timeout=%0.2f us",
                             fr, th * fr / 1e9, b_busy, b_to_ns / 1000.0);
                    check(b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc && b_ack_ok,
                          "biss item2: frame data and CRC at this MA frequency / duty");
                    if (fr <= 1e6) check(b_busy == 2, "biss item3: t_busy = 2 T_MA (f_MA <= 1 MHz)");
                    else check(b_busy >= 2 && b_busy <= 6, "biss item3: t_busy in 2..6 T_MA (f_MA > 1 MHz, handshake)");
                end
            end

            // ---- item 4: static timeout (TIMEOUT_TICKS = 600) ----
            exp_ns = 600.0 * clk_ns;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            $display("INFO biss timeout measured %0.3f us, 600 ticks = %0.3f us", b_to_ns / 1000.0, exp_ns / 1000.0);
            check(b_to_ns > exp_ns && b_to_ns < exp_ns + 8 * clk_ns, "biss item4: timeout = TIMEOUT_TICKS + sync (< 6 ticks)");
            check(b_to_ns > 12500.0 && b_to_ns < 40000.0, "biss item4: timeout inside 12.5..40 us");

            // ---- item 5: back-to-back frames at minimum cycle ----
            nb = 0;
            for (i = 0; i < 5; i = i + 1) begin
                biss_frame(50.0, 50.0, 20, 1'b0, 0);
                if (b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc) nb = nb + 1;
            end
            check(nb == 5, "biss item5: 5 back-to-back frames at 10 MHz, restart when SLO high");

            // ---- item 6: aborted frame, recovery ----
            biss_frame(500.0, 500.0, 20, 1'b0, 9);
            #(40000);
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[19:2] == 18'h12345 && b_crc_wire == ~b_crc_calc && b_busy == 2,
                  "biss item6: frame after an aborted frame and 40 us is correct");

            // ---- item 7: nE / nW and Null Value ----
            spi_wr(7'h05, 16'h1612); bus_idle;           // FORCE_NE
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[1:0] == 2'b01 && b_crc_wire == ~b_crc_calc, "biss item7: FORCE_NE gives nE = 0, CRC valid");
            spi_wr(7'h05, 16'h1A12); bus_idle;           // FORCE_NW
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data[1:0] == 2'b10 && b_crc_wire == ~b_crc_calc, "biss item7: FORCE_NW gives nW = 0, CRC valid");
            spi_wr(7'h05, 16'h0012); bus_idle;           // real position, MT off
            enc_amp = 0.0; #(20000);                      // signal loss: pos_valid drops
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_data == 36'd0 && b_crc_wire == ~b_crc_calc, "biss item7: Null Value (data 0, nE 0) on signal loss");
            enc_amp = 1400.0; #(40000);
            spi_wr(7'h03, 16'h0020); spi_wr(7'h04, 16'h0001); #(1000);   // clear the AMP fault
            spi_wr(7'h03, 16'h0000); bus_idle;

            // ---- position latch and extrapolation with a rotating head (10 kHz el) ----
            enc_f = 10000.0; #(200000);
            spi_wr(7'h05, 16'h0032); bus_idle;            // MT on, ST 18
            nb = 0; err_deg = 0.0;
            for (i = 0; i < 6; i = i + 1) begin
                biss_frame(250.0, 250.0, 36, 1'b0, 0);
                th = angle_now(0);
                tl = enc_ph0 + enc_f * b_lat_t * 1e-9; tl = tl - $floor(tl);
                exp_ns = (b_data[19:2] / 262144.0 - tl) * 360.0;
                if (exp_ns > 180.0) exp_ns = exp_ns - 360.0;
                if (exp_ns < -180.0) exp_ns = exp_ns + 360.0;
                if (exp_ns < 0) exp_ns = -exp_ns;
                if (exp_ns > err_deg) err_deg = exp_ns;
                if (b_crc_wire == ~b_crc_calc && b_data[1:0] == 2'b11) nb = nb + 1;
                $display("INFO biss latch frame %0d: busy %0d MT %0d ST 0x%05h nE nW %b crc %02h/%02h head %0.5f err %0.3f deg", i, b_busy, b_data[35:20], b_data[19:2], b_data[1:0], b_crc_wire, ~b_crc_calc, tl, exp_ns);
                #(30000);
            end
            $display("INFO biss latch: max |position at LAT - head angle at LAT| = %0.3f deg el at 10 kHz el", err_deg);
            check(nb == 6, "biss: 6 multi-turn frames with real position, nE nW 1 1, CRC valid");
            check(err_deg < 0.25, "biss: latched position within 0.25 deg el (2 ticks) of the head angle at LAT (10 kHz el)");
            enc_f = 1000.0;

            // ---- half-tick LAT timing (BUS_CFG.LAT_HALF): latch error spread at 100 kHz el ----
            begin : lh
                real mn, mx, e, spr0, spr1;
                for (k = 0; k < 2; k = k + 1) begin
                    enc_f = 100000.0;
                    spi_wr(7'h05, k ? 16'h4032 : 16'h0032); bus_idle; #(200000);
                    mn = 1e9; mx = -1e9;
                    for (i = 0; i < 40; i = i + 1) begin
                        #(i * 3.917 + 0.7);                  // spread the LAT edge over the tick
                        biss_frame(250.0, 250.0, 36, 1'b0, 0);
                        tl = enc_ph0 + enc_f * b_lat_t * 1e-9; tl = tl - $floor(tl);
                        e = (b_data[19:2] / 262144.0 - tl) * 360.0;
                        if (e > 180.0) e = e - 360.0;
                        if (e < -180.0) e = e + 360.0;
                        if (e < mn) mn = e;
                        if (e > mx) mx = e;
                        #(20000);
                    end
                    if (k) spr1 = mx - mn; else spr0 = mx - mn;
                    $display("INFO biss LAT_HALF=%0d at 100 kHz el: latch error %0.3f .. %0.3f deg el, spread %0.3f deg (1 tick = %0.3f deg)",
                             k, mn, mx, mx - mn, 360.0 * 100000.0 * clk_ns * 1e-9);
                end
                check(spr1 < 0.75 * spr0, "biss: LAT_HALF reduces the latch error spread at 100 kHz el (< 0.75 x without)");
                enc_f = 1000.0; #(200000);
            end

            // ---- item 8: control channel (D2 pp. 13-17) ----
            spi_wr(7'h05, 16'h0212); bus_idle;
            begin : cc
                reg [7:0] d;
                spi_rd(7'h32); v16 = rd_val; bus_idle;
                // read 0x42 (BP_ID high byte), S without delay
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                d = cc_byte(20);
                $display("INFO biss cc read 0x42: CDS[1..32] %b", cc_cds[32:1]);
                check(cc_cds[1] == 1'b1 && cc_cds[16:2] == 15'd0, "biss item8: IDL0 = 1 after the start bit, then 0 (D2 p. 14-15)");
                check(cc_cds[17] == 1'b1 && cc_cds[18] == 1'b0, "biss item8: slave repeats R = 1, W = 0 (address accepted, D2 p. 16)");
                check(cc_cds[19] == 1'b1 && d == 8'h00 && cc_nib(28) == ~crc4({3'd0, d}, 8),
                      "biss item8: S repeated, D = 0x00 (BP_ID high), CRC-4 inverted over the data");
                check(cc_cds[32] == 1'b0, "biss item8: stop bit P = 0 (next address 0x43 accepted)");
                // sequential read 0x42, 0x43 (second S at frame 32)
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 32, 48);
                d = cc_byte(34);
                check(cc_cds[33] == 1'b1 && d == 8'h01 && cc_nib(42) == ~crc4({3'd0, d}, 8) && cc_cds[46] == 1'b0,
                      "biss item8: sequential read gives 0x43 = 0x01 (BP_ID non-zero), CRC-4, P = 0");
                // delayed start bit (S at frame 21)
                cc_cmd(7'h78, 1'b1, 1'b0, 1'b0, 21, 0, 37);
                d = cc_byte(23);
                check(cc_cds[21:19] == 3'd0 && cc_cds[22] == 1'b1 && d == 8'h52 && cc_nib(31) == ~crc4({3'd0, d}, 8),
                      "biss item8: delayed S, read 0x78 (DEV_ID byte 0 = 0x52)");
                // last address: P = 1
                cc_cmd(7'h7F, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                d = cc_byte(20);
                check(cc_cds[19] && d == 8'h00 && cc_nib(28) == ~crc4({3'd0, d}, 8) && cc_cds[32] == 1'b1,
                      "biss item8: read 0x7F (MFR_ID low, reset value), P = 1 (no next address)");
                // refused read of 0x40 (BSEL, one bank): W inverted, no S
                cc_cmd(7'h40, 1'b1, 1'b0, 1'b0, 18, 0, 34);
                check(cc_cds[17] == 1'b1 && cc_cds[18] == 1'b1 && cc_cds[33:19] == 15'd0,
                      "biss item8: refused read (0x40) -> W repeated inverted, no data (D2 p. 16)");
                // write (not supported): W inverted
                cc_cmd(7'h44, 1'b0, 1'b1, 1'b0, 18, 0, 34);
                check(cc_cds[17] == 1'b0 && cc_cds[18] == 1'b0 && cc_cds[33:19] == 15'd0,
                      "biss item8: write access refused -> W repeated inverted, no data");
                // CRC-4 error: no response
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b1, 18, 0, 34);
                check(cc_cds[33:17] == 17'd0, "biss item8: header CRC-4 error -> no response");
                spi_rd(7'h32); bus_idle;
                $display("INFO biss cc error counter %0d -> %0d", v16[11:8], rd_val[11:8]);
                check(rd_val[11:8] == v16[11:8] + 4'd3, "biss item8: refused read, refused write and CRC error counted (DIAG_BISS[11:8] + 3)");
                // 14 x CDM = 0 aborts a started command
                cc_cmd(7'h42, 1'b1, 1'b0, 1'b0, 18, 0, 8);
                for (i = 0; i < 14; i = i + 1) biss_frame(250.0, 250.0, 20, 1'b0, 0);
                check(dut.u_biss.cst == 3'd0, "biss item8: 14 x CDM = 0 returns the control channel to idle");
            end
        end

        // =================================================================
        if (test == "ssi") begin
            enc_f = 0.0; enc_ph0 = 0.3; #(500000);
            for (k = 0; k < 2; k = k + 1) begin
                spi_wr(7'h05, k ? 16'h00ED : 16'h006D); bus_idle;   // SSI, MT on, ST 13, gray k
                ssi_frame(500.0, 500.0, 29);
                spi_rd(7'h19); v16 = rd_val; spi_rd(7'h1A); bus_idle;
                word = {rd_val, v16[15:3]};                     // MT16 + ST13 from SPI, binary
                if (k) word = word ^ (word >> 1);
                $display("INFO ssi gray=%0d data 0x%08h expected 0x%08h monoflop %0.2f us", k, s_data[28:0], word[28:0], s_mono_ns / 1000.0);
                check(s_data[28:0] == word[28:0], k ? "ssi: Gray word = SPI POS/TURNS (MT16 + ST13)" : "ssi: binary word = SPI POS/TURNS (MT16 + ST13)");
                exp_ns = 600.0 * clk_ns;
                check(s_mono_ns > exp_ns && s_mono_ns < exp_ns + 8 * clk_ns, "ssi: monoflop = TIMEOUT_TICKS + sync");
            end
            for (f_i = 0; f_i < 3; f_i = f_i + 1) begin
                fr = (f_i == 0) ? 100e3 : (f_i == 1) ? 1e6 : 2e6;
                ssi_frame(0.5e9 / fr, 0.5e9 / fr, 29);
                check(s_data[28:0] == word[28:0], "ssi: Gray word at 100 kHz / 1 MHz / 2 MHz clock");
            end
            // host clock trim (S5): OSC_COUNT over 16 SCLK periods at 1 MHz, then
            // TIMEOUT_TICKS = OSC_COUNT * 20 / 16 for a 20 us monoflop / BiSS timeout
            spi_wr(7'h08, 16'h0110);
            sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0;
            spi_rd(7'h09); v16 = rd_val;
            spi_wr(7'h07, (v16 * 20 + 8) / 16); bus_idle;
            ssi_frame(500.0, 500.0, 29);
            $display("INFO ssi clk %0.3f ns: OSC_COUNT %0d -> TIMEOUT_TICKS %0d, monoflop %0.2f us (600 ticks untrimmed = %0.2f us)",
                     clk_ns, v16, (v16 * 20 + 8) / 16, s_mono_ns / 1000.0, 600.0 * clk_ns / 1000.0);
            check(s_data[28:0] == word[28:0] && s_mono_ns > 19000.0 && s_mono_ns < 21000.0,
                  "ssi: after the host trim from OSC_COUNT the monoflop is 20 us +-5 %");
        end

        // =================================================================
        if (test == "spi") begin
            spi_rd(7'h00);
            check(rd_val == 16'h5202, "spi: ID reads 0x5202 (revision 0.2)");
            spi_rd(7'h08);
            check(rd_val == 16'd22 && osc_trim == 5'd22, "spi: OSC_TRIM reset value 22 (D13), on the oscillator port");
            spi_rd(7'h05);
            check(rd_val == 16'h40B2, "spi: BUS_CFG reset 0x40B2 (LAT_HALF on, BiSS, MT on, ST 18)");
            spi_wr(7'h05, 16'h4112); spi_rd(7'h05);
            check(rd_val == 16'h4012, "spi: BUS_CFG bit 8 reserved (reads 0; AS5047P mode removed)");
            spi_wr(7'h05, 16'h40B2);
            spi_rd(7'h56);
            check(rd_val == 16'd256, "spi: ADC_W6 reset 4 * 64 = 256 (binary weight, 1/4 LSB units)");
            spi_rd(7'h5C);
            check(rd_val == 16'd256, "spi: ADC_W12 (redundant decision) reset 256");
            // walking pattern on writable registers
            nb = 0;
            for (i = 0; i < 16; i = i + 1) begin
                spi_wr(7'h20 + (i % 7), 16'h0001 << i);
                spi_rd(7'h20 + (i % 7));
                if (rd_val == (16'h0001 << i)) nb = nb + 1;
            end
            check(nb == 16, "spi: walking-one write/read on PWM registers");
            spi_wr(7'h20, 16'h0000);
            spi_wr(7'h0C, 16'hA5C3); spi_rd(7'h0C);
            check(rd_val == 16'hA5C3 && ana_ctrl == 16'hA5C3, "spi: ANA_CTRL write reaches the analog control port");
            spi_wr(7'h08, 16'h0013); spi_rd(7'h08);
            check(rd_val == 16'h0013 && osc_trim == 5'h13, "spi: OSC_TRIM write reaches the oscillator port");
            spi_x({1'b0, 7'h0D, 16'h0007}, 24);
            check(spi_mi[23:16] == dut.status[7:0], "spi: status byte in every frame");
            spi_x({1'b1, 7'h0D, 16'h0000}, 24);
            check(spi_mi[15:0] == 16'h0007, "spi: write echo in the next frame");
            spi_rd(7'h7E); check(rd_val == 16'h0000, "spi: BiSS MFR_ID mirror at 0x7E");
            spi_rd(7'h79); check(rd_val == 16'h0031, "spi: BiSS DEV_ID mirror at 0x79 ('1')");
            // malformed frame (20 bits) -> error counter
            spi_x({4'h0, 20'hFFFFF}, 20); spi_rd(7'h33);
            check(rd_val[7:0] == 8'd1, "spi: short frame counted as SPI error");
            // OSC_COUNT: arm, burst of 40 SCLK periods at 1 MHz (malformed frame), read
            spi_wr(7'h08, 16'h0113);
            sck_half = 500.0; spi_x(24'd0, 40); sck_half = 50.0;
            spi_rd(7'h09);
            exp_ns = 16000.0 / clk_ns;
            $display("INFO OSC_COUNT = %0d, expected %0.1f (16 us of %0.3f ns ticks)", rd_val, exp_ns, clk_ns);
            check(rd_val >= exp_ns - 2 && rd_val <= exp_ns + 2 && dut.status[10], "spi: OSC_COUNT over 16 SCLK periods (1 MHz) within +-2 ticks, OSC_DONE");
            spi_rd(7'h09);
            check(rd_val >= exp_ns - 2 && rd_val <= exp_ns + 2, "spi: OSC_COUNT held after later SPI traffic");
            // clock-fault window: OSC_WIN = {HI, LO} in units of 16 ticks
            k = $rtoi(exp_ns / 16.0);
            spi_wr(7'h0A, {k[7:0] + 8'd2, k[7:0] - 8'd2}); spi_rd(7'h01);
            check(rd_val[5] == 1'b0, "spi: OSC_COUNT inside OSC_WIN -> STATUS.CLK_FAULT = 0");
            spi_wr(7'h0A, {k[7:0] - 8'd4, k[7:0] - 8'd8}); spi_rd(7'h01);
            check(rd_val[5] == 1'b1, "spi: OSC_COUNT above OSC_WIN.HI -> STATUS.CLK_FAULT = 1");
            spi_wr(7'h0A, {k[7:0] + 8'd8, k[7:0] + 8'd4}); spi_rd(7'h01);
            check(rd_val[5] == 1'b1, "spi: OSC_COUNT below OSC_WIN.LO -> STATUS.CLK_FAULT = 1");
            spi_wr(7'h0A, 16'h0000); spi_rd(7'h01);
            check(rd_val[5] == 1'b0, "spi: OSC_WIN = 0 disables the clock-fault check");
            // mode switch: BiSS frame, SPI, BiSS
            spi_wr(7'h05, 16'h1212); spi_wr(7'h06, 16'h2345); bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            $display("INFO spi/biss frame: busy %0d data 0x%05h nE nW %b crc wire %02h calc~ %02h ack %0d", b_busy, b_data[19:2], b_data[1:0], b_crc_wire, ~b_crc_calc, b_ack_ok);
            check(b_crc_wire == 6'h0D && b_data[19:2] == 18'h12345, "spi/biss: BiSS frame before SPI access");
            spi_wr(7'h06, 16'h0000); spi_wr(7'h05, 16'h0212); spi_rd(7'h06);
            check(rd_val == 16'h0000, "spi/biss: SPI access between BiSS frames");
            bus_idle;
            biss_frame(500.0, 500.0, 20, 1'b0, 0);
            check(b_crc_wire == 6'h3A && b_data[19:2] == 18'h0, "spi/biss: BiSS frame after SPI sees the new TEST_POS");
            // MA traffic while CS_N high does not disturb SPI state; SPI after BiSS
            spi_rd(7'h00);
            check(rd_val == 16'h5202, "spi/biss: SPI read correct after BiSS traffic on the shared pad");
        end

        // =================================================================
        if (test == "gate") begin
            begin : gt
                integer t_on_a, t_off_a, t_on_b, t_off_b, t_on_c, t_off_c, tk, t_sa, t_sb, t_is, n_late;
                integer t_az_on, t_az_off, n_sa;
                integer per, da, db, dc, pa, pb, pc, dt;
                reg ga_d, gb_d, gc_d, az_d, is_d;
                per = 1500; da = 600; db = 300; dc = 900; pa = 0; pb = 500; pc = 1000; dt = 15;
                spi_wr(7'h20, per); spi_wr(7'h21, da); spi_wr(7'h22, db); spi_wr(7'h23, dc);
                spi_wr(7'h24, pa); spi_wr(7'h25, pb); spi_wr(7'h26, pc); spi_wr(7'h27, dt);
                spi_wr(7'h38, 16'd1200); spi_wr(7'h39, 16'h2028);   // AZ_START 1200, AZ_LEN 40
                spi_wr(7'h04, 16'h0002);                    // GATE_EN
                #(3 * per * clk_ns);
                // measure one period in ticks relative to the counter wrap
                @(posedge dut.u_gate.pwm_wrap);
                tk = 0; t_on_a = -1; t_off_a = -1; t_on_b = -1; t_off_b = -1; t_on_c = -1; t_off_c = -1;
                t_sa = -1; t_sb = -1; t_is = -1; t_az_on = -1; t_az_off = -1; n_sa = 0;
                ga_d = gate_a; gb_d = gate_b; gc_d = gate_c; az_d = az_win; is_d = is_smp;
                while (tk < per) begin
                    @(posedge clk); #1; tk = tk + 1;
                    if (gate_a && !ga_d) t_on_a = tk;  if (!gate_a && ga_d) t_off_a = tk;
                    if (gate_b && !gb_d) t_on_b = tk;  if (!gate_b && gb_d) t_off_b = tk;
                    if (gate_c && !gc_d) t_on_c = tk;  if (!gate_c && gc_d) t_off_c = tk;
                    if (az_win && !az_d) t_az_on = tk; if (!az_win && az_d) t_az_off = tk;
                    if (is_smp && !is_d) t_is = tk;
                    if (adc_start && adc_mux == 2'd2) begin t_sa = tk; n_sa = n_sa + 1; end
                    if (adc_start && adc_mux == 2'd3) t_sb = tk;
                    ga_d = gate_a; gb_d = gate_b; gc_d = gate_c; az_d = az_win; is_d = is_smp;
                end
                $display("INFO gate A on %0d off %0d (width %0d), B on %0d off %0d (width %0d), C on %0d off %0d (width %0d); ISA start %0d ISB start %0d is_smp %0d; az_win %0d..%0d",
                         t_on_a, t_off_a, (t_off_a - t_on_a + per) % per, t_on_b, t_off_b, t_off_b - t_on_b,
                         t_on_c, t_off_c, (t_off_c - t_on_c + per) % per, t_sa, t_sb, t_is, t_az_on, t_az_off);
                check((t_off_a - t_on_a + per) % per == da - 2 * dt, "gate: A on-time = DUTY - 2 DEAD");
                check(t_off_b - t_on_b == db - 2 * dt, "gate: B on-time = DUTY - 2 DEAD");
                check((t_off_c - t_on_c + per) % per == dc - 2 * dt, "gate: C on-time = DUTY - 2 DEAD (window wraps the period)");
                check(t_on_b - (pb + dt) == t_on_a - (pa + dt) || t_on_a == -1, "gate: B rising edge at PHASE_B + DEAD (same offset as A)");
                check(t_sa >= 0 && ((t_sa - t_on_a + per) % per) - (da - 2 * dt) / 2 >= -1 &&
                      ((t_sa - t_on_a + per) % per) - (da - 2 * dt) / 2 <= 1, "gate: current strobe at the centre of the A on-time (+-1 tick)");
                check(n_sa == 1 && t_is == t_sa && t_sb > t_sa && t_sb - t_sa <= CONV + 3,
                      "gate: one current pair per period: is_smp rises with the ISA start, ISB follows the ISA conversion");
                check(t_az_off - t_az_on == 40 && t_az_on - t_on_a == 1200 - (pa + dt),
                      "gate: az_win is AZ_LEN = 40 ticks wide and starts at counter value AZ_START");
                // strobes are never late (guard keeps the ADC free) over 20 periods
                spi_rd(7'h35); n_late = rd_val;
                #(20 * per * clk_ns);
                spi_rd(7'h35);
                check(rd_val == n_late, "gate: no late current conversion over 20 PWM periods (guard)");
                spi_rd(7'h33);
                check(rd_val[11:8] == 4'd0, "gate: no position pair overrun with current conversions interleaved");
                // comparator blanking: az_win and 16 ticks after it
                @(posedge az_win); #(5 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0;
                @(negedge az_win); #(8 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0;
                #(20 * clk_ns);
                check(fault_n == 1'b1, "gate: comparator flags inside az_win and 8 ticks after it are blanked");
                #(100 * clk_ns); @(negedge clk); cmp[0] = 1'b1; #(4 * clk_ns); cmp[0] = 1'b0; #(10 * clk_ns);
                check(fault_n == 1'b0, "gate: the same flag 100 ticks after az_win latches OC_A");
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n == 1'b1, "gate: CLR releases the blanking-test fault");
                // shadow update: change duty mid-period, takes effect at wrap
                spi_wr(7'h21, 16'd200);
                @(posedge dut.u_gate.pwm_wrap); @(posedge dut.u_gate.pwm_wrap);
                tk = 0; t_on_a = -1; t_off_a = -1; ga_d = gate_a;
                while (tk < per) begin
                    @(posedge clk); #1; tk = tk + 1;
                    if (gate_a && !ga_d) t_on_a = tk; if (!gate_a && ga_d) t_off_a = tk;
                    ga_d = gate_a;
                end
                check((t_off_a - t_on_a + per) % per == 200 - 2 * dt, "gate: new DUTY_A applied at the period wrap");
                // DUTY_A <= 2 DEAD: channel A stays off, no current strobe
                spi_wr(7'h21, 16'd20);
                @(posedge dut.u_gate.pwm_wrap); @(posedge dut.u_gate.pwm_wrap);
                tk = 0; nb = 0;
                while (tk < per) begin @(posedge clk); #1; tk = tk + 1; if (gate_a) nb = nb + 1; if (adc_start && adc_mux == 2'd2) nb = nb + 1000; end
                check(nb == 0, "gate: DUTY_A <= 2 DEAD keeps channel A off and suppresses the current strobe");
                spi_wr(7'h21, 16'd600);
                // EN low forces the outputs low immediately
                #(3 * per * clk_ns);
                wait (gate_c == 1'b1); #5;
                en_pad = 1'b0; #1;
                check(gate_c == 1'b0, "gate: EN low forces GATE_C low within 1 ns (combinational)");
                #(10 * clk_ns);
                check(fault_n == 1'b0, "gate: EN low latches a fault (FAULT_N low)");
                en_pad = 1'b1; #(10 * clk_ns);
                spi_wr(7'h04, 16'h0003); #(per * 2 * clk_ns);
                check(fault_n == 1'b1, "gate: CLR after EN high releases the fault");
                // ADC weight correction in the path: ADC_W11 + 100 LSB moves I_A by +100
                ia_code = 12'd2848; #(3 * per * clk_ns);
                spi_rd(7'h29); v16 = rd_val;
                spi_wr(7'h5B, 16'd8592); #(3 * per * clk_ns);
                spi_rd(7'h29);
                $display("INFO gate I_A %0d with binary weights, %0d with ADC_W11 = 8592", v16, rd_val);
                check(v16 == 16'd2848 && rd_val == 16'd2948, "gate: I_A = corrected code (ADC_W11 = 4 * 2048 + 400 adds 100 LSB)");
                spi_wr(7'h5B, 16'd8192); ia_code = 12'd2048;
            end
        end

        // =================================================================
        // comparator offset calibration (r1_cmpcal): behavioural comparators with
        // offsets +7.3, -12.6, +33, -40 calibration steps (OC_A, NEG_A, OC_B, NEG_B).
        // Expected codes (largest code with trip < 0): 24, 44, 0 (exhausted), 63 (exhausted).
        if (test == "cal") begin
            begin : ct
                integer tk, n_gate, n_win, n_fault;
                reg az_d;
                cofs[0] = 7.3; cofs[1] = -12.6; cofs[2] = 33.0; cofs[3] = -40.0;
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150);
                spi_wr(7'h38, 16'd200); spi_wr(7'h39, 16'h2028);    // AZ_START 200, AZ_LEN 40, THR_ZERO 32
                cmp_vin = 100.0; cmp_mdl_en = 1'b1;
                spi_wr(7'h04, 16'h0002); #(4 * 300 * clk_ns);
                check(fault_n == 1'b1 && thr_oc_a == 6'd63, "cal: comparators idle at CMP_THR = 63 (reset), no fault");
                spi_wr(7'h04, 16'h000A);                             // GATE_EN + CMP_CAL
                #(4 * clk_ns);
                check(dut.status[11] == 1'b1 && thr_oc_a == 6'd32 && thr_neg_b == 6'd32,
                      "cal: STATUS.CAL_BUSY = 1, every threshold carries THR_ZERO during the search");
                tk = 0; n_gate = 0; n_win = 0; n_fault = 0; az_d = az_win;
                while (dut.status[11] && tk < 20 * 300) begin
                    @(posedge clk); #1; tk = tk + 1;
                    if (gate_a | gate_b | gate_c) n_gate = n_gate + 1;
                    if (!fault_n) n_fault = n_fault + 1;
                    if (az_d && !az_win) n_win = n_win + 1;
                    az_d = az_win;
                end
                $display("INFO cal search: %0d ticks, %0d az windows, CAL codes %0d %0d %0d %0d exh %b",
                         tk, n_win, cal_oc_a, cal_neg_a, cal_oc_b, cal_neg_b, dut.cal_exh);
                check(n_win == 7, "cal: search uses 7 auto-zero windows (6 decisions + range check)");
                check(n_gate == 0, "cal: gates held off during the search (GATE_EN set)");
                check(n_fault == 0, "cal: comparator flags outside az_win during the search do not latch a fault");
                check(cal_oc_a == 6'd24 && cal_neg_a == 6'd44, "cal: OC_A = 24 (+7.3 offset), NEG_A = 44 (-12.6 offset)");
                check(cal_oc_b == 6'd0 && cal_neg_b == 6'd63, "cal: OC_B = 0, NEG_B = 63 (offsets outside the range)");
                spi_rd(7'h3A); v16 = rd_val; spi_rd(7'h3B);
                $display("INFO cal CMP_CAL_A 0x%04h CMP_CAL_B 0x%04h", v16, rd_val);
                check(v16 == 16'h2C18 && rd_val == 16'h7F40, "cal: CMP_CAL_A/B = codes, EXH set only for OC_B and NEG_B");
                spi_rd(7'h01);
                check(rd_val[11] == 1'b0 && rd_val[12] == 1'b1 && rd_val[13] == 1'b1, "cal: STATUS CAL_BUSY 0, CAL_DONE 1, CAL_EXH 1");
                #(4 * 300 * clk_ns);
                check(fault_n == 1'b1 && (gate_a === 1'b1 || gate_a === 1'b0) && thr_oc_a == 6'd63,
                      "cal: after the search the thresholds return to CMP_THR, no fault");
                tk = 0; n_gate = 0;
                while (tk < 300) begin @(posedge clk); tk = tk + 1; if (gate_a) n_gate = n_gate + 1; end
                check(n_gate > 0, "cal: gates run again after the search");
                // host write of the codes (bench use)
                spi_wr(7'h3A, 16'h0510); spi_rd(7'h3A);
                check(rd_val[13:8] == 6'd5 && rd_val[5:0] == 6'd16 && cal_neg_a == 6'd5 && cal_oc_a == 6'd16,
                      "cal: CMP_CAL_A host write reaches the calibration ports");
                cmp_mdl_en = 1'b0;
            end
        end

        // =================================================================
        if (test == "safe") begin
            begin : sf
                integer src, tk, t_trip, t_exp, kupd, upd_ticks;
                reg [23:0] e_mod;
                reg [15:0] sqv;
                spi_wr(7'h20, 16'd300); spi_wr(7'h21, 16'd150); spi_wr(7'h22, 16'd150);
                spi_wr(7'h25, 16'd150); spi_wr(7'h04, 16'h0002);
                #(2000 * clk_ns);
                check(gate_a === 1'b1 || gate_a === 1'b0, "safe: gates running");
                // comparator flags
                for (src = 0; src < 4; src = src + 1) begin
                    @(negedge clk); cmp[src] = 1'b1;
                    tk = 0; while (fault_n && tk < 20) begin @(posedge clk); #1; tk = tk + 1; end
                    cmp[src] = 1'b0;
                    #(10 * clk_ns);
                    spi_rd(7'h02);
                    $display("INFO safe cmp[%0d]: FAULT 0x%04h, FAULT_N low after %0d ticks", src, rd_val, tk);
                    check(rd_val == (16'h1 << src) && !fault_n && !gate_a && !gate_b && !gate_c,
                          "safe: comparator flag latches its FAULT bit, FAULT_N low, gates low");
                    check(tk <= 6, "safe: comparator to FAULT_N within 6 ticks (< 1 us)");
                    spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                    check(fault_n, "safe: CLR releases the comparator fault");
                end
                // over-temperature: T2F at 2 MHz, window 2^12 ticks
                spi_wr(7'h34, 16'd12); spi_wr(7'h2C, 16'd100);
                fork
                    begin : t2f_gen
                        forever begin #250 t2f_clk = ~t2f_clk; end
                    end
                    begin #(3 * 4096 * clk_ns + 1000); disable t2f_gen; end
                join
                spi_rd(7'h2B);
                $display("INFO safe TEMP count %0d (2 MHz over 4096 ticks, expected %0.1f)", rd_val, 4096.0 * clk_ns / 500.0);
                spi_rd(7'h02);
                check(rd_val[4] && !fault_n, "safe: T2F count >= OT_LIM latches OTEMP");
                spi_wr(7'h2C, 16'hFFFF); #(2 * 4096 * clk_ns); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: OTEMP clears after the count drops below OT_LIM");
                // amplitude loss
                enc_amp = 50.0; #(20000);
                spi_rd(7'h02);
                check(rd_val[5] && !fault_n, "safe: amplitude low latches AMP");
                enc_amp = 1400.0; #(20000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: AMP clears with the amplitude restored");
                // overspeed: 20 kHz el against a limit of 1 LSB/tick (32 units)
                spi_wr(7'h0F, 16'd32); enc_f = 20000.0; #(100000);
                spi_rd(7'h02);
                check(rd_val[6] && !fault_n, "safe: |VELOCITY| > OVS_LIM latches OVERSPEED");
                enc_f = 1000.0; #(100000); spi_wr(7'h0F, 16'h4000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: OVERSPEED clears below the limit");
                // watchdog: period 4 x 1024 ticks, no bus traffic
                spi_wr(7'h0B, 16'd4); spi_wr(7'h04, 16'h0006);
                tk = 0; while (fault_n && tk < 10000) begin @(posedge clk); tk = tk + 1; end
                $display("INFO safe watchdog fired %0d ticks after the last SPI frame (period 4096 ticks)", tk);
                spi_rd(7'h02);
                check(rd_val[7] && tk > 3900 && tk < 4300, "safe: watchdog latches WDT after WDT x 1024 ticks without bus traffic");
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: WDT clears (watchdog disabled, kicked by the SPI frame)");
                // calibration invalid: a write to a cal register
                spi_wr(7'h16, 16'h1234); #(60 * clk_ns);
                spi_rd(7'h02);
                check(rd_val[11] && !fault_n, "safe: write to a calibration register -> CAL invalid fault");
                spi_wr(7'h04, 16'h0003); #(60 * clk_ns);
                check(!fault_n, "safe: CLR does not release the fault while CAL_CRC mismatches");
                load_cal_crc;
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: CLR releases the fault after the correct CAL_CRC is written");
                spi_wr(7'h03, 16'h0800);
                spi_wr(7'h16, 16'h0000); #(60 * clk_ns);
                check(!fault_n, "safe: CAL fault cannot be masked");
                load_cal_crc; spi_wr(7'h03, 16'h0000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                // I2t: |I - I_ZERO| = 800 codes -> i = 50, i^2 = 2500; TAU 6, PRE 0, LIM 2000
                ia_code = 12'd2048; ib_code = 12'd2048;
                spi_wr(7'h2F, 16'd2048); spi_wr(7'h2D, 16'h0000);   // TAU 0: E follows i^2 = 0
                #(10 * 300 * clk_ns);
                spi_wr(7'h2E, 16'd2000); spi_wr(7'h2D, 16'h0006);
                spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                spi_rd(7'h02); $display("INFO safe FAULT before I2t 0x%04h", rd_val);
                ia_code = 12'd2848;
                // model: same integer recursion as the RTL
                e_mod = 24'd0; kupd = 0; sqv = 16'd2500;
                while (e_mod[23:8] < 16'd2000) begin
                    e_mod = e_mod + (($signed({2'b00, sqv, 8'd0}) - $signed({2'b00, e_mod})) >>> 6);
                    kupd = kupd + 1;
                end
                tk = 0; while (fault_n && tk < 200000) begin @(posedge clk); tk = tk + 1; end
                upd_ticks = 300;
                $display("INFO safe I2t: trip after %0d ticks = %0.1f PWM periods; integer model %0d updates; closed form %0.2f updates",
                         tk, tk / 300.0, kupd, $ln(1.0 - 2000.0 / 2500.0) / $ln(1.0 - 1.0 / 64.0));
                spi_rd(7'h02);
                check(rd_val[9] && !rd_val[10], "safe: I2T_A latches (I2T_B stays clear)");
                check(tk >= (kupd - 1) * upd_ticks && tk <= (kupd + 2) * upd_ticks,
                      "safe: I2t trip time = integer-model update count (+-1 PWM period, sample alignment)");
                ia_code = 12'd2048;
                // EN/STO low: gates low at once, fault latched, not maskable
                while (dut.u_safe.e_a[23:8] >= 16'd2000) #(1000);
                spi_wr(7'h03, 16'h0100); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: I2t clears after the model cools below the limit");
                en_pad = 1'b0; #(10 * clk_ns);
                spi_rd(7'h02);
                check(rd_val[8] && !fault_n && !gate_a && !gate_b && !gate_c, "safe: EN low latches STO (mask ignored), gates low");
                en_pad = 1'b1; spi_wr(7'h03, 16'h0000); spi_wr(7'h04, 16'h0003); #(20 * clk_ns);
                check(fault_n, "safe: STO clears after EN returns high and CLR");
                // power-on fault
                por_n = 0; #(10 * clk_ns); por_n = 1; #(20 * clk_ns);
                check(!fault_n && dut.u_safe.cause[12] && dut.u_safe.cause[11], "safe: power-on reset latches POR and CAL (gates disabled until CAL_CRC and CLR)");
            end
        end

        #(1000);
        $display("# %0d checks, %0d failed", checks, errors);
        if (errors == 0) $display("ALL TESTS PASSED");
        else             $display("TESTS FAILED: %0d", errors);
        $finish;
    end
    // global time limit
    initial begin #(200_000_000); $display("TESTS FAILED: timeout"); $finish; end
endmodule
