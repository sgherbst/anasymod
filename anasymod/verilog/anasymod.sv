task wait_emu_reset(input integer dummy=0);
    @(negedge top.emu_rst);
endtask

task wait_emu_cycle(input integer n=1);
    repeat (n) @(posedge top.emu_clk);
    #((0.1/(`EMU_CLK_FREQ))*1s);
endtask

function real get_emu_time(input integer dummy=0);
    get_emu_time = top.emu_time * (`DT_SCALE);
endfunction

task stall_emu(input integer dummy=0);
    force top.sim_ctrl_gen_i.emu_ctrl_mode_state = 1;
endtask

task run_emu(input integer dummy=0);
    force top.sim_ctrl_gen_i.emu_ctrl_mode_state = 0;
endtask

task sleep_emu(input real t);
    longint tgt;
    tgt = top.emu_time + longint'(t/(`DT_SCALE));

    force top.sim_ctrl_gen_i.emu_ctrl_data_state = tgt;
    force top.sim_ctrl_gen_i.emu_ctrl_mode_state = 2;

    wait_emu_cycle();
    while (top.emu_dt != 0) begin
        wait_emu_cycle();
    end
endtask