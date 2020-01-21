import os
import os.path
import json
import numpy as np

from argparse import ArgumentParser

from anasymod.config import EmuConfig, SimVisionConfig, XceliumConfig
from anasymod.sim.vivado import VivadoSimulator
from anasymod.sim.icarus import IcarusSimulator
from anasymod.sim.xcelium import XceliumSimulator
from anasymod.viewer.gtkwave import GtkWaveViewer
from anasymod.viewer.scansion import ScansionViewer
from anasymod.viewer.simvision import SimVisionViewer
from anasymod.emu.vivado_emu import VivadoEmulation
from anasymod.files import get_full_path, get_from_anasymod, mkdir_p
from anasymod.sources import VerilogSource
from anasymod.filesets import Filesets
from anasymod.defines import Define
from anasymod.targets import SimulationTarget, FPGATarget, Target
from anasymod.utils import statpro
from typing import Union
from importlib import import_module

class Analysis():
    """
    This is the top user Class that shall be used to exercise anasymod.
    """
    def __init__(self, input=None, build_root=None, simulator_name=None, synthesizer_name=None, viewer_name=None, preprocess_only=None, op_mode=None, active_target=None):

        # Indicate that setup is not finished yet
        self._setup_finished = False

        # Parse command line arguments
        self.args = None
        self._parse_args()

        # Overwrite input location in case it was provided when instantiation the Analysis class
        if input is not None:
            self.args.input = input

        # expand path of input and output directories relative to analysis.py
        self.args.input = get_full_path(self.args.input)

        # update args according to user specified values when instantiating analysis class
        self.args.simulator_name = simulator_name if simulator_name is not None else self.args.simulator_name
        self.args.synthesizer_name = synthesizer_name if synthesizer_name is not None else self.args.synthesizer_name
        self.args.viewer_name = viewer_name if viewer_name is not None else self.args.viewer_name
        self.args.preprocess_only = preprocess_only if preprocess_only is not None else self.args.preprocess_only
        self.args.active_target = active_target if active_target is not None else self.args.active_target

        self.default_fpga_target = 'fpga'
        self.default_sim_target = 'sim'

        if self.args.active_target == 'fpga':
            self.default_fpga_target = self.args.active_target
        elif self.args.active_target == 'sim':
            self.default_sim_target = self.args.active_target

        # Load config file
        try:
            self.cfg_file = json.load(open(os.path.join(self.args.input, 'prj_config.json'), 'r'))
        except:
            self.cfg_file = None
            print(f"Warning: no config file was fround for the project, expected path is: {os.path.join(self.args.input, 'prj_config.json')}")

        # Initialize project config
        self._prj_cfg = EmuConfig(root=self.args.input, cfg_file=self.cfg_file, build_root=build_root)

        # Initialize Plugins
        self._plugins = []
        for plugin in self._prj_cfg.cfg.plugins:
            try:
                i = import_module(f"{plugin}.plugin")
                inst = i.CustomPlugin(prj_cfg=self._prj_cfg, cfg_file=self.cfg_file, prj_root=self.args.input)
                self._plugins.append(inst)
                setattr(self, inst._name, inst)
            except:
                raise KeyError(f"Could not process plugin:{plugin} properly! Check spelling")

        # Check which mode is used to run, in case of commandline mode, besided setting up the class, also argument will be executed
        if op_mode in ['commandline']:
            print(f"Running in commandline mode.")

            # Finalize project setup, no more modifications of filesets and targets after that!!!
            self.setup_filesets()
            self.finish_setup()

            ###############################################################
            # Set options from to command line arguments
            ###############################################################

            self._prj_cfg.cfg.preprocess_only = self.args.preprocess_only

            ###############################################################
            # Execute actions according to command line arguments
            ###############################################################

            # generate bitstream
            if self.args.build:
                self.args.active_target = self.default_fpga_target if self.args.active_target is None else self.args.active_target
                self.build()

            # run FPGA if desired
            if self.args.emulate:
                self.args.active_target = self.default_fpga_target if self.args.active_target is None else self.args.active_target
                self.emulate()

            # launch FPGA if desired
            if self.args.launch:
                self.args.active_target = self.default_fpga_target if self.args.active_target is None else self.args.active_target
                self.launch()

            # run simulation if desired
            if self.args.sim or self.args.preprocess_only:
                self.args.active_target = self.default_sim_target if self.args.active_target is None else self.args.active_target
                self.simulate(unit=self.args.unit, id=self.args.id)

            # view results if desired
            if self.args.view and (self.args.sim or self.args.preprocess_only):
                self.args.active_target = self.default_sim_target if self.args.active_target is None else self.args.active_target
                self.view()

            if self.args.view and self.args.emulate:
                self.args.active_target = self.default_fpga_target if self.args.active_target is None else self.args.active_target
                self.view()

