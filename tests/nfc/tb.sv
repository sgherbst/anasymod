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
    `PWM(0.50, 13.56e6, tx_clk);

    // compute communication waveforms
    `PWM(0.50, 100e3, comm_sig);
    `PWM(0.50, 1.0/`TSTOP_MSDSL, comm_sel);

    // assign TX and RX communication signals
    logic tx_send, rx_send;
    assign tx_send = comm_sig &   comm_sel;
    assign rx_send = comm_sig & (~comm_sel);

    // other signals
    logic tx_recv, rx_recv, rx_clk;

    // filter instantiation
    nfc nfc_i (
        .tx_send(tx_send),
        .rx_send(rx_send),
        .tx_recv(tx_recv),
        .rx_recv(rx_recv),
        .tx_clk(tx_clk),
        .rx_clk(rx_clk),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `PROBE_DIGITAL(tx_send, 1);
    `PROBE_DIGITAL(rx_send, 1);
    `PROBE_DIGITAL(tx_recv, 1);
    `PROBE_DIGITAL(rx_recv, 1);
    `PROBE_DIGITAL(tx_clk, 1);
    `PROBE_DIGITAL(rx_clk, 1);
endmodule

`default_nettype wire