import os
import os.path
import json

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

from importlib import import_module

class Analysis():
    """
    This is the top user Class that shall be used to exercise anasymod.
    """
    def __init__(self):

        # Parse command line arguments
        self.args = None
        self._parse_args()

        # expand path of input and output directories relative to analysis.py
        self.args.input = get_full_path(self.args.input)

        # Load config file
        try:
            self.cfg_file = json.load(open(os.path.join(self.args.input, 'prj_config.json'), 'r'))
        except:
            self.cfg_file = None
            print(f"Warning: no config file was fround for the project, expected path is: {os.path.join(self.args.input, 'prj_config.json')}")

        # Initialize project config
        self.cfg = EmuConfig(root=self.args.input, cfg_file=self.cfg_file)

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

        # Initialize Filesets
        self._setup_filesets()

        # Initialize Targets
        self._setup_targets()

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

    def build(self, target: FPGATarget):
        """
        Generate bitstream for FPGA target
        """
        build = VivadoBuild(cfg=self.cfg, target=target)
        build.build()

    def emulate(self, target: FPGATarget):
        """
        Run bitstream on FPGA
        """

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

    def probe(self):
        """
        Probe specified signal. Signal will be stored in a numpy array.
        """
        pass

    def view(self, target: Target):
        """
        View results from selected target run.
        """

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

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()

        parser.add_argument('-i', '--input', type=str, default=get_from_module('anasymod', 'tests', 'filter'))
        parser.add_argument('--simulator_name', type=str, default='icarus' if os.name == 'nt' else 'xcelium')
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
            self.filesets._defines += plugin.dump_defines()
            self.filesets._verilog_sources += plugin.dump_verilog_sources()
            self.filesets._verilog_headers += plugin.dump_verilog_headers()
            self.filesets._vhdl_sources += plugin.dump_vhdl_sources()

        # Add custom source and define objects here e.g.:
        # self.filesets.add_source(source=VerilogSource())
        # self.filesets.add_define(define=Define())
        config_path = os.path.join(self.args.input, 'source.config')

        self.filesets.add_source(source=VerilogSource(files=get_from_module('anasymod', 'verilog', '*.sv'), config_path=config_path))

        self.filesets.add_define(define=Define(name='CLK_MSDSL', value='top.emu_clk'))
        self.filesets.add_define(define=Define(name='RST_MSDSL', value='top.emu_rst'))
        self.filesets.add_define(define=Define(name='DEC_THR_MSDSL', value='top.emu_dec_thr'))

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

if __name__ == '__main__':
    analysis = Analysis()
