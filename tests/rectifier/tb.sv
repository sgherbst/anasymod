// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // gate drive signal

    `PWM(0.50, 1e6, ctrl);

    // generate square wave voltage
    `MAKE_REAL(v_in, 1.0);
    always @(*) begin
        case (ctrl)
            1'b0:    `FORCE_REAL(-1.0, v_in);
            1'b1:    `FORCE_REAL(+1.0, v_in);
            default: `FORCE_REAL(+1.0, v_in);
        endcase
    end

    // Output definition
    `MAKE_REAL(v_out, 1.5);

    // filter instantiation
    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out)
    );

endmodule

`default_nettype wire