
`timescale 1ns/1ps

`include "msdsl.sv"

`default_nettype none

module calc_emu_time #(
    parameter integer width=-1,
    parameter integer time_width=-1,
    parameter real tstop=-1
) (
    output var logic signed [(time_width-1):0] emu_time,
    input wire logic emu_clk,
    input wire logic emu_rst
);
    `MAKE_GENERIC_REAL(emu_time_int, 1.1*tstop, time_width);
    `COPY_FORMAT_REAL(emu_time_int, emu_time_next);
    `COPY_FORMAT_REAL(emu_time_int, emu_dt);

    `ASSIGN_CONST_REAL(0.0000001, emu_dt);
    `ADD_INTO_REAL(emu_time_int, emu_dt, emu_time_next);
    `MEM_INTO_ANALOG(emu_time_next, emu_time_int, 1'b1, `CLK_MSDSL, `RST_MSDSL, 0);
    assign emu_time = emu_time_int;
endmodule

`default_nettype wire