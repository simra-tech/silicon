// R1_CTRL / r1_bus: BiSS-C (Rev D2, point-to-point sensor slave) and SSI slave
// on the shared MA/SLO pads. Revision 0.2.
//
// Clock domains
//   ma   : frame shift logic, clocked by the MA pad (rising edge drives SLO).
//   clk  : timeout, latch handshake, frame data, control channel (CDM/CDS).
// Crossings
//   ma -> clk : lat_tog (toggle at LAT), ma_tog (toggle per MA rising edge) and
//               the MA level, each through r1_sync2; lat_tog also through a
//               falling-edge first stage (half-tick latch timing, below).
//   clk -> ma : rdy_tog through a negedge/posedge pair of MA flops; frame data
//               (fd, cds) are held stable by the handshake (written by clk
//               before rdy_tog changes, read by ma after it sees the change).
//   clk -> ma reset : ma_rst_n (registered in clk, plus the CS_N pad and rst_n,
//               assert-only paths); released only while MA is quiet.
// Frame (BiSS, D2 "BiSS FRAME"): idle 1, LAT = first rising MA edge after a
// falling edge, ACK 0 at the next rising edge, busy 0 until the handshake
// completes (t_busy >= 2 T_MA, D2 Table 10 item 10a), START 1, CDS, data MSB
// first ([MT16] ST nE nW), CRC-6 0x43 start 0 inverted, stop bit 0 at the last
// rising MA edge (STP, D2 p. 7), 0 until the timeout ends, then 1.
// CDM = inverted MA level at the end of the timeout.
// Frame (SSI): first falling edge freezes the published word, data MSB first
// from the first rising edge, then 0 for the monoflop time (= TIMEOUT_TICKS), 1.
// Revision 0.2 changes:
//  - one unshifted frame word fd for BiSS and SSI, sent by bit index (no
//    MA-domain copy, no separate SSI word, no variable shifters);
//  - half-tick LAT timing: when the LAT toggle was already captured by the
//    falling clk edge half a tick before the rising-edge capture, the latched
//    position is moved back by half a tick of travel (VELOCITY / 16);
//  - control channel per D2 "CONTROL COMMUNICATION" (pp. 13-17), see below.
// SPDX-License-Identifier: Apache-2.0