##### Functions exposed for user to exercise on Analysis Object

    def setup_filesets(self):
        """
        Setup filesets for project.
        This may differ from one project to another and needs customization.
        1. Read in source objects from source.config files and store those in a fileset object
        2. Add additional source objects to fileset object
        """

        # Read source.config files and store in fileset object
        default_filesets = ['default', 'sim', 'fpga']
        self.filesets = Filesets(root=self.args.input, default_filesets=default_filesets)
        self.filesets.read_filesets()

        # Add Defines and Sources from plugins
        for plugin in self._plugins:
            plugin._setup_sources()
            plugin._setup_defines()
            self.filesets._defines += plugin._dump_defines()
            self.filesets._verilog_sources += plugin._dump_verilog_sources()
            self.filesets._verilog_headers += plugin._dump_verilog_headers()
            self.filesets._vhdl_sources += plugin._dump_vhdl_sources()

        # Add custom source and define objects here e.g.:
        # self.filesets.add_source(source=VerilogSource())
        # self.filesets.add_define(define=Define())
        config_path = os.path.join(self.args.input, 'source.config')

        # Add some default files depending on whether there is a custom top level
        # TODO: clean this part up with generated top level
        self.filesets.add_source(source=VerilogSource(files=get_from_anasymod('verilog', 'vio_gen.sv'), config_path=config_path))
        for fileset in ['sim', 'fpga']:
            try:
                custom_top = self.cfg_file['TARGET'][fileset]['custom_top']
                print(f'Using custom top for fileset {fileset}.')
            except:
                custom_top = False

            if not custom_top:
                #ToDo: check if file inclusion should be target specific -> less for simulation only for example
                self.filesets.add_source(source=VerilogSource(files=os.path.join(self.args.input, 'tb.sv'), config_path=config_path, fileset=fileset))
                self.filesets.add_source(source=VerilogSource(files=os.path.join(self._prj_cfg.build_root, 'gen_vio_wrap.sv'), config_path=config_path, fileset=fileset))
                self.filesets.add_source(source=VerilogSource(files=os.path.join(self._prj_cfg.build_root, 'gen_ctrlwrap.sv'), config_path=config_path, fileset=fileset))
                self.filesets.add_source(source=VerilogSource(files=get_from_anasymod('verilog', 'gen_emu_clks.sv'), config_path=config_path, fileset=fileset))
                self.filesets.add_source(source=VerilogSource(files=get_from_anasymod('verilog', 'time_manager.sv'), config_path=config_path, fileset=fileset))

                get_from_anasymod('verilog', 'zynq_uart.bd')

        # Set define variables specifying the emulator control architecture
        # TODO: find a better place for these operations, and try to avoid directly accessing the config dictionary
        self.filesets.add_define(define=Define(name='DEC_BITS_MSDSL', value=self._prj_cfg.cfg.dec_bits))
        for fileset in ['sim', 'fpga']:
            try:
                top_module = self.cfg_file['TARGET'][fileset]['top_module']
            except:
                top_module = 'top'

            print(f'Using top module {top_module} for fileset {fileset}.')
            self.filesets.add_define(define=Define(name='CLK_MSDSL', value=f'{top_module}.emu_clk', fileset=fileset))
            self.filesets.add_define(define=Define(name='RST_MSDSL', value=f'{top_module}.emu_rst', fileset=fileset))
            self.filesets.add_define(define=Define(name='DEC_THR_MSDSL', value=f'{top_module}.emu_dec_thr', fileset=fileset))
            self.filesets.add_define(define=Define(name='DT_WIDTH', value=f'{self._prj_cfg.cfg.dt_width}', fileset=fileset))
            self.filesets.add_define(define=Define(name='DT_EXPONENT', value=f'{self._prj_cfg.cfg.dt_exponent}', fileset=fileset))
            self.filesets.add_define(define=Define(name='TIME_WIDTH', value=f'{self._prj_cfg.cfg.time_width}', fileset=fileset))

    def finish_setup(self):
        """
        Finalize filesets and setup targets. Both should not be modified anymore afterwards.
        :return:
        """

        # Initialize Targets
        self._setup_targets()

    def set_target(self, target_name):
        if self._setup_finished:
            self.args.active_target = target_name
            target = getattr(self, self.default_fpga_target)
            if isinstance(target, FPGATarget):
                self.default_fpga_target = target_name
            elif isinstance(target, SimulationTarget):
                self.default_sim_target = target_name
        else:
            raise Exception(f'Setup is not finished yet. Please finalize setup before setting the active target.')

    def build(self):
        """
        Generate bitstream for FPGA target
        """

        # Check if project setup was finished
        self._check_setup()

        # Check if active target is an FPGA target
        target = getattr(self, self.default_fpga_target)
        if not isinstance(target, FPGATarget):
            raise Exception(f'Active Target is of wrong type, only FPGATarget is supported for this action')

        VivadoEmulation(target=target).build()
        statpro.statpro_update(statpro.FEATURES.anasymod_build_vivado)

    def emulate(self, server_addr=None):
        """
        Program bitstream to FPGA and run simulation/emulation on FPGA
        """

        if server_addr is None:
            server_addr = self.args.server_addr

        # Check if project setup was finished
        self._check_setup()

        # Check if active target is an FPGA target
        target = getattr(self, self.default_fpga_target)
        if not isinstance(target, FPGATarget):
            raise Exception(f'Active Target is of wrong type, only FPGATarget is supported for this action')

        # create sim result folders
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        if not os.path.exists(os.path.dirname(target.cfg.csv_path)):
            mkdir_p(os.path.dirname(target.cfg.csv_path))

        # run the emulation
        VivadoEmulation(target=target).run_FPGA(start_time=self.args.start_time, stop_time=self.args.stop_time, server_addr=server_addr)
        statpro.statpro_update(statpro.FEATURES.anasymod_emulate_vivado)

        # post-process results
        from anasymod.wave import ConvertWaveform
        ConvertWaveform(target=target)

    def launch(self, server_addr=None):
        """
        Program bitstream to FPGA, setup control infrastructure and wait for interactive commands.
        :param server_addr: Address of Vivado hardware server used for communication to FPGA board
        :return:
        """

        if server_addr is None:
            server_addr = self.args.server_addr

        # Check if project setup was finished
        self._check_setup()

        # Check if active target is an FPGA target
        target = getattr(self, self.default_fpga_target)
        if not isinstance(target, FPGATarget):
            raise Exception(f'Active Target is of wrong type, only FPGATarget is supported for this action')

        # create sim result folders
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        if not os.path.exists(os.path.dirname(target.cfg.csv_path)):
            mkdir_p(os.path.dirname(target.cfg.csv_path))

        # launch the emulation
        ctrl_handle = VivadoEmulation(target=target).launch_FPGA(server_addr=server_addr)
        statpro.statpro_update(statpro.FEATURES.anasymod_emulate_vivado)

        # Return ctrl handle for interactive control
        return ctrl_handle

        #ToDo: once recording via ila in interactive mode is finishe and caotured results were dumped into a file,
        #ToDo: the conversion step to .vcd needs to be triggered via some command

    def simulate(self, unit=None, id=None):
        """
        Run simulation on a pc target.
        """

        # check if setup is already finished, if not do so
        if not self._setup_finished:
            self.finish_setup()

        # Check if active target is a SimulationTarget
        target = getattr(self, self.default_sim_target)
        if not isinstance(target, SimulationTarget):
            raise Exception(f'Active Target is of wrong type, only SimulationTarget is supported for this action')

        # create sim result folder
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        # pick simulator
        sim_cls = {
            'icarus': IcarusSimulator,
            'vivado': VivadoSimulator,
            'xrun': XceliumSimulator
        }[self.args.simulator_name]

        # run simulation

        sim = sim_cls(target=target)

        if self.args.simulator_name == "xrun":
            sim.unit = unit
            sim.id = id

        sim.simulate()
        statpro.statpro_update(statpro.FEATURES.anasymod_sim + self.args.simulator_name)

    def probe(self, name, emu_time=False):
        """
        Probe specified signal. Signal will be stored in a numpy array.
        """

        # Check if project setup was finished
        self._check_setup()

        target = getattr(self, self.args.active_target)

        probeobj = self._setup_probeobj(target=target)

        return probeobj._probe(name=name, emu_time=emu_time)

    def probes(self):
        """
        Display all signals that were stored for specified target run (simulation or emulation)
        :return: list of signal names
        """

        # Check if project setup was finished
        self._check_setup()

        target = getattr(self, self.args.active_target)

        probeobj = self._setup_probeobj(target=target)

        return probeobj._probes()

    def preserve(self, wave):
        """
        This function preserve the stepping of the waveform wave
        :param wave: 2d numpy.ndarray
        :return: 2d numpy.ndarray
        """
        temp_data = None
        wave_step =[]

        for d in wave.transpose():
            if temp_data is not None:
                if d[1] != temp_data:
                    wave_step.append([d[0],temp_data]) #old value with same timestep to preserve stepping
            wave_step.append(d)
            temp_data = d[1]

        try:
            return np.array(wave_step, dtype='float').transpose()
        except:
            return np.array(wave_step, dtype='O').transpose()

    def view(self):
        """
        View results from selected target run.
        """

        # Check if project setup was finished
        self._check_setup()

        target = getattr(self, self.args.active_target)

        # pick viewer
        viewer_cls = {
            'gtkwave': GtkWaveViewer,
            'simvision': SimVisionViewer,
            'scansion': ScansionViewer
        }[self.args.viewer_name]

        # set config file location for GTKWave
        # TODO: clean this up; it's a bit messy...
        if isinstance(target, FPGATarget):
            gtkw_search_order = ['view_fpga.gtkw', 'view.gtkw']
        elif isinstance(target, SimulationTarget):
            gtkw_search_order = ['view_sim.gtkw', 'view.gtkw']
        else:
            gtkw_search_order = ['view.gtkw']

        for basename in gtkw_search_order:
            candidate_path = os.path.join(self.args.input, basename)
            if os.path.isfile(candidate_path):
                self._prj_cfg.gtkwave_config.gtkw_config = candidate_path
                break
        else:
            self._prj_cfg.gtkwave_config.gtkw_config = None

        # set config file location for SimVision
        self._prj_cfg.simvision_config.svcf_config = os.path.join(self.args.input, 'view.svcf')

        # run viewer
        viewer = viewer_cls(target=target)
        viewer.view()

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view

        -i, --input: Path to project root directory of the project that shall be opened and worked with.
            default=None

        --simulator_name: Simulator that shall be used for logic simulation.
            default=icarus for windows, xrun for linux

        --synthesizer_name: Synthesis engine that shall be used for FPGA synthesis.
            default=vivado

        --viewer_name: Waveform viewer that shall be used for viewing result waveforms.
            default=gtkwave for windows, simvision for linux

        --active_target: Target that shall be actively used.
            default='sim'

        --launch: Launch the FPGA simulation/emulation by programming the bitstream and preparing the control interface for interactive use.

        --sim: Execute logic simulation for selected simulation target.

        --view: Open results in selected waveform viewer.

        --build: Synthesize, run P&R and generate bitstream for selected target.

        --emulate: Execute FPGA run for selected target.

        --start_time: Start time for FPGA simulation.
            default=0

        --server_addr: Hardware server address for FPGA simulation. This is necessary for connecting to a vivado
            hardware server from linux, that was setup under windows.
            default=None

        --stop_time: Stop time for FPGA simulation
            default=None

        --preprocess_only: For icarus only, this will nur run the simulation, but only compile the netlist.

        """

        parser = ArgumentParser()

        # if the Cadence tools are available, use those as defaults instead
        try:
            x = XceliumConfig(None).xrun
            default_simulator_name = 'xrun' if x is not None else 'icarus'
        except:
            default_simulator_name = 'icarus'

        try:
            s = SimVisionConfig(None).simvision
            default_viewer_name = 'simvision' if s is not None else 'gtkwave'
        except:
            default_viewer_name = 'gtkwave'
            pass


        parser.add_argument('-i', '--input', type=str, default=None)
        parser.add_argument('--simulator_name', type=str, default=default_simulator_name)
        parser.add_argument('--synthesizer_name', type=str, default='vivado')
        parser.add_argument('--viewer_name', type=str, default=default_viewer_name)
        parser.add_argument('--active_target', type=str, default=None)
        parser.add_argument('--unit', type=str, default=None)
        parser.add_argument('--id', type=str, default=None)
        parser.add_argument('--sim', action='store_true')
        parser.add_argument('--view', action='store_true')
        parser.add_argument('--build', action='store_true')
        parser.add_argument('--emulate', action='store_true')
        parser.add_argument('--launch', action='store_true')
        parser.add_argument('--start_time', type=float, default=0)
        parser.add_argument('--server_addr', type=str, default=None)
        parser.add_argument('--stop_time', type=float, default=None)
        parser.add_argument('--preprocess_only', action='store_true')

        self.args, _ = parser.parse_known_args()

    def _setup_targets(self):
        """
        Setup targets for project.
        This may differ from one project to another and needs customization.
        1. Create target object for each target that is supported in project
        2. Assign filesets to all target objects of the project
        """

        # Populate the fileset dict which will be used to copy data to target object and store in filesets variable
        self.filesets.populate_fileset_dict()
        filesets = self.filesets.fileset_dict

        #######################################################
        # Create and setup simulation target
        #######################################################

        self.sim = SimulationTarget(prj_cfg=self._prj_cfg, plugins=self._plugins, name=r"sim")
        self.sim.assign_fileset(fileset=filesets['default'])
        if 'sim' in filesets:
            self.sim.assign_fileset(fileset=filesets['sim'])



        # Update simulation target specific configuration
        self.sim.cfg.update_config(subsection=r"sim")
        self.sim.update_structure_config()
        #ToDo: currently structure generation is only necessary for FPGA simulation, in future at least signals selected in probing file should automatically be included in vcd file
        if not self.sim.cfg.custom_top:
            print('!!! gen_structure for simulation target')
            self.sim.setup_ctrl_ifc()
            self.sim.gen_structure()
        self.sim.set_tstop()
        self.sim.setup_vcd()

        #######################################################
        # Create and setup FPGA target
        #######################################################
        self.fpga = FPGATarget(prj_cfg=self._prj_cfg, plugins=self._plugins, name=r"fpga")
        self.fpga.assign_fileset(fileset=filesets['default'])
        if 'fpga' in filesets:
            self.fpga.assign_fileset(fileset=filesets['fpga'])

        # Update simulation target specific configuration
        self.fpga.cfg.update_config(subsection=r"fpga")
        self.fpga.update_structure_config()
        # Instantiate Simulation ControlInfrastructure Interface
        # ToDo: This should only be executed for FPGA simulation!
        if not self.fpga.cfg.custom_top:
            print('!!! gen_structure for FPGA target')
            self.fpga.setup_ctrl_ifc()
            self.fpga.gen_structure()
        self.fpga.set_tstop()

        # Set indication that project setup is complete
        self._setup_finished = True

    def _setup_probeobj(self, target: Union[FPGATarget, SimulationTarget]):
        """
        Check if the requested probe obj in the target object already exists, in not create one.
        Return the probe object.

        :param target: Target that signals shall be extracted from
        :return: probe object that was selected in target object
        """

        # specify probe obj name, specific to selected simulator/synthesizer
        if isinstance(target, FPGATarget):
            target_name = f"prb_{self.args.synthesizer_name}"
        elif isinstance(target, SimulationTarget):
            target_name = f"prb_{self.args.simulator_name}"
        else:
            raise ValueError(f"Provided target type:{target} is not supported")

        # check if probe obj is already existing, if not, instantiate one

        #ToDo: In future it should be also possible to instantiate different probe objects, depending on data format that shall be read in
        if target_name not in target.probes.keys():
            from anasymod.probe import ProbeVCD
            target.probes[target_name] = ProbeVCD(target=target)

        return target.probes[target_name]

    def _check_setup(self):
        """
        Check if the targets were already created for the project. If not, throw an error.

        :return:
        """

        if not self._setup_finished:
            raise ValueError("The project setup changed after data aquisition; Data might be out of sync!")

def main():
    Analysis(op_mode='commandline')

if __name__ == '__main__':
    main()
