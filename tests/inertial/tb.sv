// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // gate drive signal
    `PWM(0.50, 10e3, in_);

    // filter instantiation
    logic out;
    inertial interial_i (
        .in_(in_),
        .out(out)
    );

    // emulation output
    `PROBE_DIGITAL(in_, 1);
    `PROBE_DIGITAL(out, 1);
endmodule

`default_nettype wire