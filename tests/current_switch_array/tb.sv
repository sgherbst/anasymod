// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    localparam integer n_array=47;

    // analog inputs
    `MAKE_CONST_REAL(1.3, v_in);

    // analog outputs
    `MAKE_REAL(v_out, 5.0);

    // control signal
    logic [n_array-1:0] ctrl;

    // comparator instantiation
    current_switch_array #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) current_switch_array_i (
        .v_in(v_in),
        .ctrl(ctrl),
        .v_out(v_out)
    );

    // main stimulus logic
    integer i, j;
    initial begin
        ctrl = {n_array{1'b1}};
        for (i=0; i<n_array; i=i+1) begin
            for (j=0; j<10; j=j+1) begin
                @(posedge `CLK_MSDSL);
            end
            ctrl = ctrl >> 1;
        end
        $finish;
    end

endmodule

`default_nettype wire