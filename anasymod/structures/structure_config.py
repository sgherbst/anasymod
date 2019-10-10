import os

from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig
from anasymod.config import EmuConfig
from anasymod.structures.port_base import PortIN, PortOUT, Port
from anasymod.structures.signal_base import Signal
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput

#ToDo: wrap vios into classes to better cope with parameters such as width, name, abs_path, portobj, sigobj, ...

class StructureConfig():
    """
    In this configuration, all the toplevel information about the generated toplevel is included.
    It will be used for generation of the target specific top-level, as well as attached wrappers.

    There is also a specific interface to flow plugins that allows modification due to some needs
    from the plugin side, e.g. additional clks, resets, ios to the host application or resources on the FPGA board.
    """
    def __init__(self, prj_cfg: EmuConfig):
        # Internal variables
        self.i_addr_counter = 0
        self.o_addr_counter = 0

        self._ctrl_iofile_path = os.path.join(prj_cfg.root, 'ctrl_io.config')

        self.cfg = Config(prj_cfg=prj_cfg)
        self.cfg.update_config()

        #########################################################
        # VIO interfaces
        #########################################################

        # Add DigitalCtrlInput for reset
        self.reset_ctrl = DigitalCtrlInput(abspath=None, name='emu_rst', width=1)
        self.reset_ctrl.i_addr = self._assign_i_addr()

        # Add DigitalCtrlInput for control signal 'emu_dec_thr' to manage decimation ration for capturing probe samples
        self.dec_thr_ctrl = DigitalCtrlInput(abspath=None, name='emu_dec_thr', width=int(prj_cfg.cfg.dec_bits))
        self.dec_thr_ctrl.i_addr = self._assign_i_addr()

        # CtrlIOs
        self.digital_ctrl_inputs = []
        self.digital_ctrl_outputs = []
        self.analog_ctrl_inputs = []
        self.analog_ctrl_outputs = []

        self.digital_ctrl_inputs = [DigitalCtrlInput(name='hufflpu', width=31, abspath='',init_value=41)]
        self.digital_ctrl_outputs = [DigitalCtrlOutput(name='banii', width=1, abspath='')]
        self.analog_ctrl_inputs = [AnalogCtrlInput(name='mimpfl', init_value=42.0, abspath='', range=500)]
        self.analog_ctrl_outputs = [AnalogCtrlOutput(name='primpf', range=250, abspath='')]

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

    def _assign_i_addr(self):
        """
        Function to assign an input address to an Input object.
        """
        curr_addr = self.i_addr_counter
        self.i_addr_counter +=1
        return curr_addr

    def _assign_o_addr(self):
        """
        Function to assign an input address to an Input object.
        """
        curr_addr = self.o_addr_counter
        self.o_addr_counter +=1
        return curr_addr

    def _read_iofile(self):
        """
        Read all lines from iofile and call parse function to populate ctrl_ios container.
        """
        if os.path.isfile(self._ctrl_iofile_path):
            with open(self._ctrl_iofile_path, "r") as f:
                ctrlios = f.readlines()
            self._parse_iofile(ctrlios=ctrlios)
        else:
            print(f"No ctrl_io file existing, no additional control IOs will be available for this simulation.")

    def _parse_iofile(self, ctrlios: list):
        """
        Read all lines from ctrl io file and store IO objects in CtrlIO container while adding access addresses to
        each IO object.
        :param ctrlios: Lines extracted to ctrl_io file
        """

        for k, line in enumerate(ctrlios):
            line = line.strip()

            if line.startswith('#'):
                # skip comments
                continue

            if line:
                try:
                    line = eval(line)
                    if isinstance(line, DigitalCtrlInput):
                        line.i_addr = self._assign_i_addr()
                        self.digital_ctrl_inputs.append(line)
                    elif isinstance(line, DigitalCtrlOutput):
                        line.o_addr = self._assign_o_addr()
                        self.digital_ctrl_outputs.append(line)
                    elif isinstance(line, AnalogCtrlInput):
                        line.i_addr = self._assign_i_addr()
                        self.analog_ctrl_inputs.append(line)
                    elif isinstance(line, AnalogCtrlOutput):
                        line.o_addr = self._assign_o_addr()
                        self.analog_ctrl_outputs.append(line)
                    else:
                        raise Exception(f"Line {k+1} of ctrl_io file: {self._ctrl_iofile_path} does not fit do a specified source or config type")
                except:
                    raise Exception(f"Line {k+1} of config file: {self._ctrl_iofile_path} could not be processed properely")


class CtrlIOs():
    """
    Container to store all Control IOs for associated Control Interface.
    """
    def __init__(self):
        self.digital_inputs = []
        self.digital_outputs = []
        self.analog_inputs = []
        self.analog_outputs = []

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
        #self.vio_i_num = 0
        #self.vio_i_widths = []
        #self.vio_i_abspaths = []

        #self.vio_o_num = 0
        #self.vio_o_widths = []
        #self.vio_o_abspaths = []

        self.rst_clkcycles = 1

        #########################################################
        # CLK manager settings
        #########################################################

        # add gated clk_outs
        self.clk_o_num = 0