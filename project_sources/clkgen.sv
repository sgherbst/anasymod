`timescale 1ns/1ps

`default_nettype none

module clkgen (
    input wire logic SYSCLK,
    //input wire logic SYSCLK_N,
    output wire logic clk
);

    logic locked;

    clk_wiz_0 clk_wiz_0_i(
        // I/O for MMCM
        .reset(1'b0),
        .locked(locked),
        
        // input clock (differential)
        //.clk_in1_p(SYSCLK_P),
        //.clk_in1_n(SYSCLK_N),
        .clk_in1(SYSCLK),
        
        // main clock
        .clk_out1(clk)

        // clock used for debug hub

        
        // clock used for ila sampling


    );

endmodule

`default_nettype wire
