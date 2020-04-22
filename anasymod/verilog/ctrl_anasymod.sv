module ctrl_anasymod (
    input wire logic [3:0] emu_ctrl_mode,
    input wire logic [((`TIME_WIDTH)-1):0] emu_ctrl_data,
    input wire logic [((`TIME_WIDTH)-1):0] emu_time,
    input wire logic [((`DEC_WIDTH)-1):0] emu_dec_thr,
    output wire logic emu_dec_cmp
);
    // inputs from the top level
    (* dont_touch = "true" *) logic __emu_clk;
    (* dont_touch = "true" *) logic __emu_rst;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt;
    (* dont_touch = "true" *) logic [((`DT_WIDTH)-1):0] __emu_dt_req;

    // comparison
    logic [((`DEC_WIDTH)-1):0] emu_dec_cnt;
    assign emu_dec_cmp = (emu_dec_cnt == emu_dec_thr);

    // update count
    always @(posedge __emu_clk) begin
        if (__emu_rst == 1'b1) begin
            emu_dec_cnt <= 0;
        end else if (emu_dec_cmp == 1'b1) begin
            emu_dec_cnt <= 0;
        end else begin
            emu_dec_cnt <= emu_dec_cnt + 1;
        end
    end

    // define maximum timestep request
    logic [((`DT_WIDTH)-1):0] emu_dt_max;
    assign emu_dt_max = '1;

    // keep track of emulation time
    always @(*) begin
        case (emu_ctrl_mode)
            2'b00:      __emu_dt_req = '1;
            2'b01:      __emu_dt_req = 0;
            2'b10:      __emu_dt_req =
                ((emu_ctrl_data >= emu_time) ?
                    (((emu_ctrl_data - emu_time) <= emu_dt_max) ?
                        (emu_ctrl_data - emu_time) :
                        emu_dt_max
                    ) :
                    0
                );
            2'b11:      __emu_dt_req = (emu_ctrl_data <= emu_dt_max) ? emu_ctrl_data : emu_dt_max;
            default:    __emu_dt_req = '1;
        endcase
    end
endmodule