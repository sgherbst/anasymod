class ConfigSections:
    """
    Container including enums for sections that can be used in config file.
    """
    TARGET = "TARGET"
    FPGA_BOARD = "FPGA_BOARD"
    TOOL = "TOOL"
    PLUGIN = "PLUGIN"
    PROJECT = "PROJECT"
    STRUCTURE = "STRUCTURE"
    FPGASIM = "FPGASIM"

class BoardNames:
    """
    Container including enums for all supported boards.

    Currently supported boards are:
    PYNQ_Z1
    ARTY_A7
    VC707
    ZC702
    ULTRA96
    TE0720
    """
    PYNQ_Z1 = 'PYNQ_Z1'
    ARTY_A7 = 'ARTY_A7'
    VC707 = 'VC707'
    ZC702 = 'ZC702'
    ULTRA96 = 'ULTRA96'
    TE0720 = 'TE0720'

class PortDir:
    """
    Container including enums for all supported port directions.
    """
    IN = "input"
    OUT = "output"
    INOUT = "inout"

class CtrlOps:
    """
    Container including enums for all supported control operations for controlling the FPGA.
    """
    WRITE_PARAMETER = 0
    READ_PARAMETER = 1

class FPGASimCtrl:
    """
    Container including enums for all supported FPGA control interfaces.
    """
    UART_ZYNQ = 'uart_zynq'
    VIVADO_VIO = 'vivado_vio'
