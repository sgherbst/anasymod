`include "svreal.sv"

module clk_route (
    output wire logic clk,
    output wire logic rst
);
    // signals use for external I/O
    (* dont_touch = "true" *) logic __emu_clk;
    (* dont_touch = "true" *) logic __emu_rst;
    (* dont_touch = "true" *) logic __emu_clk_val;
    (* dont_touch = "true" *) logic __emu_clk_i;

    // assign clock value (unused)
    assign __emu_clk_val = 1'b0;

    // assign outputs
    assign clk = __emu_clk;
    assign rst = __emu_rst;
endmodule
