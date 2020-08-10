module tb;
    // emulator I/O
    (* dont_touch = "true" *) logic emu_clk;
    (* dont_touch = "true" *) logic emu_rst;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] dt_req;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_dt;
    (* dont_touch = "true" *) logic clk_val;
    (* dont_touch = "true" *) logic clk_i;

    // low and high durations
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] t_lo;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] t_hi;

    // negate emu_dt
    // TODO: fix this (related to https://github.com/sgherbst/msdsl/issues/20)
    logic [((`DT_WIDTH)-1):0] neg_emu_dt;
    assign neg_emu_dt = -emu_dt;

    // oscillator
    osc osc_i (
        .emu_clk(emu_clk),
        .emu_rst(emu_rst),
        .dt_req(dt_req),
        .emu_dt(emu_dt),
        .neg_emu_dt(neg_emu_dt),
        .clk_val(clk_val),
        .t_lo(t_lo),
        .t_hi(t_hi)
    );
endmodule
