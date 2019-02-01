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
    // input is voltage square wave

    // compute envelope
    `PWM(0.50, 50e3, in_env_dig);
    `MAKE_CONST_REAL(5.0, in_env_hi);
    `MAKE_CONST_REAL(4.0, in_env_lo);
    `ITE_REAL(in_env_dig, in_env_hi, in_env_lo, in_env);

    // apply to carrier
    `PWM(0.50, 13.56e6, in_dig);
    `ITE_REAL(in_dig, in_env, `MINUS_REAL(in_env), v_in);

    // output has range range +/- 25 V
    `MAKE_REAL(v_out, 1000);

    // filter instantiation
    nfc #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) nfc_i (
        .v_in(v_in),
        .v_out(v_out),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `PROBE_ANALOG(v_in);
    `PROBE_ANALOG(v_out);
endmodule

`default_nettype wire