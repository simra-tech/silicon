// R1_CTRL: sine table for the r1_pos 3rd-harmonic angle correction.
// Generated: round(127*sin(2*pi*i/256)), quarter wave i = 0..64, folded to 256 entries.
// SPDX-License-Identifier: Apache-2.0

module r1_sinlut (
    input  wire [7:0] idx,      // phase, 1/256 turn
    output reg  signed [7:0] val
);
    reg [5:0] a; reg [6:0] m; reg [6:0] q;
    always @(*) begin
        // fold: quadrant idx[7:6]; index within the quadrant runs up (q0, q2) or down (q1, q3)
        m = idx[6] ? (7'd64 - {1'b0, idx[5:0]}) : {1'b0, idx[5:0]};
        case (m)
            7'd0: q = 7'd0;
            7'd1: q = 7'd3;
            7'd2: q = 7'd6;
            7'd3: q = 7'd9;
            7'd4: q = 7'd12;
            7'd5: q = 7'd16;
            7'd6: q = 7'd19;
            7'd7: q = 7'd22;
            7'd8: q = 7'd25;
            7'd9: q = 7'd28;
            7'd10: q = 7'd31;
            7'd11: q = 7'd34;
            7'd12: q = 7'd37;
            7'd13: q = 7'd40;
            7'd14: q = 7'd43;
            7'd15: q = 7'd46;
            7'd16: q = 7'd49;
            7'd17: q = 7'd51;
            7'd18: q = 7'd54;
            7'd19: q = 7'd57;
            7'd20: q = 7'd60;
            7'd21: q = 7'd63;
            7'd22: q = 7'd65;
            7'd23: q = 7'd68;
            7'd24: q = 7'd71;
            7'd25: q = 7'd73;
            7'd26: q = 7'd76;
            7'd27: q = 7'd78;
            7'd28: q = 7'd81;
            7'd29: q = 7'd83;
            7'd30: q = 7'd85;
            7'd31: q = 7'd88;
            7'd32: q = 7'd90;
            7'd33: q = 7'd92;
            7'd34: q = 7'd94;
            7'd35: q = 7'd96;
            7'd36: q = 7'd98;
            7'd37: q = 7'd100;
            7'd38: q = 7'd102;
            7'd39: q = 7'd104;
            7'd40: q = 7'd106;
            7'd41: q = 7'd107;
            7'd42: q = 7'd109;
            7'd43: q = 7'd111;
            7'd44: q = 7'd112;
            7'd45: q = 7'd113;
            7'd46: q = 7'd115;
            7'd47: q = 7'd116;
            7'd48: q = 7'd117;
            7'd49: q = 7'd118;
            7'd50: q = 7'd120;
            7'd51: q = 7'd121;
            7'd52: q = 7'd122;
            7'd53: q = 7'd122;
            7'd54: q = 7'd123;
            7'd55: q = 7'd124;
            7'd56: q = 7'd125;
            7'd57: q = 7'd125;
            7'd58: q = 7'd126;
            7'd59: q = 7'd126;
            7'd60: q = 7'd126;
            7'd61: q = 7'd127;
            7'd62: q = 7'd127;
            7'd63: q = 7'd127;
            7'd64: q = 7'd127;
            default: q = 7'd0;
        endcase
        val = idx[7] ? -$signed({1'b0, q}) : $signed({1'b0, q});
    end
endmodule
