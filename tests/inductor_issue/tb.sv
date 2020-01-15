// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;

    localparam real sw_duty = 0.5;    // duty cycle of gate drive
    localparam real sw_freq = 1e6;    // frequency of gate drive

    `PWM(sw_duty, sw_freq, gate);

    // input is a fixed value
    `MAKE_CONST_REAL(1.0, v_in);

    // output has range range +/- 1.5
    `MAKE_REAL(v_out, 1.5);

    // filter instantiation
    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .sw1(1'b1),
        .sw2(gate)
    );

endmodule

`default_nettype wire