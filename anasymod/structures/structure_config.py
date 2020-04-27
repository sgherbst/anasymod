import os, yaml

from anasymod.enums import ConfigSections
from anasymod.base_config import BaseConfig
from anasymod.config import EmuConfig
from anasymod.sim_ctrl.datatypes import (
    DigitalSignal, DigitalCtrlInput, DigitalCtrlOutput,
    AnalogProbe, AnalogCtrlInput, AnalogCtrlOutput
)

class StructureConfig():
    """
    In this configuration, all the toplevel information about the generated toplevel is included.
    It will be used for generation of the target specific top-level, as well as attached wrappers.

    There is also a specific interface to flow plugins that allows modification due to some needs
    from the plugin side, e.g. additional clks, resets, ios to the host application or resources on the FPGA board.
    """
    def __init__(self, prj_cfg: EmuConfig, tstop, simctrl_path, can_use_default_oscillator=True):
        # Internal variables
        self.i_addr_counter = 0
        self.o_addr_counter = 0

        # Path to clks.yaml file
        self._clks_file_path = os.path.join(prj_cfg.root, 'clks.yaml')
        # Path to simctrl.yaml file
        self._simctrl_file_path = simctrl_path

        self.cfg = Config(prj_cfg=prj_cfg)
        self.cfg.update_config()

        #########################################################
        # Manage clks
        #########################################################

        self.emu_clk = ClkIndependent(name='emu_clk', freq=float(prj_cfg.cfg.emu_clk_freq))
        self.emu_clk_2x = ClkIndependent(name='emu_clk_2x', freq=float(prj_cfg.cfg.emu_clk_freq) * 2) # multiplied by two, as emu_clk_2x is twice as fast as emu_clk
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

        # add a default derived clock if needed
        if (self.num_dt_reqs == 0) and can_use_default_oscillator:
            self._add_default_oscillator()
            self.use_default_oscillator = True
        else:
            self.use_default_oscillator = False

        # add control block
        self._add_ctrl_anasymod()

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

        # annotate special control signals that should not
        # be routed to sim_ctrl
        self.special_ctrl_ios = set()

        # Add time signal representing current simulated time
        self.time_probe = DigitalSignal(
            name='emu_time',
            width=prj_cfg.cfg.time_width,
            abspath=''
        )

        # Add DigitalCtrlInput for reset
        self.reset_ctrl = DigitalCtrlInput(
            name='emu_rst',
            width=1,
            abspath = None
        )
        self.reset_ctrl.i_addr = self._assign_i_addr()
        self.digital_ctrl_inputs += [self.reset_ctrl]
        self.special_ctrl_ios.add(self.reset_ctrl.name)

        # Add DigitalCtrlInput for control signal 'emu_dec_thr' to manage decimation
        # ratio for capturing probe samples
        self.dec_thr_ctrl = DigitalCtrlInput(
            name='emu_dec_thr',
            width=int(prj_cfg.cfg.dec_bits),
            abspath = None
        )
        self.dec_thr_ctrl.i_addr = self._assign_i_addr()
        self.digital_ctrl_inputs += [self.dec_thr_ctrl]
        self.special_ctrl_ios.add(self.dec_thr_ctrl.name)

        # Add DigitalCtrlInput for control signal 'emu_time_tgt' to run for
        # a specific amount of time
        self.emu_ctrl_data = DigitalCtrlInput(
            name='emu_ctrl_data',
            width=int(prj_cfg.cfg.time_width),
            abspath = None
        )
        self.emu_ctrl_data.i_addr = self._assign_i_addr()
        self.digital_ctrl_inputs += [self.emu_ctrl_data]
        self.special_ctrl_ios.add(self.emu_ctrl_data.name)

        # Add DigitalCtrlInput for control signal 'emu_ctrl_mode' to run for
        # a specific amount of time
        self.emu_ctrl_mode = DigitalCtrlInput(
            name='emu_ctrl_mode',
            width=4,
            abspath = None
        )
        self.emu_ctrl_mode.i_addr = self._assign_i_addr()
        self.digital_ctrl_inputs += [self.emu_ctrl_mode]
        self.special_ctrl_ios.add(self.emu_ctrl_mode.name)

        # Add DigitalCtrlOutput for reading the emulation time
        self.emu_time_vio = DigitalCtrlOutput(
            name='emu_time_vio',
            width=prj_cfg.cfg.time_width,
            abspath = 'emu_time'
        )
        self.emu_time_vio.i_addr = self._assign_o_addr()
        self.digital_ctrl_outputs += [self.emu_time_vio]
        self.special_ctrl_ios.add(self.emu_time_vio.name)

        # Add DigitalSignal for control of signal 'emu_dec_cmp' to trigger sampling
        # for the ila depending on 'emu_dec_thr'
        self.dec_cmp = DigitalSignal(
            name='emu_dec_cmp',
            abspath='emu_dec_cmp_probe',
            width=1
        )

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
                        self.clk_independent.append(
                            ClkIndependent(
                                name=independent_clk,
                                freq=float(clks['independent_clks'][independent_clk]['freq'])
                            )
                        )
                else:
                    print(f'No Independent Clks provided.')

                # Add derived clks to structure config
                if 'derived_clks' in clks.keys():
                    print(f'Derived Clks: {[key for key in clks["derived_clks"].keys()]}')

                    for derived_clk_name, derived_clk in clks['derived_clks'].items():
                        # find out the absolute path prefix
                        if 'abspath' in derived_clk:
                            abspath_default = derived_clk['abspath']
                        else:
                            raise Exception(f'No abspath provided for clk: {derived_clk}')

                        # little convenience function for prepending the absolute path
                        def make_abs_path(key, default):
                            signame = derived_clk.get(key, '')
                            if signame == '':
                                signame = default
                            return f'{abspath_default}.{signame}'

                        # read out the prefix name (if any)
                        preset = derived_clk.get('preset', None)

                        # for each subsequent signal, set its absolute path
                        # if provided explicitly or implicitly via a preset

                        if ('emu_dt' in derived_clk) or \
                                (preset in {'variable_timestep', 'oscillator'}):
                            abspath_emu_dt = make_abs_path('emu_dt', '__emu_dt')
                        else:
                            abspath_emu_dt = None

                        if ('dt_req' in derived_clk) or \
                                (preset in {'variable_timestep', 'oscillator'}):
                            abspath_dt_req = make_abs_path('dt_req', '__emu_dt_req')
                            self.num_dt_reqs += 1
                        else:
                            abspath_dt_req = None

                        if ('emu_clk' in derived_clk) or \
                                (preset in {'fixed_timestep', 'variable_timestep', 'oscillator'}):
                            abspath_emu_clk = make_abs_path('emu_clk', '__emu_clk')
                        else:
                            abspath_emu_clk = None

                        if ('emu_rst' in derived_clk) or \
                                (preset in {'fixed_timestep', 'variable_timestep', 'oscillator'}):
                            abspath_emu_rst = make_abs_path('emu_rst', '__emu_rst')
                        else:
                            abspath_emu_rst = None

                        if ('gated_clk' in derived_clk) or \
                                (preset in {'fixed_timestep', 'oscillator'}):
                            abspath_gated_clk = make_abs_path('gated_clk', '__emu_clk_i')
                            self.num_gated_clks += 1
                        else:
                            abspath_gated_clk = None

                        if ('gated_clk_req' in derived_clk) or \
                                (preset in {'fixed_timestep', 'oscillator'}):
                            abspath_gated_clk_req = make_abs_path('gated_clk_req', '__emu_clk_val')
                        else:
                            abspath_gated_clk_req = None

                        self.clk_derived.append(
                            ClkDerived(
                                name=derived_clk_name,
                                abspath_emu_dt=abspath_emu_dt,
                                abspath_emu_clk=abspath_emu_clk,
                                abspath_emu_rst=abspath_emu_rst,
                                abspath_dt_req=abspath_dt_req,
                                abspath_gated_clk=abspath_gated_clk,
                                abspath_gated_clk_req=abspath_gated_clk_req
                            )
                        )
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
        else:
            print('No simctrl.yaml file existing, no additional probes will be available for this simulation.')
            return

        if sigs is None:
            print('No signals specified in simctrl.yaml.')
            return

        # debug waveform dumping (simulation only)
        if 'dump_debug' in sigs:
            self.dump_debug = True
        else:
            self.dump_debug = False

        # Add analog probes to structure config
        if 'analog_probes' in sigs:
            print(f'Analog Probes: {list(sigs["analog_probes"].keys())}')
            for name, analog_probe in sigs['analog_probes'].items():
                self.analog_probes.append(AnalogProbe.from_dict(name, analog_probe))
        else:
            print(f'No Analog Probes provided.')

        # Add digital probes to structure config
        if 'digital_probes' in sigs:
            print(f'Digital Probes: {list(sigs["digital_probes"].keys())}')
            for name, digital_probe in sigs['digital_probes'].items():
                self.digital_probes.append(DigitalSignal.from_dict(name, digital_probe))
        else:
            print(f'No Digital Probes provided.')

        # Add digital ctrl inputs to structure config
        if sigs.get('digital_ctrl_inputs', None) is not None:
            print(f'Digital Ctrl Inputs: {list(sigs["digital_ctrl_inputs"].keys())}')
            for name, d_ctrl_in in sigs['digital_ctrl_inputs'].items():
                d_ctrl_i = DigitalCtrlInput.from_dict(name, d_ctrl_in)
                d_ctrl_i.i_addr = self._assign_i_addr()
                self.digital_ctrl_inputs.append(d_ctrl_i)
        else:
            print(f'No Digital Ctrl Input provided.')

        # Add digital ctrl outputs to structure config
        if sigs.get('digital_ctrl_outputs', None) is not None:
            print(f'Digital Ctrl Outputs: {list(sigs["digital_ctrl_outputs"].keys())}')
            for name, d_ctrl_out in sigs['digital_ctrl_outputs'].items():
                d_ctrl_o = DigitalCtrlOutput.from_dict(name, d_ctrl_out)
                d_ctrl_o.o_addr = self._assign_o_addr()
                self.digital_ctrl_outputs.append(d_ctrl_o)
        else:
            print(f'No Digital Ctrl Outputs provided.')

        # Add analog ctrl inputs to structure config
        if sigs.get('analog_ctrl_inputs', None) is not None:
            print(f'Analog Ctrl Inputs: {list(sigs["analog_ctrl_inputs"].keys())}')
            for name, a_ctrl_in in sigs['analog_ctrl_inputs'].items():
                a_ctrl_i = AnalogCtrlInput.from_dict(name, a_ctrl_in)
                a_ctrl_i.i_addr = self._assign_i_addr()
                self.analog_ctrl_inputs.append(a_ctrl_i)
        else:
            print(f'No Analog Ctrl Input provided.')

        # Add analog ctrl outputs to structure config
        if sigs.get('analog_ctrl_outputs', None) is not None:
            print(f'Analog Ctrl Outputs: {list(sigs["analog_ctrl_outputs"].keys())}')
            for name, a_ctrl_out in sigs['analog_ctrl_outputs'].items():
                a_ctrl_o = AnalogCtrlOutput.from_dict(name, a_ctrl_out)
                a_ctrl_o.o_addr = self._assign_o_addr()
                self.analog_ctrl_outputs.append(a_ctrl_o)
        else:
            print(f'No Analog Ctrl Outputs provided.')

    def _add_default_oscillator(self):
        self.clk_derived.append(
            ClkDerived(
                name='def_osc',
                abspath_emu_dt='def_osc_i.__emu_dt',
                abspath_emu_clk='def_osc_i.__emu_clk',
                abspath_emu_rst='def_osc_i.__emu_rst',
                abspath_dt_req='def_osc_i.__emu_dt_req'
            )
        )

        # update counts
        self.num_dt_reqs += 1
        #self.num_gated_clks += 1

    def _add_ctrl_anasymod(self):
        self.clk_derived.append(
            ClkDerived(
                name='ctrl_blk',
                abspath_emu_dt='ctrl_anasymod_i.__emu_dt',
                abspath_emu_clk='ctrl_anasymod_i.__emu_clk',
                abspath_emu_rst='ctrl_anasymod_i.__emu_rst',
                abspath_dt_req='ctrl_anasymod_i.__emu_dt_req'
            )
        )

class ClkIndependent(DigitalSignal):
    """
    Container for an independent clk object.
    """

    def __init__(self, name, freq):
        # call the super constructor
        super().__init__(abspath='', name=name, width=1)

        # save settings
        self.freq = freq


class ClkDerived(DigitalSignal):
    """
    Container for a derived clk object.
    """

    def __init__(self, name, abspath_emu_dt=None, abspath_emu_clk=None,
                 abspath_emu_rst=None, abspath_dt_req=None,
                 abspath_gated_clk=None, abspath_gated_clk_req=None):
        # call the super constructor
        super().__init__(abspath='', name=name, width=1)

        # save settings
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
        """ type(int) : number of clk cycles, the initial emu_rst signal shall be active. """