module r1_biss #(
    parameter [15:0] PROFILE_ID = 16'h0001,      // placeholder, see R1_REGISTER_MAP.md 4.9
    parameter [47:0] DEV_ID     = 48'h52_31_4A_46_45_30, // "R1JFE0"
    parameter [31:0] DEV_SN     = 32'h0000_0000,
    parameter [15:0] MFR_ID     = 16'h0000       // not assigned yet (spec open item 5)
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ma,             // MA/SCLK pad (level-shifted)
    input  wire        cs_n,           // CS_N pad: low = SPI owns the pads
    output wire        slo,
    // configuration (clk domain, quasi-static)
    input  wire        ssi_mode,
    input  wire        gray,
    input  wire        mt_en,
    input  wire [4:0]  st_len,         // 10..18 single-turn bits
    input  wire [11:0] timeout_ticks,
    input  wire        lat_half_en,    // half-tick LAT correction enable
    // frame content (clk domain)
    input  wire [17:0] pos,            // extrapolated position, 16.2
    input  wire [15:0] turns,
    input  wire [15:0] velocity,       // signed, 2^-5 LSB16 per tick, same sign as pos
    input  wire        err,            // -> nE = 0
    input  wire        warn,           // -> nW = 0
    input  wire        null_val,       // position invalid: data all 0, nE = 0
    // events (clk domain)
    output reg         frame_end,      // pulse at the end of a frame timeout
    output reg         lat_seen,       // pulse when a BiSS LAT has been captured
    output reg  [3:0]  cc_err_cnt,     // control-channel CRC errors and refused accesses (saturating)
    output reg  [7:0]  frame_cnt
);
    // =====================================================================
    // clk domain: activity, timeout, arming, reset of the ma domain
    // =====================================================================
    wire ma_s, mtog_s, ltog_s;
    reg  ma_tog, lat_tog;               // ma domain, defined below
    r1_sync2 #(.W(1), .RST_VAL(1)) u_sma (.clk(clk), .rst_n(rst_n), .d(ma),      .q(ma_s));
    r1_sync2 #(.W(1))             u_smt (.clk(clk), .rst_n(rst_n), .d(ma_tog),  .q(mtog_s));
    r1_sync2 #(.W(1))             u_slt (.clk(clk), .rst_n(rst_n), .d(lat_tog), .q(ltog_s));
    wire cs_s;
    r1_sync2 #(.W(1), .RST_VAL(1)) u_scs (.clk(clk), .rst_n(rst_n), .d(cs_n), .q(cs_s));

    reg        ma_d, mtog_d, ltog_d;
    reg [11:0] idle_cnt;
    reg        armed, frame_act;
    reg [1:0]  to_rst;                  // reset pulse for the ma domain
    reg        cdm, cdm_stb;
    wire activity = (ma_s != ma_d) | (mtog_s != mtog_d);
    wire to_hit = (idle_cnt == timeout_ticks);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ma_d <= 1'b1; mtog_d <= 1'b0; idle_cnt <= 12'd0;
            armed <= 1'b0; frame_act <= 1'b0; to_rst <= 2'b00;
            cdm <= 1'b0; cdm_stb <= 1'b0; frame_end <= 1'b0; frame_cnt <= 8'd0;
        end else begin
            ma_d <= ma_s; mtog_d <= mtog_s;
            cdm_stb <= 1'b0; frame_end <= 1'b0;
            to_rst <= {to_rst[0], 1'b0};
            if (!cs_s) begin
                idle_cnt <= 12'd0; armed <= 1'b0; frame_act <= 1'b0;
            end else if (activity) begin
                idle_cnt <= 12'd0;
                if (armed) frame_act <= 1'b1;
            end else if (!to_hit) begin
                idle_cnt <= idle_cnt + 12'd1;
            end else begin
                // MA quiet for TIMEOUT_TICKS
                if (!armed) armed <= 1'b1;
                if (frame_act) begin
                    frame_act <= 1'b0;
                    to_rst    <= 2'b11;
                    cdm       <= ~ma_s;           // CDM is sent inverted on MA
                    cdm_stb   <= ~ssi_mode;
                    frame_end <= 1'b1;
                    frame_cnt <= frame_cnt + 8'd1;
                end
            end
        end
    end
    // Reset of the ma domain (revision 0.5, CDC finding F of the 0.4 sign-off): the clk-domain terms (armed, frame
    // timeout pulse) are registered in ma_rel (asynchronously cleared by rst_n), so a change of `armed` and of
    // `to_rst` in the same tick cannot produce a runt pulse on the reset net. The only other input is the CS_N pad:
    // it asserts the reset when it falls. It releases it only when ma_rel is already 1, i.e. never while CS_N
    // was low, because `armed` is cleared while CS_N is low (>= 24 SCLK cycles, longer than the 2 ticks of ma_rel).
    // ma_rel changes only at clk edges: the release of the ma-domain reset is synchronous to clk (not to MA; see the CDC
    // table, crossing E: the release is issued only after MA has been quiet for TIMEOUT_TICKS).
    reg ma_rel;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) ma_rel <= 1'b0;
        else        ma_rel <= armed & ~to_rst[1];
    wire ma_rst_n = ma_rel & cs_n;

    // =====================================================================
    // clk domain: half-tick LAT timing
    //   n1 samples lat_tog on the falling clk edge, n2/n3 re-time it on the
    //   rising edge. When the rising-edge chain (ltog_s) shows the new toggle,
    //   n3 shows it in the same tick only if n1 captured it half a tick before
    //   the rising-edge capture, i.e. the LAT edge came in the first half of
    //   the clk period and the capture is half a tick later than for an edge in
    //   the second half.
    // =====================================================================
    reg n1;
    always @(negedge clk or negedge rst_n)
        if (!rst_n) n1 <= 1'b0; else n1 <= lat_tog;
    reg n2, n3;
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin n2 <= 1'b0; n3 <= 1'b0; end else begin n2 <= n1; n3 <= n2; end
    wire        early = lat_half_en & (n3 == ltog_s);
    wire [33:0] vh    = {{22{velocity[15]}}, velocity[15:4]};       // half a tick of travel, 16.2 bit
    wire [33:0] tp    = {turns, pos} - (early ? vh : 34'd0);

    // =====================================================================
    // clk domain: latch handshake and frame data
    // fd holds {MT[15:0], ST[17:0] (MSB-aligned), nE, nW} unshifted; the MA
    // domain selects the transmitted bit by index (revision 0.2: no variable
    // 36-bit shifters). Bit i of the data field (MSB first):
    //   i < OFF            : MT[15 - i]           OFF = 16 if MT_EN else 0
    //   j = i - OFF < ST_N : ST[17 - j]
    //   j = ST_N, ST_N + 1 : nE, nW               (BiSS only)
    // =====================================================================
    reg        rdy_tog;
    reg [35:0] fd;
    reg        cds_cur;                 // CDS of the next frame
    reg        cds_frame;               // CDS frozen for the current frame

    wire [5:0]  st_n   = (st_len < 5'd10) ? 6'd10 : (st_len > 5'd18) ? 6'd18 : {1'b0, st_len};
    wire [5:0]  off    = mt_en ? 6'd16 : 6'd0;
    wire [5:0]  nbits  = off + st_n + (ssi_mode ? 6'd0 : 6'd2);
    wire [35:0] fd_n   = null_val ? 36'd0 : {tp[33:18], tp[17:0], ~err, ~warn};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ltog_d <= 1'b0; rdy_tog <= 1'b0; fd <= 36'd0; cds_frame <= 1'b0;
            lat_seen <= 1'b0;
        end else begin
            ltog_d   <= ltog_s;
            lat_seen <= 1'b0;
            if (ssi_mode) begin
                // SSI: publish while MA is idle high and no frame is running
                if (ma_s && !frame_act) fd <= fd_n;
            end else if (ltog_s != ltog_d) begin
                fd        <= fd_n;
                cds_frame <= cds_cur;
                lat_seen  <= 1'b1;
            end
            if (ltog_s != ltog_d) rdy_tog <= ltog_s;
        end
    end

    // =====================================================================
    // ma domain: frame shift logic (bit index into fd)
    // =====================================================================
    localparam M_IDLE = 3'd0, M_ACK = 3'd1, M_BUSY = 3'd2, M_CDS = 3'd3, M_DATA = 3'd4,
               M_CRC = 3'd5, M_STOP = 3'd6, M_SSI = 3'd7;
    reg [2:0]  mst;
    reg [5:0]  bidx;                    // index of the next data bit
    reg [5:0]  crc;
    reg        slo_q;
    reg        prev_b;                  // previous binary bit (SSI Gray code)
    reg        fall_seen;
    reg        rdy_n1, rdy_p2;          // clk -> ma synchroniser (negedge, then posedge)
    wire [5:0] jdx = bidx - off;
    wire [3:0] mi  = 4'd15 - bidx[3:0];
    wire [4:0] si  = 5'd17 - jdx[4:0];
    wire       cur = (bidx < off)    ? fd[20 + mi] :
                     (jdx < st_n)    ? fd[2 + si]  :
                     (jdx == st_n)   ? fd[1] : fd[0];
    wire       cur_s = cur ^ (gray & prev_b);                   // SSI: Gray over the word

    always @(negedge ma or negedge ma_rst_n) begin
        if (!ma_rst_n) begin fall_seen <= 1'b0; rdy_n1 <= 1'b0; end
        else begin fall_seen <= 1'b1; rdy_n1 <= rdy_tog; end
    end
    // ma_tog and lat_tog survive the frame reset (only rst_n clears them)
    always @(posedge ma or negedge rst_n) begin
        if (!rst_n) ma_tog <= 1'b0;
        else        ma_tog <= ~ma_tog;
    end

    wire [5:0] crc_nx = {crc[4:0], 1'b0} ^ ((crc[5] ^ cur) ? 6'h03 : 6'h00);

    always @(posedge ma or negedge ma_rst_n) begin
        if (!ma_rst_n) begin
            mst <= M_IDLE; bidx <= 6'd0; crc <= 6'd0; slo_q <= 1'b1; rdy_p2 <= 1'b0; prev_b <= 1'b0;
        end else begin
            rdy_p2 <= rdy_n1;
            case (mst)
                M_IDLE: if (fall_seen) begin
                    if (ssi_mode) begin
                        slo_q  <= cur_s;     // bidx = 0: MSB
                        prev_b <= cur;
                        bidx   <= 6'd1;
                        mst    <= M_SSI;
                    end else begin
                        mst   <= M_ACK;      // this edge is LAT (lat_tog toggled below)
                    end
                end
                M_ACK:  begin slo_q <= 1'b0; mst <= M_BUSY; end
                M_BUSY: if (rdy_p2 == lat_tog) begin
                    slo_q <= 1'b1;           // START
                    bidx  <= 6'd0;
                    crc   <= 6'd0;
                    mst   <= M_CDS;
                end
                M_CDS:  begin slo_q <= cds_frame; mst <= M_DATA; end
                M_DATA: begin
                    slo_q <= cur;
                    crc   <= crc_nx;
                    bidx  <= bidx + 6'd1;
                    if (bidx + 6'd1 == nbits) mst <= M_CRC;
                end
                M_CRC:  begin
                    slo_q <= ~crc[5];
                    crc   <= {crc[4:0], 1'b0};
                    bidx  <= bidx + 6'd1;
                    if (bidx == nbits + 6'd5) mst <= M_STOP;
                end
                M_STOP: slo_q <= 1'b0;
                M_SSI:  begin
                    if (bidx != nbits) begin
                        slo_q  <= cur_s;
                        prev_b <= cur;
                        bidx   <= bidx + 6'd1;
                    end else slo_q <= 1'b0;      // monoflop: low until the timeout
                end
                default: mst <= M_IDLE;
            endcase
        end
    end
    // LAT toggle: separate flop so the frame reset does not clear it
    always @(posedge ma or negedge rst_n) begin
        if (!rst_n) lat_tog <= 1'b0;
        else if (mst == M_IDLE && fall_seen && !ssi_mode) lat_tog <= ~lat_tog;
    end
    // SLO reads 0 (busy) until the slave is armed (after reset and after SPI use),
    // so a master does not start a frame that would be ignored
    assign slo = slo_q & armed;

    // =====================================================================
    // clk domain: control channel (D2 "CONTROL COMMUNICATION", register read)
    // One CDM bit is received per frame (end of timeout); the CDS bit that
    // answers it is sent in the next frame (D2 p. 14). Point-to-point slave
    // with no SLI input, i.e. slave 0 of D2 Figure 26.
    //   CDM: S CTS ID[2:0] ADR[6:0] CRC[3:0] R W S  (13 bits don't care)
    //   CDS: IDL0 = 1 (this slave takes ID 0), IDL1..8 = 0, 0 ..., then
    //        R and W repeated (W inverted when the access is refused), S
    //        repeated, D[7:0], CRC[3:0], P.
    //   Header CRC-4: polynomial 0x13, start 0, over CTS + ID + ADR (11 bits),
    //   sent inverted; the start bit is excluded (D2 p. 14). Data CRC-4: same
    //   polynomial over the data byte only, inverted (D2 p. 16).
    //   Accepted: CTS = 1, ID = 0, CRC correct, R = 1, W = 0, readable address
    //   (r1_idrom ok). A CRC error: ignore the rest of the frame (D2 p. 16).
    //   P = 0 when ADR + 1 is readable, else 1 (D2 p. 16); after P = 0 a new
    //   CDM start bit reads ADR + 1 (sequential read, D2 Figure 30).
    //   14 consecutive CDM = 0 reset the channel to idle (D2 p. 15).
    //   BiSS commands (CTS = 0) are not supported: the frame is ignored.
    // =====================================================================
    localparam C_IDLE = 3'd0, C_HDR = 3'd1, C_R = 3'd2, C_W = 3'd3, C_S = 3'd4,
               C_TX = 3'd5, C_WAIT = 3'd6;
    reg [2:0]  cst;
    reg [3:0]  ccnt;
    reg [14:0] hdr;                    // CTS ID ADR CRC
    reg [6:0]  adr;
    reg [12:0] ctx;                    // D CRC P
    reg [3:0]  zcnt;

    function [3:0] crc4_step;
        input [3:0] c; input b;
        begin crc4_step = {c[2:0], 1'b0} ^ ((c[3] ^ b) ? 4'h3 : 4'h0); end
    endfunction
    function [3:0] crc4_11;
        input [10:0] d;
        integer i;
        reg [3:0] c;
        begin c = 4'd0; for (i = 10; i >= 0; i = i - 1) c = crc4_step(c, d[i]); crc4_11 = c; end
    endfunction
    function [3:0] crc4_8;
        input [7:0] d;
        integer i;
        reg [3:0] c;
        begin c = 4'd0; for (i = 7; i >= 0; i = i - 1) c = crc4_step(c, d[i]); crc4_8 = c; end
    endfunction

    wire [14:0] hdr_n   = {hdr[13:0], cdm};
    wire        hdr_crc = (hdr_n[3:0] == ~crc4_11(hdr_n[14:4]));
    wire        hdr_ok  = hdr_crc && hdr_n[14] && (hdr_n[13:11] == 3'd0);
    wire [7:0]  rd_byte;
    wire        rd_ok;
    r1_idrom #(.PROFILE_ID(PROFILE_ID), .DEV_ID(DEV_ID), .DEV_SN(DEV_SN), .MFR_ID(MFR_ID))
        u_rom (.addr(adr), .data(rd_byte), .ok(rd_ok));
    wire        nxt_ok;
    r1_idrom #(.PROFILE_ID(PROFILE_ID), .DEV_ID(DEV_ID), .DEV_SN(DEV_SN), .MFR_ID(MFR_ID))
        u_rom_n (.addr(adr + 7'd1), .data(), .ok(nxt_ok));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cst <= C_IDLE; ccnt <= 4'd0; hdr <= 15'd0; adr <= 7'd0; ctx <= 13'd0; zcnt <= 4'd0;
            cds_cur <= 1'b0; cc_err_cnt <= 4'd0;
        end else if (cdm_stb) begin
            if (cdm) zcnt <= 4'd0; else if (zcnt != 4'd14) zcnt <= zcnt + 4'd1;
            if (!cdm && zcnt == 4'd13) begin
                cst <= C_IDLE; cds_cur <= 1'b0;          // 14 x CDM = 0: reset
            end else case (cst)
                C_IDLE: begin
                    cds_cur <= cdm;                      // IDL0 = 1 after the start bit
                    if (cdm) begin cst <= C_HDR; ccnt <= 4'd0; end
                end
                C_HDR: begin
                    cds_cur <= 1'b0;                     // IDL1..IDL8 and the rest: 0
                    hdr  <= hdr_n;
                    ccnt <= ccnt + 4'd1;
                    if (ccnt == 4'd14) begin
                        adr <= hdr_n[10:4];
                        if (hdr_ok) cst <= C_R;
                        else begin
                            if (!hdr_crc) if (cc_err_cnt != 4'hF) cc_err_cnt <= cc_err_cnt + 4'd1;
                            cst <= C_WAIT;
                        end
                    end
                end
                C_R: begin cds_cur <= cdm; hdr[0] <= cdm; cst <= C_W; end
                C_W: begin
                    // accept: R = 1, W = 0 and a readable address; else W inverted
                    if (hdr[0] && !cdm && rd_ok) begin
                        cds_cur <= cdm; cst <= C_S;
                    end else begin
                        cds_cur <= ~cdm; cst <= C_WAIT;
                        if (cc_err_cnt != 4'hF) cc_err_cnt <= cc_err_cnt + 4'd1;
                    end
                end
                C_S: begin
                    cds_cur <= cdm;                      // repeat the start bit
                    if (cdm) begin
                        ctx  <= {rd_byte, ~crc4_8(rd_byte), ~nxt_ok};
                        ccnt <= 4'd0;
                        cst  <= C_TX;
                    end
                end
                C_TX: begin
                    cds_cur <= ctx[12];
                    ctx     <= {ctx[11:0], 1'b0};
                    ccnt    <= ccnt + 4'd1;
                    if (ccnt == 4'd12) begin
                        if (ctx[12]) cst <= C_WAIT;      // P = 1: no next byte
                        else begin adr <= adr + 7'd1; cst <= C_S; end
                    end
                end
                default: cds_cur <= 1'b0;                // C_WAIT: until 14 x CDM = 0
            endcase
        end
    end
endmodule
