# program device
set bit_file {build/project/project.runs/impl_1/top.bit}
set probe_file {build/project/project.runs/impl_1/top.ltx}

open_hw
connect_hw_server
open_hw_target

set hw_device [get_hw_devices *xc7*]
current_hw_device $hw_device
refresh_hw_device $hw_device

set_property PROGRAM.FILE $bit_file $hw_device
set_property PROBES.FILE $probe_file $hw_device
set_property FULL_PROBES.FILE $probe_file $hw_device

program_hw_devices $hw_device
refresh_hw_device $hw_device

# configure VIO for low latency
# since there is no refresh, writing the VIO requires commit_hw_vio 
# and reading the VIO requires refresh_hw_vio
set vio_0_i [get_hw_vios -of_objects $hw_device -filter {CELL_NAME=~"sim_ctrl_gen_i/vio_0_i"}]
set_property CORE_REFRESH_RATE_MS 0 $vio_0_i

# set aliases to VIO probes
set emu_rst [get_hw_probes "sim_ctrl_gen_i/emu_rst" -of_objects $vio_0_i]
set go_vio [get_hw_probes "sim_ctrl_gen_i/go_vio" -of_objects $vio_0_i]
set rst_vio [get_hw_probes "sim_ctrl_gen_i/rst_vio" -of_objects $vio_0_i]
set v_out_vio [get_hw_probes "sim_ctrl_gen_i/v_out_vio" -of_objects $vio_0_i]
set v_in_vio [get_hw_probes "sim_ctrl_gen_i/v_in_vio" -of_objects $vio_0_i]

# configure VIO radix
set_property INPUT_VALUE_RADIX SIGNED $v_out_vio
set_property OUTPUT_VALUE_RADIX SIGNED $v_in_vio
