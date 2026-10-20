// R1_CTRL: read-only BiSS identification bytes, addresses 0x40..0x7F
// (BiSS C Rev D2 fixed register area; no EDS). Byte order: high byte at the
// lower address [verify against the D2 register table]. Unlisted addresses read 0.
// SPDX-License-Identifier: Apache-2.0

module r1_idrom #(
    parameter [15:0] PROFILE_ID = 16'h0001,
    parameter [47:0] DEV_ID     = 48'h52_31_4A_46_45_30,
    parameter [31:0] DEV_SN     = 32'h0000_0000,
    parameter [15:0] MFR_ID     = 16'h0000
) (
    input  wire [6:0] addr,
    output reg  [7:0] data
);
    always @(*) begin
        case (addr)
            7'h42: data = PROFILE_ID[15:8];  7'h43: data = PROFILE_ID[7:0];
            7'h44: data = DEV_SN[31:24];     7'h45: data = DEV_SN[23:16];
            7'h46: data = DEV_SN[15:8];      7'h47: data = DEV_SN[7:0];
            7'h78: data = DEV_ID[47:40];     7'h79: data = DEV_ID[39:32];
            7'h7A: data = DEV_ID[31:24];     7'h7B: data = DEV_ID[23:16];
            7'h7C: data = DEV_ID[15:8];      7'h7D: data = DEV_ID[7:0];
            7'h7E: data = MFR_ID[15:8];      7'h7F: data = MFR_ID[7:0];
            default: data = 8'h00;
        endcase
    end
endmodule
