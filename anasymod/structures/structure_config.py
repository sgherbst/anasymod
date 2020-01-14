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
    def __init__(self, prj_cfg: EmuConfig, tstop):
        # Internal variables
        self.i_addr_counter = 0
        self.o_addr_counter = 0

        # Path to clks.yaml file
        self._clks_file_path = os.path.join(prj_cfg.root, 'clks.yaml')
        # Path to simctrl.yaml file
        self._simctrl_file_path = os.path.join(prj_cfg.root, 'simctrl.yaml')

        self.cfg = Config(prj_cfg=prj_cfg)
        self.cfg.update_config()

        #########################################################
        # Manage clks
        #########################################################

        self.emu_clk = ClkIndependent(name='emu_clk', freq=float(prj_cfg.cfg.emu_clk_freq))
        self.emu_clk_2x = ClkIndependent(name='emu_clk_2x', freq=float(prj_cfg.cfg.emu_clk_freq * 2)) # multiplied by two, as emu_clk_2x is twice as fast as emu_clk
        self.dbg_clk = ClkIndependent(name='dbg_hub_clk', freq=float(prj_cfg.board.dbg_hub_clk_freq))

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

        # Add independent clks, that will be implemented via clk_wiz IP core for FPGA
        self.clk_independent = []
        """ type : [ClkIndependent]"""

        # Add derived clks; those are aligned with emu_clk
        self.clk_derived = []
        """ type : [ClkDerived]"""

        # Number of gated clks
        self.num_gated_clks = 0

        # Number of dt requests
        self.num_dt_reqs = 0

        self._read_clksfile()

        #########################################################
        # Simulation control interfaces
        #########################################################

        # CtrlIOs
        self.digital_ctrl_inputs = []
        self.digital_ctrl_outputs = []
        self.analog_ctrl_inputs = []
        self.analog_ctrl_outputs = []
        self.analog_probes = []
        self.digital_probes = []

        # ToDo: Dec Threshold behavior needs to be moved from mactros to SV module

        # Add time signal representing current simulated time
        self.time_probe = AnalogProbe(name='emu_time', abspath='', range=(1.1 * tstop), width=prj_cfg.cfg.time_width)

        # Add DigitalCtrlInput for reset
        self.reset_ctrl = DigitalCtrlInput(abspath=None, name='emu_rst', width=1)
        self.reset_ctrl.i_addr = self._assign_i_addr()

        # Add DigitalCtrlInput for control signal 'emu_dec_thr' to manage decimation ration for capturing probe samples
        self.dec_thr_ctrl = DigitalCtrlInput(abspath=None, name='emu_dec_thr', width=int(prj_cfg.cfg.dec_bits))
        self.dec_thr_ctrl.i_addr = self._assign_i_addr()

        # Add DigitalCtrlInput for control signal 'emu_dec_cmp' to trigger samplöing for the ila depending on 'emu_dec_thr'
        self.dec_cmp = DigitalSignal(name='emu_dec_cmp', abspath='emu_dec_cmp_probe', width=1)

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

    def _read_clksfile(self):
        """
        Read all lines from clks file clks.config and store in structure config attributes. This includes either
        independent clks, which will directly be added to the clk management block and in case of a FPGA simulation
        implemented via clk_wiz IP core, or derived clks, which will be derived for the main emulation clk em,u_clk_2x.
        """
        if os.path.isfile(self._clks_file_path):
            try:
                clks = yaml.safe_load(open(self._clks_file_path, "r"))
            except yaml.YAMLError as exc:
                raise Exception(exc)

            if clks is not None:
                # Add independent clks to structure config
                if 'independent_clks' in clks.keys():
                    print(f'Independent Clks: {[key for key in clks["independent_clks"].keys()]}')
                    for independent_clk in clks['independent_clks'].keys():
                        self.clk_independent.append(ClkIndependent(name=independent_clk,
                                                                   freq=float(clks['independent_clks'][independent_clk]['freq'])))
                else:
                    print(f'No Independent Clks provided.')

                # Add derived clks to structure config
                if 'derived_clks' in clks.keys():
                    print(f'Derived Clks: {[key for key in clks["derived_clks"].keys()]}')
                    for derived_clk in clks['derived_clks'].keys():
                        abspath_emu_dt = None
                        abspath_emu_clk = None
                        abspath_emu_rst = None
                        abspath_dt_req = None
                        abspath_gated_clk = None
                        abspath_gated_clk_req = None
                        if 'abspath' in clks['derived_clks'][derived_clk].keys():  # default abspath is provided
                            abspath_default = clks['derived_clks'][derived_clk]['abspath']
                        else:
                            raise Exception(f'No abspath provided for clk: {derived_clk}')

                        if 'emu_dt' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['fixed_timestep', 'variable_timestep', 'oscillator']):
                            abspath_emu_dt = abspath_default + '.' + clks['derived_clks'][derived_clk]['emu_dt'] if clks['derived_clks'][derived_clk]['emu_dt'] is not "" else '__emu_dt'
                        if 'emu_clk' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['fixed_timestep', 'variable_timestep', 'oscillator']):
                            abspath_emu_clk = abspath_default + '.' + clks['derived_clks'][derived_clk]['emu_clk'] if clks['derived_clks'][derived_clk]['emu_clk'] is not "" else '__emu_clk'
                        if 'emu_rst' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['fixed_timestep', 'variable_timestep', 'oscillator']):
                            abspath_emu_rst = abspath_default + '.' + clks['derived_clks'][derived_clk]['emu_rst'] if clks['derived_clks'][derived_clk]['emu_rst'] is not "" else '__emu_rst'
                        if 'dt_req' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['variable_timestep', 'oscillator']):
                            abspath_dt_req = abspath_default + '.' + clks['derived_clks'][derived_clk]['dt_req'] if clks['derived_clks'][derived_clk]['dt_req'] is not "" else '__emu_dt_req'
                            self.num_dt_reqs += 1
                        if 'gated_clk' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['oscillator']):
                            abspath_gated_clk = abspath_default + '.' + clks['derived_clks'][derived_clk]['gated_clk'] if clks['derived_clks'][derived_clk]['gated_clk'] is not "" else '__emu_clk_i'
                            self.num_gated_clks += 1
                        if 'gated_clk_req' in clks['derived_clks'][derived_clk].keys() or ('preset' in clks['derived_clks'][derived_clk].keys() and clks['derived_clks'][derived_clk]['preset'] in ['oscillator']):
                            abspath_gated_clk_req = abspath_default + '.' + clks['derived_clks'][derived_clk]['gated_clk'] if clks['derived_clks'][derived_clk]['gated_clk'] is not "" else '__emu_clk_val'

                        self.clk_derived.append(ClkDerived(name=derived_clk, abspath_emu_dt=abspath_emu_dt, abspath_emu_clk=abspath_emu_clk, abspath_emu_rst=abspath_emu_rst, abspath_dt_req=abspath_dt_req, abspath_gated_clk=abspath_gated_clk, abspath_gated_clk_req=abspath_gated_clk_req))
                else:
                    print(f'No Derived Clks provided.')
        else:
            print(f"No clks.config file existing, no additional clks will be added for this design.")

    def _read_simctrlfile(self):
        """
        Read all lines from simulation control file simctrl.yaml and store in structure config attributes.
        """
        if os.path.isfile(self._simctrl_file_path):
            try:
                sigs = yaml.safe_load(open(self._simctrl_file_path, "r"))
            except yaml.YAMLError as exc:
                raise Exception(exc)

            if sigs is not None:
                # Add analog probes to structure config
                if 'analog_probes' in sigs.keys():
                    print(f'Analog Probes: {[key for key in sigs["analog_probes"].keys()]}')
                    for analog_probe in sigs['analog_probes'].keys():
                        self.analog_probes.append(AnalogProbe(name=analog_probe,
                                                              abspath=sigs['analog_probes'][analog_probe]['abspath'],
                                                              range=sigs['analog_probes'][analog_probe]['range'],
                                                              width=sigs['analog_probes'][analog_probe]['width'] if 'width' in sigs['analog_probes'][analog_probe].keys() else 25))
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
                        d_ctrl_i = DigitalCtrlInput(name=d_ctrl_in,
                                                    abspath=sigs['digital_ctrl_inputs'][d_ctrl_in]['abspath'],
                                                    width=sigs['digital_ctrl_inputs'][d_ctrl_in]['width'],
                                                    init_value=sigs['digital_ctrl_inputs'][d_ctrl_in]['init_value'] if 'init_value' in sigs['digital_ctrl_inputs'][d_ctrl_in].keys() else 0)
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
                        a_ctrl_i = AnalogCtrlInput(name=a_ctrl_in,
                                                    abspath=sigs['analog_ctrl_inputs'][a_ctrl_in]['abspath'],
                                                    range=sigs['analog_ctrl_inputs'][a_ctrl_in]['range'],
                                                    init_value=sigs['analog_ctrl_inputs'][a_ctrl_in]['init_value'] if 'init_value' in sigs['analog_ctrl_inputs'][a_ctrl_in].keys() else 0.0)
                        a_ctrl_i.i_addr = self._assign_i_addr()
                        self.analog_ctrl_inputs.append(a_ctrl_i)
                else:
                    print(f'No Analog Ctrl Input provided.')

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
        else:
            print(f"No simctrl.yaml file existing, no additional probes will be available for this simulation.")

class ClkIndependent(DigitalSignal):
    """
    Container for an independent clk object.
    """

    def __init__(self, name, freq):
        super().__init__(abspath="", name=name, width=1)
        self.freq = freq

class ClkDerived(DigitalSignal):
    """
    Container for a derived clk object.
    """

    def __init__(self, name, abspath_emu_dt, abspath_emu_clk, abspath_emu_rst, abspath_dt_req, abspath_gated_clk, abspath_gated_clk_req):
        super().__init__(abspath="", name=name, width=1)
        self.abspath_emu_dt = abspath_emu_dt
        self.abspath_emu_clk = abspath_emu_clk
        self.abspath_emu_rst = abspath_emu_rst
        self.abspath_dt_req = abspath_dt_req
        self.abspath_gated_clk = abspath_gated_clk
        self.abspath_gated_clk_req = abspath_gated_clk_req

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """

    def __init__(self, prj_cfg: EmuConfig):
        super().__init__(cfg_file=prj_cfg.cfg_file, section=ConfigSections.STRUCTURE)

        self.rst_clkcycles = 1