// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb (
    input wire logic clk,
    input wire logic rst
);
    // I/O definition
    `MAKE_CONST_REAL(5.0, v_in);
    `MAKE_REAL(v_out, 10.0);
    `MAKE_REAL(i_mag, 20.0);

    // gate drive signal
    `PWM(0.50, 500e3, gate);

    // buck instantiation
    buck #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out),
        `PASS_REAL(i_mag, i_mag)
    ) buck_i (
        .v_in(v_in),
        .v_out(v_out),
        .i_mag(i_mag),
        .gate(gate),
        .clk(clk),
        .rst(rst)
    );

    // emulation output
    `PROBE_ANALOG(v_out);
    `PROBE_ANALOG(i_mag);

    // emulation control
    `MAKE_RESET_PROBE;
    `MAKE_TIME_PROBE;
endmodule

`default_nettype wire