module osc_model_anasymod (
    output wire logic clk,
    output reg rst
);
    // inputs from the top level
    (* dont_touch = "true" *) logic __emu_clk;
    (* dont_touch = "true" *) logic __emu_rst;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt;
    (* dont_touch = "true" *) logic __emu_clk_i;

    // outputs to the top level
    (* dont_touch = "true" *) logic __emu_clk_val;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt_req;

    // assign output clock (note that a module output pin cannot be directly
    // written hierachically)
    assign clk = __emu_clk_i;

    // Compute amount of time clock should be low vs. high;
    localparam longint t_per_int = (`EMU_DT)/(`DT_SCALE);
    localparam longint t_hi_int = t_per_int / 2;
    localparam longint t_lo_int = t_per_int - t_hi_int;

    // main logic
    // note that it is only necessary to save the emulation time up
    // to `DT_WIDTH, due to the properties of modular arithmetic

    logic [((`DT_WIDTH)-1):0] emu_time;
    logic [((`DT_WIDTH)-1):0] next_edge_time;

    assign __emu_dt_req = next_edge_time - emu_time;

    always @(posedge __emu_clk) begin
        if (__emu_rst==1'b1) begin
            emu_time <= 0;
            next_edge_time <= 0;
            __emu_clk_val <= 0;
            rst <= 1;
        end else begin
            // always increment the emulation time
            emu_time <= emu_time + __emu_dt;
            if (__emu_dt == __emu_dt_req) begin
                // if the timestep request was granted, update the next edge time...
                if (__emu_clk_val == 0) begin
                    // i.e., clock was low and is going to be high
                    next_edge_time <= next_edge_time + t_hi_int;
                    rst <= rst;
                end else begin
                    // i.e., clock was high and is going to be low
                    next_edge_time <= next_edge_time + t_lo_int;
                    rst <= 0;
                end
                // ... and invert the clock value
                __emu_clk_val <= ~__emu_clk_val;
            end else begin
                // otherwise maintain the next edge time and clock value
                next_edge_time <= next_edge_time;
                __emu_clk_val <= __emu_clk_val;
                rst <= rst;
            end
        end
    end
endmodule