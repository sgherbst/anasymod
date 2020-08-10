`timescale 1s/1ns

module tb;
    logic [7:0] a_in;
    logic [7:0] b_in;
    logic [7:0] mode_in;
    logic [7:0] c_out;

    always @(*) begin
        if (mode_in == 0) begin
            c_out = a_in + b_in;
        end else if (mode_in == 1) begin
            c_out = a_in - b_in;
        end else if (mode_in == 2) begin
            c_out = b_in - a_in;
        end else if (mode_in == 3) begin
            c_out = a_in * b_in;
        end else if (mode_in == 4) begin
            c_out = a_in >> b_in;
        end else if (mode_in == 5) begin
            c_out = a_in << b_in;
        end else if (mode_in == 6) begin
            c_out = b_in >> a_in;
        end else if (mode_in == 7) begin
            c_out = b_in << a_in;
        end else begin
            c_out = 42;
        end
    end
endmodule
