`include "svreal.sv"

module tb;
    // analog signals
    `MAKE_REAL(v_in, 10.0);
    `MAKE_REAL(v_out, 10.0);

    // control signals
    logic go_vio, rst_vio, clk;

    // clock control
    single_step_clk clk_gen (
        .go_i(go_vio),
        .clk_o(clk)
    );

    // filter
    model #(
       `PASS_REAL(v_in, v_in),
       `PASS_REAL(v_out, v_out) 
    ) model_i (
        .v_in(v_in),
        .v_out(v_out),
        .clk(clk),
        .rst(rst_vio)
    );
endmodule
