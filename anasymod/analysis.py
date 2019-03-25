import os
import os.path
import json
import numpy as np

from argparse import ArgumentParser

from anasymod.config import EmuConfig
from anasymod.sim.vivado import VivadoSimulator
from anasymod.sim.icarus import IcarusSimulator
from anasymod.sim.xcelium import XceliumSimulator
from anasymod.viewer.gtkwave import GtkWaveViewer
from anasymod.viewer.simvision import SimVisionViewer
from anasymod.build import VivadoBuild
from anasymod.files import get_full_path, get_from_module
from anasymod.sources import VerilogSource, VerilogHeader, VHDLSource, Sources
from anasymod.filesets import Filesets
from anasymod.defines import Define
from anasymod.targets import SimulationTarget, FPGATarget, Target
from anasymod.enums import ConfigSections
from anasymod.files import mkdir_p
from anasymod.util import read_config, update_config
from anasymod.probe import ProbeCSV, ProbeVCD
from typing import Union

from importlib import import_module

class Analysis():
    """
    This is the top user Class that shall be used to exercise anasymod.
    """
    def __init__(self, input=None, build_root=None, simulator_name=None, synthesizer_name=None, viewer_name=None, preprocess_only=None, op_mode=None):

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

        # Load config file
        try:
            self.cfg_file = json.load(open(os.path.join(self.args.input, 'prj_config.json'), 'r'))
        except:
            self.cfg_file = None
            print(f"Warning: no config file was fround for the project, expected path is: {os.path.join(self.args.input, 'prj_config.json')}")

        # Initialize project config
        self.cfg = EmuConfig(root=self.args.input, cfg_file=self.cfg_file, build_root=build_root)

        # Initialize Plugins
        self._plugins = []
        for plugin in self.cfg.cfg['plugins']:
            try:
                i = import_module(f"plugin.{plugin}")
                inst = i.CustomPlugin(cfg_file=self.cfg_file, prj_root=self.args.input, build_root=self.cfg.build_root)
                self._plugins.append(inst)
                setattr(self, inst._name, inst)
            except:
                raise KeyError(f"Could not process plugin:{plugin} properly! Check spelling")

        # Check which mode is used to run, in case of commandline mode, besided setting up the class, also argument will be executed
        if op_mode in ['commandline']:
            print(f"Running in commandline mode.")

            # Finalize project setup, no more modifications of filesets and targets after that!!!
            self.finish_setup()

            ###############################################################
            # Set options from to command line arguments
            ###############################################################

            self.cfg.preprocess_only = self.args.preprocess_only

            ###############################################################
            # Execute actions according to command line arguments
            ###############################################################

            # generate bitstream
            if self.args.build:
                self.build(target=getattr(self, self.args.fpga_target))

            # run FPGA if desired
            if self.args.emulate:
                self.emulate(target=getattr(self, self.args.fpga_target))

            # run simulation if desired
            if self.args.sim or self.args.preprocess_only:
                self.simulate(target=getattr(self, self.args.sim_target))

            # view results if desired
            if self.args.view and (self.args.sim or self.args.preprocess_only):
                self.view(target=getattr(self, self.args.sim_target))

            if self.args.view and self.args.emulate:
                self.view(target=getattr(self, self.args.fpga_target))

