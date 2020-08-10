module ctrl_anasymod (
    input wire logic [1:0] emu_ctrl_mode,
    input wire logic [((`TIME_WIDTH)-1):0] emu_ctrl_data,
    input wire logic [((`TIME_WIDTH)-1):0] emu_time,
    input wire logic [((`DEC_WIDTH)-1):0] emu_dec_thr,
    input wire logic emu_clk,
    input wire logic emu_rst,
    output wire logic [((`DT_WIDTH)-1):0] dt_req_stall,
    output wire logic emu_dec_cmp
);
    // comparison
    logic [((`DEC_WIDTH)-1):0] emu_dec_cnt;
    logic [((`DT_WIDTH)-1):0] emu_dt_req;
    (* dont_touch = "true" *)logic [((`TIME_WIDTH)-1):0] emu_time_s;
    logic emu_stalled, emu_sample;
    assign emu_time_s = emu_time;

    //assign emu_sample = (emu_dec_cnt == emu_dec_thr);
    //assign emu_stalled = !(emu_dt_req == 0);
    //assign emu_dec_cmp = emu_sample;
    
    assign emu_sample = (emu_dec_cnt == emu_dec_thr);
    assign emu_dec_cmp = (emu_dt_req == 0) ? 0 : emu_sample;

    // update count
    always @(posedge emu_clk) begin
        if (emu_rst == 1'b1) begin
            emu_dec_cnt <= 0;
        end else if (emu_sample == 1'b1) begin
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
            2'b00:      emu_dt_req = '1;
            2'b01:      emu_dt_req = 0;
            2'b10:      emu_dt_req =
                            ((emu_ctrl_data >= emu_time_s) ?
                                (((emu_ctrl_data - emu_time_s) <= emu_dt_max) ?
                                    (emu_ctrl_data - emu_time_s) :
                                    emu_dt_max
                                ) :
                                0
                            );
            //begin
                            //if (emu_ctrl_data >= emu_time) begin
                            //    emu_dt_req = (emu_ctrl_data - emu_time_s);
                            //end else begin
                            //    emu_dt_req = '0;
                            //end  
                        //end
                  
                
            2'b11:      emu_dt_req = (emu_ctrl_data <= emu_dt_max) ? emu_ctrl_data : emu_dt_max;
            default:    emu_dt_req = '1;
        endcase
    end
    
    assign dt_req_stall = emu_dt_req ;
endmodule