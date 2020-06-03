from anasymod.sim_ctrl.datatypes import DigitalSignal

class TemplZynqGPIO:
    def __init__(self, ps_vlnv='xilinx.com:ip:processing_system7:5.5',
                 gpio_vlnv='xilinx.com:ip:axi_gpio:2.0', design_name='zynq_gpio'):
        # save settings
        self.design_name=design_name
        self.ps_vlnv = ps_vlnv
        self.gpio_vlnv = gpio_vlnv

        # save IO that are used by the emulator
        self.o_ctrl = DigitalSignal(name='o_ctrl', width=32, abspath=None)
        self.o_data = DigitalSignal(name='o_data', width=32, abspath=None)
        self.i_ctrl = DigitalSignal(name='i_ctrl', width=32, abspath=None)
        self.i_data = DigitalSignal(name='i_data', width=32, abspath=None)

        # generate text
        self.text = f'''
############################
# Create the block diagram #
############################

# Initialize

create_bd_design "{self.design_name}"

# Instantiate IPs

create_bd_cell -type ip -vlnv {self.ps_vlnv} processing_system7_0
create_bd_cell -type ip -vlnv {self.gpio_vlnv} axi_gpio_0
create_bd_cell -type ip -vlnv {self.gpio_vlnv} axi_gpio_1

# Configure IPs

set_property \\
    -dict [list \\
        CONFIG.C_IS_DUAL {{1}} \\
        CONFIG.C_ALL_OUTPUTS {{1}} \\
        CONFIG.C_ALL_INPUTS_2 {{1}} \\
    ] \\
    [get_bd_cells axi_gpio_0]

set_property \\
    -dict [list \\
        CONFIG.C_IS_DUAL {{1}} \\
        CONFIG.C_ALL_OUTPUTS {{1}} \\
        CONFIG.C_ALL_OUTPUTS_2 {{1}} \\
    ] \\
    [get_bd_cells axi_gpio_1]

# Create ports

create_bd_port -dir O -from 31 -to 0 o_ctrl 
create_bd_port -dir I -from 31 -to 0 o_data
create_bd_port -dir O -from 31 -to 0 i_ctrl 
create_bd_port -dir O -from 31 -to 0 i_data

# Wire up IPs

connect_bd_net \\
    [get_bd_pins processing_system7_0/FCLK_CLK0] \\
    [get_bd_pins processing_system7_0/M_AXI_GP0_ACLK]

connect_bd_net \\
    [get_bd_ports o_ctrl] \\
    [get_bd_pins axi_gpio_0/gpio_io_o]

connect_bd_net \\
    [get_bd_ports o_data] \\
    [get_bd_pins axi_gpio_0/gpio2_io_i]

connect_bd_net \\
    [get_bd_ports i_ctrl] \\
    [get_bd_pins axi_gpio_1/gpio_io_o]

connect_bd_net \\
    [get_bd_ports i_data] \\
    [get_bd_pins axi_gpio_1/gpio2_io_o]

# Apply automation    

apply_bd_automation \\
    -rule xilinx.com:bd_rule:processing_system7 \\
    -config {{ \\
        make_external "FIXED_IO, DDR" \\
        apply_board_preset "1" \\
        Master "Disable" \\
        Slave "Disable" \\
    }} \\
    [get_bd_cells processing_system7_0]

apply_bd_automation \\
    -rule xilinx.com:bd_rule:axi4 \\
    -config {{ \\
        Clk_master {{/processing_system7_0/FCLK_CLK0 (100 MHz)}} \\
        Clk_slave {{Auto}} \\
        Clk_xbar {{Auto}} \\
        Master {{/processing_system7_0/M_AXI_GP0}} \\
        Slave {{/axi_gpio_0/S_AXI}} \\
        intc_ip {{New AXI Interconnect}} \\
        master_apm {{0}}\\
    }} \\
    [get_bd_intf_pins axi_gpio_0/S_AXI]

apply_bd_automation \\
    -rule xilinx.com:bd_rule:axi4 \\
    -config {{ \\
        Clk_master {{/processing_system7_0/FCLK_CLK0 (100 MHz)}} \\
        Clk_slave {{Auto}} \\
        Clk_xbar {{Auto}} \\
        Master {{/processing_system7_0/M_AXI_GP0}} \\
        Slave {{/axi_gpio_1/S_AXI}} \\
        intc_ip {{New AXI Interconnect}} \\
        master_apm {{0}}\\
    }} \\
    [get_bd_intf_pins axi_gpio_1/S_AXI]

validate_bd_design
'''

    # save external IOs that need to be wired to the top
    EXT_IOS = [
        DigitalSignal(name='DDR_addr', width=15, abspath=None),
        DigitalSignal(name='DDR_ba', width=3, abspath=None),
        DigitalSignal(name='DDR_cas_n', width=1, abspath=None),
        DigitalSignal(name='DDR_ck_n', width=1, abspath=None),
        DigitalSignal(name='DDR_ck_p', width=1, abspath=None),
        DigitalSignal(name='DDR_cke', width=1, abspath=None),
        DigitalSignal(name='DDR_cs_n', width=1, abspath=None),
        DigitalSignal(name='DDR_dm', width=4, abspath=None),
        DigitalSignal(name='DDR_dq', width=32, abspath=None),
        DigitalSignal(name='DDR_dqs_n', width=4, abspath=None),
        DigitalSignal(name='DDR_dqs_p', width=4, abspath=None),
        DigitalSignal(name='DDR_odt', width=1, abspath=None),
        DigitalSignal(name='DDR_ras_n', width=1, abspath=None),
        DigitalSignal(name='DDR_reset_n', width=1, abspath=None),
        DigitalSignal(name='DDR_we_n', width=1, abspath=None),
        DigitalSignal(name='FIXED_IO_ddr_vrn', width=1, abspath=None),
        DigitalSignal(name='FIXED_IO_ddr_vrp', width=1, abspath=None),
        DigitalSignal(name='FIXED_IO_mio', width=54, abspath=None),
        DigitalSignal(name='FIXED_IO_ps_clk', width=1, abspath=None),
        DigitalSignal(name='FIXED_IO_ps_porb', width=1, abspath=None),
        DigitalSignal(name='FIXED_IO_ps_srstb', width=1, abspath=None)
    ]