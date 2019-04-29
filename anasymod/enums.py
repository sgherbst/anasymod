class ConfigSections:
    """
    Container including enums for sections that can be used in config file.
    """
    TARGET = "TARGET"
    CLK = "CLK"
    ILA = "ILA"
    VIO = "VIO"
    FPGA_BOARD = "FPGA_BOARD"
    TOOL = "TOOL"
    PLUGIN = "PLUGIN"
    PROJECT = "PROJECT"
    STRUCTURE = "STRUCTURE"

class BoardNames:
    """
    Container including enums for all supported boards.
    """
    PYNQ_Z1 = 'PYNQ_Z1'
    VC707 = 'VC707'
    ULTRA96 = 'ULTRA96'
    TE0720 = 'TE0720'

class PortDir:
    """
    Container including enums for all supported port directions.
    """
    IN = "IN"
    OUT = "OUT"
