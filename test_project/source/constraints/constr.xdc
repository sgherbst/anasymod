##########################
# 200 MHz system clock
##########################

#set_property IOSTANDARD LVDS [get_ports SYSCLK_P]
#set_property PACKAGE_PIN H9 [get_ports SYSCLK_P]
#set_property PACKAGE_PIN G9 [get_ports SYSCLK_N]
#set_property IOSTANDARD LVDS [get_ports SYSCLK_N]
#create_clock -period 5.000 -name SYSCLK_P -waveform {0.000 2.500} -add [get_ports SYSCLK_P]

##########################
# 125 MHz system clock Pynq Z1
##########################


set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports SYSCLK]
create_clock -period 8.000 -name SYSCLK_P -waveform {0.000 4.000} -add [get_ports SYSCLK]

##########################
# LED outputs
##########################

#set_property -dict { PACKAGE_PIN R14 IOSTANDARD LVCMOS33 } [get_ports { GPIO_LED_LEFT }]
#set_property -dict { PACKAGE_PIN P14 IOSTANDARD LVCMOS33 } [get_ports { GPIO_LED_CENTER }]
#set_property -dict { PACKAGE_PIN N16 IOSTANDARD LVCMOS33 } [get_ports { GPIO_LED_RIGHT }]
#set_property -dict { PACKAGE_PIN M14 IOSTANDARD LVCMOS33 } [get_ports { GPIO_LED_0 }]

#set_property PACKAGE_PIN Y21 [get_ports GPIO_LED_LEFT]
#set_property IOSTANDARD LVCMOS25 [get_ports GPIO_LED_LEFT]

#set_property PACKAGE_PIN G2 [get_ports GPIO_LED_CENTER]
#set_property IOSTANDARD LVCMOS15 [get_ports GPIO_LED_CENTER]

#set_property PACKAGE_PIN W21 [get_ports GPIO_LED_RIGHT]
#set_property IOSTANDARD LVCMOS25 [get_ports GPIO_LED_RIGHT]

#set_property PACKAGE_PIN A17 [get_ports GPIO_LED_0]
#set_property IOSTANDARD LVCMOS15 [get_ports GPIO_LED_0]

create_debug_core u_ila_0 ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila_0]
set_property ALL_PROBE_SAME_MU_CNT 1 [get_debug_cores u_ila_0]
set_property C_ADV_TRIGGER false [get_debug_cores u_ila_0]
set_property C_DATA_DEPTH 1024 [get_debug_cores u_ila_0]
set_property C_EN_STRG_QUAL false [get_debug_cores u_ila_0]
set_property C_INPUT_PIPE_STAGES 0 [get_debug_cores u_ila_0]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_0]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila_0]
set_property port_width 1 [get_debug_ports u_ila_0/clk]
connect_debug_port u_ila_0/clk [get_nets [list clkgen_i/clk_wiz_0_i/inst/clk_out1]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe0]
set_property port_width 25 [get_debug_ports u_ila_0/probe0]
connect_debug_port u_ila_0/probe0 [get_nets [list {tb_i/v_out_probe[0]} {tb_i/v_out_probe[1]} {tb_i/v_out_probe[2]} {tb_i/v_out_probe[3]} {tb_i/v_out_probe[4]} {tb_i/v_out_probe[5]} {tb_i/v_out_probe[6]} {tb_i/v_out_probe[7]} {tb_i/v_out_probe[8]} {tb_i/v_out_probe[9]} {tb_i/v_out_probe[10]} {tb_i/v_out_probe[11]} {tb_i/v_out_probe[12]} {tb_i/v_out_probe[13]} {tb_i/v_out_probe[14]} {tb_i/v_out_probe[15]} {tb_i/v_out_probe[16]} {tb_i/v_out_probe[17]} {tb_i/v_out_probe[18]} {tb_i/v_out_probe[19]} {tb_i/v_out_probe[20]} {tb_i/v_out_probe[21]} {tb_i/v_out_probe[22]} {tb_i/v_out_probe[23]} {tb_i/v_out_probe[24]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe1]
set_property port_width 1 [get_debug_ports u_ila_0/probe1]
connect_debug_port u_ila_0/probe1 [get_nets [list rst]]
set_property C_CLK_INPUT_FREQ_HZ 300000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER false [get_debug_cores dbg_hub]
set_property C_USER_SCAN_CHAIN 1 [get_debug_cores dbg_hub]
connect_debug_port dbg_hub/clk [get_nets clk]
