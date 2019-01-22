# Load command-line arguments
set bit_file [lindex $argv 0]
set ltx_file [lindex $argv 1]
set device_name [lindex $argv 2]
set vio_name [lindex $argv 3]
set ila_name [lindex $argv 4]
set output [lindex $argv 5] 
set probe_file [lindex $argv 6]
set ila_reset [lindex $argv 7]
set vio_reset [lindex $argv 8]

# Define procedure for setting the reset VIO to "0" or "1"
proc assign_reset {rst_hw_probe value} {
    startgroup
    set_property OUTPUT_VALUE $value $rst_hw_probe
    commit_hw_vio $rst_hw_probe
    endgroup
}

# Define procedure for toggling the reset VIO
proc toggle_reset {rst_hw_probe} {
    assign_reset $rst_hw_probe 1
    assign_reset $rst_hw_probe 0
}

# Connect to hardware
open_hw
catch {disconnect_hw_server}
connect_hw_server
open_hw_target

# Configure files to be programmed
set my_hw_device [get_hw_devices $device_name]
set_property PROGRAM.FILE $bit_file $my_hw_device
set_property PROBES.FILE $ltx_file $my_hw_device
set_property FULL_PROBES.FILE $ltx_file $my_hw_device

# Program the device
current_hw_device $my_hw_device
program_hw_devices $my_hw_device
refresh_hw_device $my_hw_device

# ILA setup
set my_hw_ila [get_hw_ilas -of_objects $my_hw_device -filter CELL_NAME=~"$ila_name"]
display_hw_ila_data [get_hw_ila_data hw_ila_data_1 -of_objects $my_hw_ila]

# VIO setup
set my_hw_vio [get_hw_vios -of_objects $my_hw_device -filter CELL_NAME=~"$vio_name"]
set rst_hw_probe [get_hw_probes $vio_reset -of_objects $my_hw_vio]

# Trigger setup
set_property CONTROL.TRIGGER_POSITION 0 $my_hw_ila
set_property TRIGGER_COMPARE_VALUE eq1'bF [get_hw_probes $ila_reset -of_objects $my_hw_ila]

# Radix setup
# TODO: make this more flexible
set_property DISPLAY_RADIX SIGNED [get_hw_probes tb_i/v_out_probe]

# Toggle the reset VIO once to put it in a known state
toggle_reset $rst_hw_probe

# Arm the ILA trigger
run_hw_ila $my_hw_ila

# Toggle reset to cause emulation to run
toggle_reset $rst_hw_probe

# Get data from the ILA
wait_on_hw_ila $my_hw_ila
display_hw_ila_data [upload_hw_ila_data $my_hw_ila]

# Write ILA data to a file
write_hw_ila_data -csv_file -force $output hw_ila_data_1