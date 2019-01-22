// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"

`define PROBE(signal) \
    (* mark_debug = `"true`", fp_exponent = `EXPONENT_PARAM_REAL(signal), fp_width = `WIDTH_PARAM_REAL(signal) *) `DATA_TYPE_REAL(`WIDTH_PARAM_REAL(signal)) `PROBE_NAME_REAL(signal); \
    assign `PROBE_NAME_REAL(signal) = signal

module tb (
    input wire logic clk,
    input wire logic rst
);
    // input is a fixed value
    `MAKE_CONST_REAL(1.0, v_in);
    `PROBE(v_in);

    // output has range range +/- 1.5
    `MAKE_REAL(v_out, 1.5);
    `PROBE(v_out);

    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    integer f;
    initial begin
        f = $fopen("output.txt", "w");
    end
    always @(posedge clk) begin
        if (rst == 1'b0) begin
            $fwrite(f, "%f\n", `TO_REAL(v_out));
        end
    end
endmodule

