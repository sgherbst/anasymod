from anasymod.enums import FPGASimCtrl

class FPGA_Board():
    board_part = None
    dbg_hub_clk_freq = 100e6
    uart_vid = None
    uart_pid = None
    uart_suffix = None
    is_ultrascale = False

class PYNQ_Z1(FPGA_Board):
    """
    Container to store PYNQ_Z1 FPGA board specific properties.
    """
    clk_pin = ['H16']
    clk_io = 'LVCMOS33'
    clk_freq = 125e6
    board_part = 'www.digilentinc.com:pynq-z1:part0:1.0'
    full_part_name = 'xc7z020clg400-1'
    short_part_name = 'xc7z020'
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_vid = 1027
    uart_pid = 24592
    uart_suffix = '.1'  # needed since this board has two com ports under the same VID/PID

class ARTY_A7(FPGA_Board):
    """
    Container to store ARTY_A7 FPGA board specific properties.
    """
    clk_pin = ['E3']
    clk_io = 'LVCMOS33'
    clk_freq = 100e6
    full_part_name = 'xc7a35ticsg324-1L'
    short_part_name = 'xc7a35'
    fpga_sim_ctrl = [FPGASimCtrl.VIVADO_VIO]

class ARTY_200T_CUSTOM_LIDAR(FPGA_Board):
    """
    Container to store ARTY_200T_CUSTOM_LIDAR FPGA board specific properties; this is a custom board specifically for
    the Lidar Project.
    """
    clk_pin = ['H4', 'G4']
    clk_io = 'DIFF_SSTL15'
    clk_freq = 50e6
    full_part_name = 'xc7a200tfbg484-2L'
    short_part_name = 'xc7a200'
    fpga_sim_ctrl = [FPGASimCtrl.VIVADO_VIO]

class TE0720(FPGA_Board):
    """
    Container to store PYNQ_Z1 FPGA board specific properties.
    """
    clk_pin = ['F7']
    clk_io = 'LVCMOS33'
    clk_freq = 33.333333e6
    full_part_name = 'xc7z020clg484-1'
    short_part_name = 'xc7z020'
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]

class VC707(FPGA_Board):
    """
    Container to store VC707 FPGA board specific properties.
    """
    clk_pin = ['E19', 'E18']
    clk_io = 'LVDS'
    clk_freq = 200e6
    full_part_name = 'XC7VX485T-2FFG1761C'
    short_part_name = 'XC7VX485T'
    fpga_sim_ctrl = [FPGASimCtrl.VIVADO_VIO]

class ZC702(FPGA_Board):
    """
    Container to store ZC702 FPGA board specific properties.
    """
    clk_pin = ['D18', 'C19']
    clk_io = 'LVDS_25'
    clk_freq = 200e6
    board_part = 'xilinx.com:zc702:part0:1.4'
    full_part_name = 'xc7z020clg484-1'
    short_part_name = 'xc7z020'
    fpga_sim_ctrl = [FPGASimCtrl.VIVADO_VIO]
    uart_vid = 4292
    uart_pid = 60000

class ULTRA96(FPGA_Board):
    """
    Container to store ULTRA96 FPGA board specific properties.
    """
    clk_pin = ['L19', 'L20']
    clk_io = 'LVDS'
    clk_freq = 26e6
    full_part_name = 'xczu3eg-sbva484-???'
    short_part_name = 'xczu3eg'
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]

class ZC706(FPGA_Board):
    """
    Container to store ZC706 FPGA board specific properties.
    """
    clk_pin = ['H9', 'G9']
    clk_io = 'LVDS'
    clk_freq = 200e6
    board_part = 'xilinx.com:zc706:part0:1.4'
    full_part_name = 'xc7z045ffg900-2'
    short_part_name = 'xc7z045'
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_vid = 4292
    uart_pid = 60000

class ZCU106(FPGA_Board):
    """
    Container to store ZCU106 FPGA board specific properties.
    """
    clk_pin = ['H9', 'G9']
    clk_io = 'LVDS'
    clk_freq = 125e6
    board_part = 'xilinx.com:zcu106:part0:2.5'
    full_part_name = 'xczu7ev-ffvc1156-2-e'
    short_part_name = 'xczu7ev'
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_vid = 4292
    uart_pid = 60000
    is_ultrascale = True
