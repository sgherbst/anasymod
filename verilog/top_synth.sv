`timescale 1ns/1ps

`default_nettype none

module top (
    input wire logic ext_clk
);
    logic emu_clk;
    logic emu_rst;

    // testbench
    tb tb_i (
        .clk(emu_clk),
        .rst(emu_rst)
    );

    // clock generator
    logic dbg_hub_clk, locked;
    clk_wiz_0 clk_wiz_0_i(
        .reset(1'b0),
        .locked(locked),
        .clk_in1(ext_clk),
        .clk_out1(emu_clk),
        .clk_out2(dbg_hub_clk)
    );

    // reset generator
    vio_0 vio_0_i (
        .clk(emu_clk),
        .probe_out0(emu_rst)
    );

    // emulation management
    `MAKE_RESET_PROBE;
    `MAKE_TIME_PROBE;
endmodule

`default_nettype wire

