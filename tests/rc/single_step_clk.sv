`include "svreal.sv"

module single_step_clk (
    input wire logic go_i,
    output wire logic clk_o
);
    // signals use for external I/O
    (* dont_touch = "true" *) logic __emu_clk_val;
    (* dont_touch = "true" *) logic __emu_rst;
    (* dont_touch = "true" *) logic __emu_clk;
    (* dont_touch = "true" *) logic signed [((`DT_WIDTH)-1):0] __emu_dt;
    (* dont_touch = "true" *) logic signed [((`DT_WIDTH)-1):0] __emu_dt_req;
    (* dont_touch = "true" *) logic __emu_clk_i;

    // assign output clock (note that a module output pin cannot be directly
    // written hierachically)
    assign clk_o = __emu_clk_i;
    assign __emu_dt_req = 'd0;

    // single-stepping clock logic
    logic go_prev;
    always @(posedge __emu_clk) begin
        if (__emu_rst == 1'b1) begin
            __emu_clk_val <= 1'b0;
            go_prev <= 1'b0;
        end else if ((go_i == 1'b1) && (go_prev == 1'b0)) begin
            __emu_clk_val <= 1'b1;
            go_prev <= go_i;
        end else begin
            __emu_clk_val <= 1'b0;
            go_prev <= go_i;
        end
    end
endmodule
