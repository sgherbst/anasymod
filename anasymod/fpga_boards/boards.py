

class PYNQ_Z1():
    """
    Container to store PYNQ_Z1 FPGA board specific properties.
    """
    clk_pin = ['H16']
    clk_io = 'LVCMOS33'
    clk_freq = 125e6
    full_part_name = 'xc7z020clg400-1'
    short_part_name = 'xc7z020'
    dbg_hub_clk_freq = 100e6

class VC707():
    """
    Container to store VC707 FPGA board specific properties.
    """
    clk_pin = ['E19', 'E18']
    clk_io = 'LVDS'
    clk_freq = 200e6
    full_part_name = 'XC7VX485T-2FFG1761C'
    short_part_name = 'XC7VX485T'
    dbg_hub_clk_freq = 100e6