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

    // compute carrier
    `PWM(0.50, 13.56e6, carrier);
    `MAKE_CONST_REAL(5.0, v_in_ampl);
    `ITE_REAL(carrier, v_in_ampl, `MINUS_REAL(v_in_ampl), v_in);

    // compute communication waveforms
    `PWM(0.50, 50.0e3, comm_sig);
    `PWM(0.50, 6.25e3, comm_sel);

    // assign TX and RX communication signals
    logic tx, rx;
    assign tx = comm_sig &   comm_sel;
    assign rx = comm_sig & (~comm_sel);

    // output has range range +/- 100 V
    `MAKE_REAL(v_out, 100);

    // filter instantiation
    nfc #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) nfc_i (
        .v_in(v_in),
        .v_out(v_out),
        .tx(tx),
        .rx(rx),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `PROBE_ANALOG(v_in);
    `PROBE_ANALOG(v_out);
    `PROBE_DIGITAL(tx, 1);
    `PROBE_DIGITAL(rx, 1);
endmodule

`default_nettype wire