import os

from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig
from anasymod.config import EmuConfig
from anasymod.structures.port_base import PortIN, PortOUT, Port
from anasymod.structures.signal_base import Signal
from anasymod.sim_ctrl.ctrlifc_datatypes import DigitalSignal, DigitalCtrlInput, DigitalCtrlOutput, AnalogSignal, AnalogCtrlInput, AnalogCtrlOutput, ProbeSignal

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

        # Path to ctrl_io file
        self._ctrl_iofile_path = os.path.join(prj_cfg.root, 'ctrl_io.config')
        # Path to clk file
        self._clk_file_path = os.path.join(prj_cfg.root, 'clk.config')
        # Path to clk file
        self._dt_req_file_path = os.path.join(prj_cfg.root, 'dt_req.config')
        # Path to probe file
        self._probe_file_path = os.path.join(prj_cfg.root, 'probe.config')


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

        #Only for testing
        #self.digital_ctrl_inputs = [DigitalCtrlInput(name='hufflpu', width=31, abspath='test',init_value=41)]
        #self.digital_ctrl_inputs[0].i_addr = self._assign_i_addr()
        #self.digital_ctrl_outputs = [DigitalCtrlOutput(name='banii', width=1, abspath='testi')]
        #self.digital_ctrl_outputs[0].o_addr = self._assign_o_addr()
        #self.analog_ctrl_inputs = [AnalogCtrlInput(name='mimpfl', init_value=42.0, abspath='testii', range=500)]
        #self.analog_ctrl_inputs[0].i_addr = self._assign_i_addr()
        #self.analog_ctrl_outputs = [AnalogCtrlOutput(name='primpf', range=250, abspath=r'top.tb_i.v_out')]
        #self.analog_ctrl_outputs[0].o_addr = self._assign_o_addr()

        self._read_iofile()

        #########################################################
        # CLK manager interfaces
        #########################################################

        self.emu_clk = DigitalSignal(name='emu_clk', abspath=None, width=1)

        # add clk_in
        self.clk_i_num = len(prj_cfg.board.clk_pin)

        # clk_in names cannot be changed
        if self.clk_i_num == 2:
            self.clk_i = [DigitalSignal(abspath=None, width=1, name='clk_in1_p'), DigitalSignal(abspath=None, width=1, name='clk_in1_n')]
        elif self.clk_i_num == 1:
            self.clk_i = [DigitalSignal(abspath=None, width=1, name='clk_in1')]
        else:
            raise ValueError(
                f"Wrong number of pins for boards param 'clk_pin', expecting 1 or 2, provided:{self.clk_i_num}")

        # add master clk_outs, currently there is exactly one master clock, in case there is the need for multiple ones,
        # the num parameter needs to be exposed and naming needs to be configurable -> names might still be hardcoded at
        # some places!!!
        self.clk_m_num = 1
        self.clk_m = [DigitalSignal(abspath=None, width=1, name='emu_clk_2x')]

        # add debug clk_out
        self.clk_d_num = 1
        self.clk_d = []

        # currently there is exactly one debug clock, in case there is the need for multiple ones, name handling must be
        # implemented, there are some places in codebase where the debug clk name is still hard coded!!!
        for k in range(self.clk_d_num):
            self.clk_d += [DigitalSignal(abspath=None, width=1, name=f'dbg_hub_clk{k}')]

        #########################################################
        # EMU CLK generator interfaces
        #########################################################

        # add custom clk_out and associated clk_gate (currently all of them are derrived from this one master clk)
        # signals as tuples (clk_out, clk_gate)
        self.clk_o = []

        self._read_clkfile()

        #########################################################
        # Time manager interfaces
        #########################################################

        self.dt_reqs = []

        self._read_dt_reqfile()

        #########################################################
        # Probe interfaces
        #########################################################

        self.analog_probes = [] # use later
        self.time_probes = [] # use later
        self.reset_probes = [] # use later
        self.digital_probes = [] # use later

        #temporary
        self.probes = []
        """ : type: ProbeSignal"""

        self._read_probefile()

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
        Read all lines from iofile and call parse function to populate ctrl_ios attributes.
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

    def _read_clkfile(self):
        """
        Read all lines from clk.config file and call parse function to populate emu clk attribute.
        """
        if os.path.isfile(self._clk_file_path):
            with open(self._clk_file_path, "r") as f:
                clks = f.readlines()
            self._parse_clkfile(clks=clks)
        else:
            print(f"No clk.config file existing, no additional clks will be added.")

    def _parse_clkfile(self, clks: []):
        """
        Read all lines from ctrl io file and store IO objects in CtrlIO container while adding access addresses to
        each IO object.
        :param clks: Lines extracted from clk file
        """

        for k, item in enumerate(clks):
            item = item.strip()

            if item.startswith('#'):
                # skip comments
                continue

            if item:
                try:
                    item = eval(item)
                    if isinstance(item, str):
                        self.clk_o.append(item)
                    else:
                        raise Exception(f"Elements of line {k + 1} in clk file: {self._clk_file_path} don't consist of strings")
                except:
                    raise Exception(f"Line {k+1} of clk file: {self._clk_file_path} could not be processed properely")

    def _read_dt_reqfile(self):
        """
        Read all lines from dt_req.config file and call parse function to populate dt_req attribute.
        """
        if os.path.isfile(self._dt_req_file_path):
            with open(self._dt_req_file_path, "r") as f:
                dt_reqs = f.readlines()
            self._parse_dt_reqfile(dt_reqs=dt_reqs)
        else:
            print(f"No dt_req.config file existing, no additional dt requests will be added.")

    def _parse_dt_reqfile(self, dt_reqs: list):
        """
        Read all lines from dt_req file dt_req.config and store in dt_req attribute.
        :param clks: Lines extracted from dt_req file
        """

        for k, dt_req in enumerate(dt_reqs):
            dt_req = dt_req.strip()

            if dt_req.startswith('#'):
                # skip comments
                continue

            if dt_req:
                try:
                    dt_req = eval(dt_req)
                    if isinstance(dt_req, str):
                        self.dt_reqs.append(dt_req)
                    else:
                        raise Exception(f"Tuple elements of line {k + 1} in clk file: {self._dt_req_file_path} don't consist of strings")
                except:
                    raise Exception(f"Line {k+1} of clk file: {self._dt_req_file_path} could not be processed properely")

    def _read_probefile(self):
        """
        Read all lines from probe.config file and call parse function to populate probe attribute.
        """
        if os.path.isfile(self._probe_file_path):
            with open(self._probe_file_path, "r") as f:
                probes = f.readlines()
            self._parse_probefile(probes=probes)
        else:
            print(f"No probe.config file existing, no additional probes will be available for this simulation.")

    def _parse_probefile(self, probes: list):
        """
        Read all lines from probe file probe.config and store in probe attribute.
        :param clks: Lines extracted from dt_req file
        """

        for k, probe in enumerate(probes):
            probe = probe.strip()

            if probe.startswith('#'):
                # skip comments
                continue

            if probe:
                try:
                    probe = eval(probe)
                    if (isinstance(probe, list) and len(probe) == 4):
                        self.probes.append(ProbeSignal(name=probe[0], abspath=probe[1], width=probe[2], exponent=probe[3]))
                    else:
                        raise Exception(f"Probe specified in line {k + 1} in probe file: {self._probe_file_path} has "
                                        f"wrong format, expected is: ['name', 'abspath', 'width','exponent']")
                except:
                    raise Exception(f"Line {k+1} of probe.config file: {self._probe_file_path} could not be processed properely")

        # ToDo: Once different probe types are supported, parser needs to differenciate properly
        #self.analog_signals = []
        #for name, width, exponent in zip(signals[0], signals[2], signals[1]):
        #    self.analog_signals.append((name, width, exponent))

        #self.time_signal = []
        #for name,width, exponent in zip(signals[3], signals[5], signals[4]):
        #    self.time_signal.append((name, width, exponent))

        #self.reset_signal = []
        #for name,width, exponent in zip(signals[6], [r"1"], [None]):
        #    self.reset_signal.append((name, width, exponent))

        #self.digital_signals = []
        #for name in signals[7]:
        #    self.digital_signals.append((name, r"1", None))

        #for name, width in zip(signals[8], signals[9]):
        #    self.digital_signals.append((name, width, None))

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, prj_cfg: EmuConfig):
        super().__init__(cfg_file=prj_cfg.cfg_file, section=ConfigSections.STRUCTURE)

        self.rst_clkcycles = 1

        #########################################################
        # CLK manager settings
        #########################################################

        # add gated clk_outs
        self.clk_o_num = 0
        self.clk_g_num = 0