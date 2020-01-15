// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // input is voltage square wave
    `PWM(0.50, 1e6, in_dig);
    `MAKE_CONST_REAL(+1.0, in_hi);
    `MAKE_CONST_REAL(-1.0, in_lo);
    `ITE_REAL(in_dig, in_hi, in_lo, v_in);

    // output has range range +/- 10
    `MAKE_REAL(v_out, 15.0);

    initial begin
        $display(`DT_MSDSL);
    end

    // filter instantiation
    rlc #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) rlc_i (
        .v_in(v_in),
        .v_out(v_out)
    );

endmodule

`default_nettype wire