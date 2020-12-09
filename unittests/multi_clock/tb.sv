module tb;
    // emulator I/O
    (* dont_touch = "true" *) logic clk_val_0;
    (* dont_touch = "true" *) logic clk_val_1;
    (* dont_touch = "true" *) logic clk_0;
    (* dont_touch = "true" *) logic clk_1;

    // oscillators
    osc osc_0 (.clk_val(clk_val_0));
    osc osc_1 (.clk_val(clk_val_1));
endmodule
