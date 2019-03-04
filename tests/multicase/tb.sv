// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // I/O definition
    `MAKE_CONST_REAL(1.0, v_in);
    `MAKE_REAL(v_out, 1.5);

    // gate drive signal
    `PWM(0.50, 300e3, ctrl);

    // filter instantiation
    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .ctrl(ctrl)
    );

    // emulation output
    `PROBE_ANALOG(v_out);
    `PROBE_DIGITAL(ctrl, 1);
endmodule

`default_nettype wire