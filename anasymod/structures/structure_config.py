from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig
from anasymod.config import EmuConfig
from anasymod.structures.port_base import PortIN, PortOUT, Port

class StructureConfig():
    """
    In this configuration, all the toplevel information about the generated toplevel is included.
    It will be used for generation of the target specific top-level, as well as attached wrappers.

    There is also a specific interface to flow plugins that allows modification due to some needs
    from the plugin side, e.g. additional clks, resets, ios to the host application or resources on the FPGA board.
    """
    def __init__(self, prj_cfg: EmuConfig):
        self.cfg = Config(prj_cfg=prj_cfg)

        #########################################################
        # VIO interfaces
        #########################################################

        # vio inputs
        self.vio_i_names = [f"vio_i_{i}" for i in range(self.cfg.vio_i_num)]
        self.vio_i_ports = [Port(name=self.vio_i_names[i], width=self.cfg.vio_i_widths[i]) for i in range(self.cfg.vio_i_num)]

        # vio reset
        self.vio_r_num = 1
        self.vio_r_widths = [1]
        self.vio_r_names = ['emu_rst']
        self.vio_r_ports = [Port(name=self.vio_r_names[i], width=self.vio_r_widths[i]) for i in range(self.vio_r_num)]

        # vio sim constrol
        self.vio_s_num = 1
        self.vio_s_widths = [int(prj_cfg.cfg.dec_bits)]
        self.vio_s_names = ['emu_dec_thr']
        self.vio_s_ports = [Port(name=self.vio_s_names[i], width=self.vio_s_widths[i]) for i in range(self.vio_s_num)]

        # names for reset and decimation_threshold are fixed
        self.vio_o_names = ([f"vio_o_{i}" for i in range(self.cfg.vio_o_num)])
        self.vio_o_ports = [Port(name=self.vio_o_names[i], width=self.cfg.vio_o_widths[i]) for i in range(self.cfg.vio_o_num)]

        #########################################################
        # CLK manager interfaces
        #########################################################

        # add clk_in
        self.clk_i_num = len(prj_cfg.board.clk_pin)
        self.clk_i_widths = self.clk_i_num * [1]

        # clk_in names cannot be changed
        if self.clk_i_num == 2:
            self.clk_i_names = ['clk_in1_p', 'clk_in1_n']
        elif self.clk_i_num == 1:
            self.clk_i_names = ['clk_in1']
        else:
            raise ValueError(
                f"Wrong number of pins for boards param 'clk_pin', expecting 1 or 2, provided:{self.clk_i_num}")

        self.clk_i_ports = [Port(name=self.clk_i_names[i], width=self.clk_i_widths[i]) for i in range(self.clk_i_num)]

        # add master clk_out
        self.clk_m_num = 1
        self.clk_m_widths = self.clk_m_num * [1]
        self.clk_m_names = ['emu_clk']
        self.clk_m_ports = [Port(name=self.clk_m_names[i], width=self.clk_m_widths[i]) for i in range(self.clk_m_num)]

        # add debug clk_out
        self.clk_d_num = 1
        self.clk_d_widths = self.clk_d_num * [1]
        self.clk_d_names = ['dbg_hub_clk']
        self.clk_d_ports = [Port(name=self.clk_d_names[i], width=self.clk_d_widths[i]) for i in range(self.clk_d_num)]

        # add custom clk_outs
        self.clk_o_widths = self.cfg.clk_o_num * [1]
        self.clk_o_names = [f"clk_o_{i}" for i in range(self.cfg.clk_o_num)]
        self.clk_o_ports = [Port(name=self.clk_o_names[i], width=self.clk_o_widths[i]) for i in range(self.cfg.clk_o_num)]

        # add enable ports for each gated clk
        self.clk_g_num = self.cfg.clk_o_num
        self.clk_g_widths = self.clk_g_num * [1]
        self.clk_g_names = [f"clk_o_{i}_ce" for i in range(self.clk_g_num)]
        self.clk_g_ports = [Port(name=self.clk_g_names[i], width=self.clk_g_widths[i]) for i in range(self.clk_g_num)]

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, prj_cfg: EmuConfig):
        super().__init__(cfg_file=prj_cfg.cfg_file, section=ConfigSections.STRUCTURE)
        self.prj_cfg = prj_cfg

        #########################################################
        # VIO settings
        #########################################################
        self.vio_i_num = 0
        self.vio_i_widths = []

        self.vio_o_num = 0
        self.vio_o_widths = []

        #########################################################
        # CLK manager settings
        #########################################################

        # add gated clk_outs
        self.clk_o_num = 0