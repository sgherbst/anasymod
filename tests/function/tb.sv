`include "svreal.sv"

module tb;
    // signals
    `MAKE_REAL(in_, 10.0);
    `MAKE_REAL(out, 10.0);

    // clock control
    logic clk, rst;
    clk_route clk_route_i (
        .clk(clk),
        .rst(rst)
    );

    // function
    model #(
       `PASS_REAL(in_, in_),
       `PASS_REAL(out, out)
    ) model_i (
        .in_(in_),
        .out(out),
        .clk(clk),
        .rst(rst)
    );
endmodule