##### Functions exposed for user to exercise on Analysis Object

    def finish_setup(self):
        """
        Finalize filesets and setup targets. Both should not be modified anymore afterwards.
        :return:
        """
        # Initialize Filesets
        self._setup_filesets()

        # Initialize Targets
        self._setup_targets()

        # Set indication that project setup is complete
        self._setup_finished = True

    def build(self, target: FPGATarget):
        """
        Generate bitstream for FPGA target
        """

        # Check if project setup was finished
        self._check_setup()

        build = VivadoBuild(cfg=self.cfg, target=target)
        build.build()

    def emulate(self, target: FPGATarget):
        """
        Run bitstream on FPGA
        """

        # Check if project setup was finished
        self._check_setup()

        # create sim result folders
        if not os.path.exists(os.path.dirname(target.cfg['vcd_path'])):
            mkdir_p(os.path.dirname(target.cfg['vcd_path']))

        if not os.path.exists(os.path.dirname(target.cfg['csv_path'])):
            mkdir_p(os.path.dirname(target.cfg['csv_path']))

        # create VivadoBuild object if necessary (this does not actually build the design)
        if r"build" not in locals():
            build = VivadoBuild(cfg=self.cfg, target=target)

        # run the emulation
        build.run_FPGA()

        # post-process results
        from anasymod.wave import ConvertWaveform
        ConvertWaveform(cfg=self.cfg, target=target)

    def simulate(self, target: SimulationTarget):
        """
        Run simulation on a pc target.
        """

        # check if setup is already finished, if not do so
        if not self._setup_finished:
            self.finish_setup()

        # create sim result folder
        if not os.path.exists(os.path.dirname(target.cfg['vcd_path'])):
            mkdir_p(os.path.dirname(target.cfg['vcd_path']))

        # pick simulator
        sim_cls = {
            'icarus': IcarusSimulator,
            'vivado': VivadoSimulator,
            'xrun': XceliumSimulator
        }[self.args.simulator_name]

        # run simulation
        sim = sim_cls(cfg=self.cfg, target=target)
        sim.simulate()

    def probe(self, target: Union[FPGATarget, SimulationTarget], name, emu_time=False):
        """
        Probe specified signal. Signal will be stored in a numpy array.
        """

        # Check if project setup was finished
        self._check_setup()

        probeobj = self._setup_probeobj(target=target)

        return probeobj._probe(name=name, emu_time=emu_time)

    def probes(self, target: Union[FPGATarget, SimulationTarget]):
        """
        Display all signals that were stored for specified target run (simulation or emulation)
        :param target: Target for which all stored signals will be displayed
        :return: list of signal names
        """

        # Check if project setup was finished
        self._check_setup()

        probeobj = self._setup_probeobj(target=target)

        return probeobj._probes()

    def view(self, target: Target):
        """
        View results from selected target run.
        """

        # Check if project setup was finished
        self._check_setup()

        # pick viewer
        viewer_cls = {
            'gtkwave': GtkWaveViewer,
            'simvision': SimVisionViewer
        }[self.args.viewer_name]

        # set config file location
        self.cfg.gtkwave_config.gtkw_config = os.path.join(self.args.input, 'view.gtkw')
        self.cfg.simvision_config.svcf_config = os.path.join(self.args.input, 'view.svcf')

        # run viewer
        viewer = viewer_cls(cfg=self.cfg, target=target)
        viewer.view()

    def compress(self, wave=np.ndarray):
        """
        This function compress the waveform wave and removes redundant values
        :param wave: 2d numpy.ndarray
        :return: 2d numpy.ndarray
        """
        temp_data = ""
        temp_time = ""
        compressed =[]

        for d in wave.transpose():
            if d[0] == temp_time:
                compressed.pop()
                compressed.append(d)
            else:
                if d[1] != temp_data:
                    if temp_data != "":
                        compressed.append([temp_time, temp_data])
                    compressed.append(d)
            temp_data = d[1]
            temp_time = d[0]
        # check if last value was taken otherwise append it
        if wave.transpose()[-1][0] != compressed[-1][0]:
            compressed.append(wave.transpose()[-1])
        return np.array(compressed, dtype='float').transpose()


##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()

        parser.add_argument('-i', '--input', type=str, default=get_from_module('anasymod', 'tests', 'filter'))
        parser.add_argument('--simulator_name', type=str, default='icarus' if os.name == 'nt' else 'xcelium')
        parser.add_argument('--synthesizer_name', type=str, default='vivado')
        parser.add_argument('--viewer_name', type=str, default='gtkwave' if os.name == 'nt' else 'simvision')
        parser.add_argument('--sim_target', type=str, default='sim')
        parser.add_argument('--fpga_target', type=str, default='fpga')
        parser.add_argument('--sim', action='store_true')
        parser.add_argument('--view', action='store_true')
        parser.add_argument('--build', action='store_true')
        parser.add_argument('--emulate', action='store_true')
        parser.add_argument('--preprocess_only', action='store_true')

        self.args, _ = parser.parse_known_args()

    def _setup_filesets(self):
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

        self.filesets.add_source(source=VerilogSource(files=get_from_module('anasymod', 'verilog', '*.sv'), config_path=config_path))

        self.filesets.add_define(define=Define(name='CLK_MSDSL', value='top.emu_clk'))
        self.filesets.add_define(define=Define(name='RST_MSDSL', value='top.emu_rst'))
        self.filesets.add_define(define=Define(name='DEC_THR_MSDSL', value='top.emu_dec_thr'))
        self.filesets.add_define(define=Define(name='DEC_BITS_MSDSL', value=self.cfg.cfg['dec_bits']))

        self.filesets.add_source(source=VerilogSource(files=os.path.join(self.args.input, 'tb.sv'), config_path=config_path))

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

        self.sim = SimulationTarget(prj_cfg=self.cfg, name=r"sim")
        self.sim.assign_fileset(fileset=filesets['default'])
        if 'sim' in filesets:
            self.sim.assign_fileset(fileset=filesets['sim'])

        # Update simulation target specific configuration
        self.sim.cfg = update_config(cfg=self.sim.cfg, config_section=read_config(cfg_file=self.cfg_file, section=ConfigSections.TARGET, subsection=r"sim"))
        self.sim.set_tstop()
        self.sim.setup_vcd()

        #######################################################
        # Create and setup FPGA target
        #######################################################
        self.fpga = FPGATarget(prj_cfg=self.cfg, name=r"fpga")
        self.fpga.assign_fileset(fileset=filesets['default'])
        if 'fpga' in filesets:
            self.fpga.assign_fileset(fileset=filesets['fpga'])

        # Update simulation target specific configuration
        self.fpga.cfg = update_config(cfg=self.fpga.cfg, config_section=read_config(cfg_file=self.cfg_file, section=ConfigSections.TARGET, subsection=r"fpga"))
        self.fpga.set_tstop()

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
            target.probes[target_name] = ProbeVCD(prj_config=self.cfg, target=target)

        return target.probes[target_name]

    def _check_setup(self):
        """
        Check if the targets were already created for the project. If not, throw an error.
        :return:
        """
        if not self._setup_finished:
            raise ValueError("The project setup changed after data aquisition; Data might be out of sync!")





if __name__ == '__main__':
    analysis = Analysis(op_mode='commandline')
