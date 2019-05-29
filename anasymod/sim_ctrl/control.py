from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalCtrlInput, DigitalCtrlOutput, AnalogCtrlInput, AnalogCtrlOutput

import serial, os

class Control():
    def __init__(self, prj_cfg):
        # Initialize target_config
        self.cfg = Config(cfg_file=prj_cfg.cfg_file)

        # Dict container including all IO objects that are accessible via the control interface
        self.ctrl_ios = CtrlIOs()

        # Internal variables
        self.i_addr_counter = 0
        self.o_addr_counter = 0
        self._ctrl_iofile_path = os.path.join(prj_cfg.root, 'ctrl_io.config')

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
                        self.ctrl_ios.digital_inputs.append(line)
                    elif isinstance(line, DigitalCtrlOutput):
                        line.o_addr = self._assign_o_addr()
                        self.ctrl_ios.digital_outputs.append(line)
                    elif isinstance(line, AnalogCtrlInput):
                        line.i_addr = self._assign_i_addr()
                        self.ctrl_ios.analog_inputs.append(line)
                    elif isinstance(line, AnalogCtrlOutput):
                        line.o_addr = self._assign_o_addr()
                        self.ctrl_ios.analog_outputs.append(line)
                    else:
                        raise Exception(f"Line {k+1} of ctrl_io file: {self._ctrl_iofile_path} does not fit do a specified source or config type")
                except:
                    raise Exception(f"Line {k+1} of config file: {self._ctrl_iofile_path} could not be processed properely")

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file):
        super().__init__(cfg_file=cfg_file, section=ConfigSections.FPGASIM)
        self.comport = None
        self.baud_rate = 115200
        self.timeout = None
        self.parity = serial.PARITY_NONE
        self.stopbits=1
        self.bytesize=serial.EIGHTBITS

class CtrlIOs():
    """
    Container to store all Control IOs for associated Control Interface.
    """
    def __init__(self):
        self.digital_inputs = []
        self.digital_outputs = []
        self.analog_inputs = []
        self.analog_outputs = []