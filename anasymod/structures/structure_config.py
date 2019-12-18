import os, yaml

from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.datatypes import DigitalSignal, DigitalCtrlInput, DigitalCtrlOutput, AnalogSignal, AnalogCtrlInput, AnalogCtrlOutput, AnalogProbe

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

        # Path to clk file
        self._clk_file_path = os.path.join(prj_cfg.root, 'clk.config')
        # Path to clk file
        self._dt_req_file_path = os.path.join(prj_cfg.root, 'dt_req.config')
        # Path to simctrl file
        self._simctrl_file_path = os.path.join(prj_cfg.root, 'simctrl.config')

        self.cfg = Config(prj_cfg=prj_cfg)
        self.cfg.update_config()

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
        # Simulation control interfaces
        #########################################################

        self.analog_probes = []
        self.time_probe = None
        self.digital_probes = []

        # ToDo: Dec Threshold behavior needs to be moved from mactros to SV module

        ## Add ctrl signals for the ila block
        # Time signal representing current simulated time
        self.time_probe = AnalogProbe(name='emu_time', abspath='emu_time_probe', range=10, width=39)
        # Decimation comparator signal, this controls enabling and disabling signal capturing via ila
        self.digital_probes.append(DigitalSignal(name='emu_dec_cmp', abspath='emu_dec_cmp_probe', width=1))

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

        # Only for testing
        # self.digital_ctrl_inputs = [DigitalCtrlInput(name='hufflpu', width=31, abspath='test',init_value=41)]
        # self.digital_ctrl_inputs[0].i_addr = self._assign_i_addr()
        # self.digital_ctrl_outputs = [DigitalCtrlOutput(name='banii', width=1, abspath='testi')]
        # self.digital_ctrl_outputs[0].o_addr = self._assign_o_addr()
        # self.analog_ctrl_inputs = [AnalogCtrlInput(name='mimpfl', init_value=42.0, abspath='testii', range=500)]
        # self.analog_ctrl_inputs[0].i_addr = self._assign_i_addr()
        # self.analog_ctrl_outputs = [AnalogCtrlOutput(name='primpf', range=250, abspath=r'top.tb_i.v_out')]
        # self.analog_ctrl_outputs[0].o_addr = self._assign_o_addr()

        self._read_simctrlfile()

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

    def _read_simctrlfile(self):
        """
        Read all lines from simulation control file simctrl.config and store in structure config attributes.
        """
        if os.path.isfile(self._simctrl_file_path):
            with open(self._simctrl_file_path, "r") as f:
                try:
                    sigs = yaml.safe_load(f)
                except yaml.YAMLError as exc:
                    print(exc)
        else:
            print(f"No probe.config file existing, no additional probes will be available for this simulation.")

        # Add analog probes to structure config
        if 'analog_probes' in sigs.keys():
            print(f'Analog Probes: {[key for key in sigs["analog_probes"].keys()]}')
            for analog_probe in sigs['analog_probes'].keys():
                if 'width' in sigs['analog_probes'][analog_probe].keys(): # Set width if given
                    self.analog_probes.append(AnalogProbe(name=analog_probe,
                                                          abspath=sigs['analog_probes'][analog_probe]['abspath'],
                                                          range=sigs['analog_probes'][analog_probe]['range'],
                                                          width=sigs['analog_probes'][analog_probe]['width']))
                else:
                    self.analog_probes.append(AnalogProbe(name=analog_probe,
                                                          abspath=sigs['analog_probes'][analog_probe]['abspath'],
                                                          range=sigs['analog_probes'][analog_probe]['range']))
        else:
            print(f'No Analog Probes provided.')

        # Add digital probes to structure config
        if 'digital_probes' in sigs.keys():
            print(f'Digital Probes: {[key for key in sigs["digital_probes"].keys()]}')
            for digital_probe in sigs['digital_probes'].keys():
                self.digital_probes.append(DigitalSignal(name=digital_probe,
                                                        abspath=sigs['digital_probes'][digital_probe]['abspath'],
                                                        width=sigs['digital_probes'][digital_probe]['width']))
        else:
            print(f'No Digital Probes provided.')

        # Add digital ctrl inputs to structure config
        if 'digital_ctrl_inputs' in sigs.keys() and sigs['digital_ctrl_inputs'] is not None:
            print(f'Digital Ctrl Inputs: {[key for key in sigs["digital_ctrl_inputs"].keys()]}')
            for d_ctrl_in in sigs['digital_ctrl_inputs'].keys():
                if 'init_value' in sigs['digital_ctrl_inputs'][d_ctrl_in].keys():  # Set init_value if given
                    d_ctrl_i = DigitalCtrlInput(name=d_ctrl_in,
                                                abspath=sigs['digital_ctrl_inputs'][d_ctrl_in]['abspath'],
                                                width=sigs['digital_ctrl_inputs'][d_ctrl_in]['width'],
                                                init_value=sigs['digital_ctrl_inputs'][d_ctrl_in]['init_value'])
                else:
                    d_ctrl_i = DigitalCtrlInput(name=d_ctrl_in,
                                                abspath=sigs['digital_ctrl_inputs'][d_ctrl_in]['abspath'],
                                                width=sigs['digital_ctrl_inputs'][d_ctrl_in]['width'])
                d_ctrl_i.i_addr = self._assign_i_addr()
                self.digital_ctrl_inputs.append(d_ctrl_i)
        else:
            print(f'No Digital Ctrl Input provided.')

        # Add digital ctrl outputs to structure config
        if 'digital_ctrl_outputs' in sigs.keys() and sigs['digital_ctrl_outputs'] is not None:
            print(f'Digital Ctrl Outputs: {[key for key in sigs["digital_ctrl_outputs"].keys()]}')
            for d_ctrl_out in sigs['digital_ctrl_outputs'].keys():
                d_ctrl_o = DigitalCtrlOutput(name=d_ctrl_out,
                                             abspath=sigs['digital_ctrl_outputs'][d_ctrl_out]['abspath'],
                                             width=sigs['digital_ctrl_outputs'][d_ctrl_out]['width'])
                d_ctrl_o.o_addr = self._assign_o_addr()
                self.digital_ctrl_outputs.append(d_ctrl_o)
        else:
            print(f'No Digital Ctrl Outputs provided.')

        # Add analog ctrl inputs to structure config
        if 'analog_ctrl_inputs' in sigs.keys() and sigs['analog_ctrl_inputs'] is not None:
            print(f'Analog Ctrl Inputs: {[key for key in sigs["analog_ctrl_inputs"].keys()]}')
            for a_ctrl_in in sigs['analog_ctrl_inputs'].keys():
                if 'init_value' in sigs['digital_ctrl_inputs'][a_ctrl_in].keys():  # Set init_value if given
                    a_ctrl_i = AnalogCtrlInput(name=a_ctrl_in,
                                                abspath=sigs['analog_ctrl_inputs'][a_ctrl_in]['abspath'],
                                                range=sigs['analog_ctrl_inputs'][a_ctrl_in]['range'],
                                                init_value=sigs['analog_ctrl_inputs'][a_ctrl_in]['init_value'])
                else:
                    a_ctrl_i = AnalogCtrlInput(name=a_ctrl_in,
                                                abspath=sigs['digital_ctrl_inputs'][a_ctrl_in]['abspath'],
                                                range=sigs['digital_ctrl_inputs'][a_ctrl_in]['range'])
                a_ctrl_i.i_addr = self._assign_i_addr()
                self.analog_ctrl_inputs.append(a_ctrl_i)
        else:
            print(f'No Digital Ctrl Input provided.')

        # Add analog ctrl outputs to structure config
        if 'analog_ctrl_outputs' in sigs.keys() and sigs['analog_ctrl_outputs'] is not None:
            print(f'Analog Ctrl Outputs: {[key for key in sigs["analog_ctrl_outputs"].keys()]}')
            for a_ctrl_out in sigs['analog_ctrl_outputs'].keys():
                a_ctrl_o = AnalogCtrlOutput(name=a_ctrl_out,
                                             abspath=sigs['analog_ctrl_outputs'][a_ctrl_out]['abspath'],
                                             range=sigs['analog_ctrl_outputs'][a_ctrl_out]['range'])
                a_ctrl_o.o_addr = self._assign_o_addr()
                self.analog_ctrl_outputs.append(a_ctrl_o)
        else:
            print(f'No Analog Ctrl Outputs provided.')

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