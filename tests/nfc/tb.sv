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
    `PWM(0.50, 50e3, tx_mod);
    `MAKE_CONST_REAL(5.0, tx_mod_hi);
    `MAKE_CONST_REAL(4.0, tx_mod_lo);
    `ITE_REAL(tx_mod, tx_mod_hi, tx_mod_lo, tx_amp);
    `PWM(0.50, 13.56e6, tx);
    `ITE_REAL(tx, tx_amp, `MINUS_REAL(tx_amp), v_tx);

    // output has range range +/- 25 V
    `MAKE_REAL(v_hpf, 25.0);

    // filter instantiation
    nfc #(
        `PASS_REAL(v_tx, v_tx),
        `PASS_REAL(v_hpf, v_hpf)
    ) nfc_i (
        .v_tx(v_tx),
        .v_hpf(v_hpf),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `PROBE_ANALOG(v_tx);
    `PROBE_ANALOG(v_hpf);
endmodule

`default_nettype wire