from anasymod.enums import FPGASimCtrl

class FPGA_Board():
    board_part = None
    dbg_hub_clk_freq = 100e6
    uart_vid = None
    uart_pid = None
    uart_suffix = None
    is_ultrascale = False
    no_rev_check = False

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
    bram = 4.9e6
    dbg_hub_clk_freq = 100e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [1027]
    uart_zynq_pid = [24592]
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
    bram = 1.8e6
    dbg_hub_clk_freq = 100e6
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
    bram = 13e6
    dbg_hub_clk_freq = 100e6
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
    bram = 4.9e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [1027] # might need adjustment
    uart_zynq_pid = [24592] # might need adjustment

class VC707(FPGA_Board):
    """
    Container to store VC707 FPGA board specific properties.
    """
    clk_pin = ['E19', 'E18']
    clk_io = 'LVDS'
    clk_freq = 200e6
    full_part_name = 'XC7VX485T-2FFG1761C'
    short_part_name = 'XC7VX485T'
    bram = 37e6
    dbg_hub_clk_freq = 100e6
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
    bram = 4.9e6
    dbg_hub_clk_freq = 100e6
    fpga_sim_ctrl = [FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [4292]
    uart_zynq_pid = [60000]

class ULTRA96(FPGA_Board):
    """
    Container to store ULTRA96 FPGA board specific properties.
    """
    clk_pin = ['L19', 'L20']
    clk_io = 'LVDS'
    clk_freq = 26e6
    full_part_name = 'xczu3eg-sbva484-???'
    short_part_name = 'xczu3eg'
    bram = 7.6e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [1027] # might need adjustment
    uart_zynq_pid = [24592] # might need adjustment

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
    bram = 19.2e6
    dbg_hub_clk_freq = 100e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [4292]
    uart_zynq_pid = [60000]

class ZCU102(FPGA_Board):
    """
    Container to store ZCU102 FPGA board specific properties.
    """
    clk_pin = ['AL8', 'AL7']
    clk_io = 'DIFF_SSTL12'
    clk_freq = 300e6
    board_part = 'xilinx.com:zcu102:part0:3.2'
    full_part_name = 'xczu9eg-ffvb1156-2-e'
    short_part_name = 'xczu9'
    bram = 32.1e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [4292]
    uart_zynq_pid = [60017]
    uart_suffix = '.0'  # needed since this board has four com ports under the same VID/PID
    is_ultrascale = True
    no_rev_check = True  # needed in case the FPGA is an engineering sample

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
    bram = 11.0e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [4292]
    uart_zynq_pid = [60017]
    uart_suffix = '.0'  # needed since this board has four com ports under the same VID/PID
    is_ultrascale = True

class ZCU111(FPGA_Board):
    """
    Container to store ZCU111 FPGA board specific properties.
    """
    clk_pin = ['AL17', 'AM17']  # from Table 3-17 in the user guide
    clk_io = 'LVDS'
    clk_freq = 125e6
    board_part = 'xilinx.com:zcu111:part0:1.2'
    full_part_name = 'xczu28dr-ffvg1517-2-e'
    short_part_name = 'xczu28'
    bram = 38e6
    fpga_sim_ctrl = [FPGASimCtrl.UART_ZYNQ, FPGASimCtrl.VIVADO_VIO]
    uart_zynq_vid = [1027]  # FT4232HL from Table 3-8 in the user guide
    uart_zynq_pid = [24593]  # FT4232HL from Table 3-8 in the user guide
    uart_suffix = '.1'  # needed since this board has four com ports under the same VID/PID
    is_ultrascale = True
    no_rev_check = True  # needed in case the FPGA is an engineering sample
