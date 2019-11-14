interface emu_intf #(
    parameter integer dt_width=-1
);
    logic signed [(dt_width-1):0] dt;
    logic clk;
    logic rst;
endinterface
