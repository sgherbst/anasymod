module tb;
    // emulator I/O
    (* dont_touch = "true" *) logic clk_val_0;
    (* dont_touch = "true" *) logic clk_val_1;
    (* dont_touch = "true" *) logic clk_0;
    (* dont_touch = "true" *) logic clk_1;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_dt;

    // negate emu_dt
    // TODO: fix this (related to https://github.com/sgherbst/msdsl/issues/20)
    logic [((`DT_WIDTH)-1):0] neg_emu_dt;
    assign neg_emu_dt = -emu_dt;

    // oscillators
    osc osc_0 (.clk_val(clk_val_0), .neg_emu_dt(neg_emu_dt));
    osc osc_1 (.clk_val(clk_val_1), .neg_emu_dt(neg_emu_dt));
endmodule
