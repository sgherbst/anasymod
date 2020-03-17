// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "svreal.sv"
`include "msdsl.sv"

`default_nettype none

module tb;
    // analog inputs
    `MAKE_REAL(in_p, 10.0);
    `MAKE_CONST_REAL(3.45, in_n);

    // digital inputs
    logic clk;

    // digital outputs
    logic out;

    // comparator instantiation
    comparator #(
        `PASS_REAL(in_p, in_p),
        `PASS_REAL(in_n, in_n)
    ) comparator_i (
        .in_p(in_p),
        .in_n(in_n),
        .clk(clk),
        .out(out)
    );

    // main stimulus
    real stim;
    initial begin
        clk = 1'b0;

        for (stim=0.0; stim < 10.0; stim = stim + 0.25) begin
            `FORCE_REAL(stim, in_p);
            #(1ns);
            clk = 1'b1;
            #(1ns);
            clk = 1'b0;

            $display("in_p: %0.3f, in_n: %0.3f, out: %0b", `TO_REAL(in_p), `TO_REAL(in_n), out);
        end

        $finish;
    end
endmodule

`default_nettype wire