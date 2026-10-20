// R1_CTRL / r1_bus: SPI register access on SCLK/SDI/SDO/CS_N (pads shared with
// MA/SLO; CS_N low selects SPI). Revision 0.2.
//
// SPI mode 0, 24-bit frames.
//   SDI: R/nW, A[6:0], D[15:0]     (write: D is written; read: D ignored)
//   SDO: STATUS[7:0], RD[15:0]     RD = result of the previous frame
//        (read data of a read command, echo of the written value after a write).
// Revision 0.2 removes the AS5047P-compatible mode of revision 0.1 (area trim
// listed in the 0.1 README; BUS_CFG bit 8 is reserved).
// Clocking: the shift logic runs on SCLK; its flops only update while CS_N is
// low, so they hold the received word after CS_N rises and MA traffic of a
// BiSS master on the same pad does not disturb them. The clk domain decodes
// the frame after CS_N rises (2-flop synchroniser) and prepares the next SDO
// word before the next CS_N fall (CS_N high time >= 8 clk ticks). The clk
// domain reads the received word, the bit count and the write data directly
// from the SCLK-domain flops (stable while CS_N is high); reg_addr is a
// clk-domain flip-flop loaded at the decode, so the latch enables of the
// register file never decode an address that moves with SCLK. The register
// file latches the write data in the tick after reg_wr, 3-5 ticks after CS_N
// rises, inside the >= 8-tick CS_N high time.
// SPDX-License-Identifier: Apache-2.0

module r1_spi (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        sclk,
    input  wire        cs_n,
    input  wire        sdi,
    output wire        sdo,
    // register file port (clk domain)
    output reg         reg_wr,
    output reg  [6:0]  reg_addr,
    output wire [15:0] reg_wdata,
    input  wire [15:0] reg_rdata,      // combinational read of reg_addr
    output reg         reg_rd,         // pulse: a register was read (read side effects)
    input  wire [7:0]  status8,
    // events
    output reg         frame_ok,       // pulse: well-formed frame decoded
    output reg  [3:0]  err_cnt         // saturating
);
    // ---------------- SCLK domain ----------------
    reg        fresh;
    reg [23:0] rx;
    reg [5:0]  rcnt;
    reg [4:0]  oidx;
    reg [23:0] tx_word;                // clk domain, stable while CS_N is low

    always @(posedge sclk or posedge cs_n) begin
        if (cs_n) fresh <= 1'b1;
        else      fresh <= 1'b0;
    end
    always @(posedge sclk or negedge rst_n) begin
        if (!rst_n) begin
            rx <= 24'd0; rcnt <= 6'd0;
        end else if (!cs_n) begin
            if (fresh) begin
                rx <= {23'd0, sdi}; rcnt <= 6'd1;
            end else begin
                rx <= {rx[22:0], sdi};
                if (rcnt != 6'd63) rcnt <= rcnt + 6'd1;
            end
        end
    end
    always @(negedge sclk or posedge cs_n) begin
        if (cs_n) oidx <= 5'd0;
        else if (oidx != 5'd31) oidx <= oidx + 5'd1;
    end
    assign sdo = (oidx < 5'd24) ? tx_word[5'd23 - oidx] : 1'b0;
    assign reg_wdata = rx[15:0];

    // ---------------- clk domain ----------------
    wire cs_s;
    r1_sync2 #(.W(1), .RST_VAL(1)) u_scs (.clk(clk), .rst_n(rst_n), .d(cs_n), .q(cs_s));
    reg        cs_d;
    reg [1:0]  ph;                     // decode phases after CS_N rise

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cs_d <= 1'b1; ph <= 2'd0; tx_word <= 24'd0; reg_wr <= 1'b0; reg_rd <= 1'b0;
            frame_ok <= 1'b0; err_cnt <= 4'd0; reg_addr <= 7'd0;
        end else begin
            cs_d <= cs_s;
            reg_wr <= 1'b0; reg_rd <= 1'b0; frame_ok <= 1'b0;
            case (ph)
                2'd0: if (cs_s && !cs_d) begin ph <= 2'd1; reg_addr <= rx[22:16]; end
                2'd1: begin
                    ph <= 2'd2;
                    if (rcnt == 6'd24) begin
                        reg_wr   <= ~rx[23];
                        frame_ok <= 1'b1;
                    end else begin
                        if (err_cnt != 4'hF) err_cnt <= err_cnt + 4'd1;
                        ph <= 2'd3;
                    end
                end
                2'd2: begin
                    // reg_addr decoded; prepare the next SDO word
                    ph      <= 2'd0;
                    tx_word <= {status8, rx[23] ? reg_rdata : rx[15:0]};
                    reg_rd  <= rx[23];
                end
                2'd3: begin
                    // malformed frame: status only, data 0
                    ph      <= 2'd0;
                    tx_word <= {status8, 16'd0};
                end
            endcase
        end
    end
endmodule
