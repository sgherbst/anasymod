module osc_model_anasymod (
    output wire logic cke
);
    // inputs from the top level
    (* dont_touch = "true" *) logic __emu_clk;
    (* dont_touch = "true" *) logic __emu_rst;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt;

    // outputs to the top level
    (* dont_touch = "true" *) logic __emu_clk_val;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt_req;

    // Compute amount of time clock should be low vs. high;
    localparam longint t_int = (`EMU_DT)/(`DT_SCALE);

    // main logic
    // note that it is only necessary to save the emulation time up
    // to `DT_WIDTH, due to the properties of modular arithmetic

    logic [((`DT_WIDTH)-1):0] emu_time;
    logic [((`DT_WIDTH)-1):0] nxt_time;

    assign __emu_dt_req = nxt_time - emu_time;
    assign cke = (__emu_dt_req == __emu_dt);

    always @(posedge __emu_clk) begin
        if (__emu_rst==1'b1) begin
            emu_time <= 0;
            nxt_time <= t_int;
        end else begin
            // always increment the emulation time
            emu_time <= emu_time + __emu_dt;
            if (__emu_dt == __emu_dt_req) begin
                nxt_time <= nxt_time + t_int;
            end else begin
                nxt_time <= nxt_time;
            end
        end
    end
endmodule