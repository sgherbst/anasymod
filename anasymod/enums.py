class ConfigSections:
    """
    Container including enums for sections that can be used in config file.
    """
    PROJECT = "PROJECT"
    CPU_TARGET = "CPU_TARGET"
    FPGA_TARGET = "FPGA_TARGET"
    PLUGIN = "PLUGIN"
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
    ARTY_200T_CUSTOM_LIDAR = 'ARTY_200T_CUSTOM_LIDAR'


class PortDir:
    """
    Container including enums for all supported port directions.
    """
    IN = "input"
    OUT = "output"
    INOUT = "inout"


class TraceUnitOperators:
    """
    Container including enums for all valid operators that can be used for setting up the trace unit
    """
    EQUAL = 'eq'
    NOTEQUAL = 'neq'
    GREATER = 'gt'
    GREATEREQUAL = 'gteq'
    LESSER = 'lt'
    LESSEREQUAL = 'lteq'


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
    UART_ZYNQ = 'UART_ZYNQ'
    VIVADO_VIO = 'VIVADO_VIO'


class ResultFileTypes:
    """
    Container including enums for all supported data formats to store simulation/emulation results.
    """
    VCD = 'vcd'
    CSV = 'csv'