// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "svreal.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // analog inputs
    `MAKE_CONST_REAL(1.3, v_in);

    // analog outputs
    `MAKE_REAL(v_out, 5.0);

    // digital inputs
    `PWM(0.50, 3e9, ctrl);

    // comparator instantiation
    current_switch #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) current_switch_i (
        .v_in(v_in),
        .ctrl(ctrl),
        .v_out(v_out)
    );

endmodule

`default_nettype wire