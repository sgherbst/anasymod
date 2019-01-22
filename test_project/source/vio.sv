`timescale 1ns/1ps

`default_nettype none

module vio (
    input wire logic clk,
    output wire logic rst
);

    vio_0 vio_0_i (
        .clk(clk),
        .probe_out0(rst)
    );

endmodule

`default_nettype wire
