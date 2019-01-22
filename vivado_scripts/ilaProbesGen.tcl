#command line arguments
#set $bit_file = C:\Users\saravshi\sv_real\sv_real.runs\impl_1\top.bit
#set $ltx_file = C:\Users\saravshi\sv_real\sv_real.runs\impl_1\top.ltx
set bit_file [lindex $argv 0]
set ltx_file [lindex $argv 1]
set device_name [lindex $argv 2]
set vio_name [lindex $argv 3]
set ila_name [lindex $argv 4]
set output [lindex $argv 5] 
set probe_file [lindex $argv 6]
set reset [lindex $argv 7]
#configure hw manager for emulation
#open_hw

catch {disconnect_hw_server}
connect_hw_server 

#current_hw_target [get_hw_targets *]
open_hw_target

set_property PROGRAM.FILE $bit_file [get_hw_devices $device_name]

set_property PROBES.FILE $ltx_file [get_hw_devices $device_name]
set_property FULL_PROBES.FILE $ltx_file [get_hw_devices $device_name]
current_hw_device [get_hw_devices $device_name]
program_hw_devices  [get_hw_devices $device_name] 
refresh_hw_device [lindex [get_hw_devices $device_name] 0]


#program the fpga


#ILA setup
display_hw_ila_data [ get_hw_ila_data hw_ila_data_1 -of_objects [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]]

#display_hw_ila_data [ get_hw_ila_data hw_ila_data_1 -of_objects [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter {CELL_NAME=~"$ila_name"}]]
#read_hw_ila_data (to import previously saved data)


# Trigger setup
##############
set_property CONTROL.TRIGGER_POSITION 0 [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]

set_property TRIGGER_COMPARE_VALUE eq1'bF [get_hw_probes $reset -of_objects [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]]

#Radix setup


set f [open "$probe_file" "r"]

while {1 == 1} {
    set cnt [gets $f column]
    if {$cnt < 0} {break}
    set v_out [lindex [split $column ","] 0]
    puts $v_out
}

close $f

set_property DISPLAY_RADIX SIGNED [get_hw_probes $v_out ]


#toggle reset to setup trigger

proc assign_reset {value device_name vio_name} {
startgroup
set_property OUTPUT_VALUE $value [get_hw_probes rst -of_objects [get_hw_vios -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$vio_name"]]
commit_hw_vio [get_hw_probes rst -of_objects [get_hw_vios -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$vio_name"]]
endgroup
 }
assign_reset 1 $device_name $vio_name
assign_reset 0 $device_name $vio_name



puts [get_hw_devices $device_name]
#set trigger
run_hw_ila [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]


assign_reset 1  $device_name $vio_name
assign_reset 0  $device_name $vio_name


#get the data
puts [get_hw_devices $device_name]
wait_on_hw_ila [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]
display_hw_ila_data [upload_hw_ila_data [get_hw_ilas -of_objects [get_hw_devices $device_name] -filter CELL_NAME=~"$ila_name"]]

# make the directory

write_hw_ila_data -csv_file -force $output hw_ila_data_1

		
	


