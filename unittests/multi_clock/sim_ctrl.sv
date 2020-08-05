`timescale 1s/1ns

module sim_ctrl #(
    parameter integer num_osc = 2
) (
    // osc_0
    input clk_0,
    output reg [31:0] t_lo_0,
    output reg [31:0] t_hi_0,

    // osc_1
    input clk_1,
    output reg [31:0] t_lo_1,
    output reg [31:0] t_hi_1
);
    // set t_lo
    real t_lo_val [0:(num_osc-1)];
    assign t_lo_val[0] = 0.123e-12;
    assign t_lo_0 = t_lo_val[0]/(`DT_SCALE);
    assign t_lo_val[1] = 0.234e-12;
    assign t_lo_1 = t_lo_val[1]/(`DT_SCALE);

    // set t_hi
    real t_hi_val [0:(num_osc-1)];
    assign t_hi_val[0] = 0.345e-12;
    assign t_hi_0 = t_hi_val[0]/(`DT_SCALE);
    assign t_hi_val[1] = 0.456e-12;
    assign t_hi_1 = t_hi_val[1]/(`DT_SCALE);

    // wire up clocks
    logic [(num_osc-1):0] clk_i;
    assign clk_i[0] = clk_0;
    assign clk_i[1] = clk_1;

    // logic to end test
    logic [(num_osc-1):0] done;
    always @(done) begin
        if ((&done) === 1'b1) begin
            $finish;
        end
    end

    // instantiate oscillators
    genvar i;
    generate
        for (i=0; i<num_osc; i=i+1) begin
            osc_checker #(
                .index(i)
            ) osc_checker_i (
                .t_lo_val(t_lo_val[i]),
                .t_hi_val(t_hi_val[i]),
                .clk_i(clk_i[i]),
                .done(done[i])
            );
        end
    endgenerate
endmodule
