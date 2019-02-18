// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`default_nettype none

module tb (
    input wire logic clk,
    input wire logic rst
);
    // signal instantiation
    logic a, b, a_inv, b_inv, a_and_b, a_or_b, a_xor_b;

    // module instantiation
    bitwise bitwise_i (
        .a(a),
        .b(b),
        .a_inv(a_inv),
        .b_inv(b_inv),
        .a_and_b(a_and_b),
        .a_or_b(a_or_b),
        .a_xor_b(a_xor_b),
        .clk(clk),
        .rst(rst)
    );

    integer i, j;
    initial begin
        for (i = 0; i <= 1; i = i+1) begin
            for (j = 0; j <= 1; j = j+1) begin
                a = i;
                b = j;
                #0;
                $display("******************");
                $display("a:       ", a);
                $display("b:       ", b);
                $display("a_inv:   ", a_inv);
                $display("b_inv:   ", b_inv);
                $display("a_and_b: ", a_and_b);
                $display("a_or_b:  ", a_or_b);
                $display("a_xor_b: ", a_xor_b);
            end
        end
        $finish;
    end
endmodule

`default_nettype wire