`ifndef __ANASYMOD_SV__
`define __ANASYMOD_SV__

task wait_emu_rst;
    @(negedge top.emu_rst);
endtask

task wait_emu_cycles(input integer n);
    repeat (n) @(posedge top.emu_clk);
endtask

`endif // `ifndef __ANASYMOD_SV__