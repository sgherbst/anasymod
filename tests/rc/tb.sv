`include "svreal.sv"

module tb;
    // signals
    (* dont_touch="true" *) logic signed [24:0] v_in_vio;
    (* dont_touch="true" *) logic signed [24:0] v_out_vio;
    (* dont_touch="true" *) logic go_vio;
    (* dont_touch="true" *) logic rst_vio;
    (* dont_touch="true" *) logic clk;

    // declare SVREAL signals
    (* dont_touch="true" *) `REAL_FROM_WIDTH_EXP(v_in, 25, `ANALOG_EXPONENT);
    (* dont_touch="true" *) `REAL_FROM_WIDTH_EXP(v_out, 25, `ANALOG_EXPONENT);
    assign v_in = v_in_vio;
    assign v_out_vio = v_out;

    // clock control
    (* dont_touch="true" *) single_step_clk clk_gen (
        .go_i(go_vio),
        .clk_o(clk)
    );

    // filter
    (* dont_touch="true" *) model #(
       `PASS_REAL(v_in, v_in),
       `PASS_REAL(v_out, v_out) 
    ) model_i (
        .v_in(v_in),
        .v_out(v_out),
        .clk(clk),
        .rst(rst_vio)
    );
endmodule
