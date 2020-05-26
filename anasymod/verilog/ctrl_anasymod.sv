module ctrl_anasymod (
    input wire logic [((`TIME_WIDTH)-1):0] emu_time,
    input wire logic [((`DEC_WIDTH)-1):0] emu_dec_thr,
    input wire logic emu_clk,
    input wire logic emu_rst,
    output wire logic emu_dec_cmp
);
    // inputs from the top level

    // comparison
    logic [((`DEC_WIDTH)-1):0] emu_dec_cnt;
    assign emu_dec_cmp = (emu_dec_cnt == emu_dec_thr);

    // update count
    always @(posedge emu_clk) begin
        if (emu_rst == 1'b1) begin
            emu_dec_cnt <= 0;
        end else if (emu_dec_cmp == 1'b1) begin
            emu_dec_cnt <= 0;
        end else begin
            emu_dec_cnt <= emu_dec_cnt + 1;
        end
    end
endmodule