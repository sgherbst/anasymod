module osc_model_anasymod (
    input wire logic emu_clk,
    input wire logic emu_rst,
    input wire logic [((`DT_WIDTH)-1):0] emu_dt,
    output wire logic [((`DT_WIDTH)-1):0] emu_dt_req,
    output wire logic cke
);

    // Compute amount of time clock should be low vs. high;
    localparam longint t_int = (`EMU_DT)/(`DT_SCALE);

    // main logic
    // note that it is only necessary to save the emulation time up
    // to `DT_WIDTH, due to the properties of modular arithmetic

    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_time = 0;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] nxt_time = 0;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_dt_s;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] emu_dt_req_s;

    assign emu_dt_s = emu_dt;
    assign emu_dt_req_s = nxt_time - emu_time;
    assign emu_dt_req = emu_dt_req_s;
    assign cke = (emu_dt_req == emu_dt_s);

    always @(posedge emu_clk) begin
        if (emu_rst==1'b1) begin
            emu_time <= 0;
            nxt_time <= t_int;
        end else begin
            // always increment the emulation time
            emu_time <= emu_time + emu_dt_s;
            if (emu_dt_s == emu_dt_req_s) begin
                nxt_time <= nxt_time + t_int;
            end else begin
                nxt_time <= nxt_time;
            end
        end
    end
endmodule