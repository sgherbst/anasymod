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
