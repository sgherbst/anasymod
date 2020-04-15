
`timescale 1ns/1ps

`include "svreal.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    initial begin
        $error("test error");
    end
endmodule

`default_nettype wire