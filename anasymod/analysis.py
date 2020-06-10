import shutil, zipfile, filecmp, errno
import os.path
import yaml
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
from anasymod.emu.xsct_emu import XSCTEmulation
from anasymod.files import get_full_path, get_from_anasymod, mkdir_p
from anasymod.sources import *
from anasymod.filesets import Filesets
from anasymod.defines import Define
from anasymod.targets import CPUTarget, FPGATarget
from anasymod.enums import ConfigSections
from anasymod.utils import statpro
from anasymod.wave import ConvertWaveform
from anasymod.plugins import Plugin
from typing import Union
from importlib import import_module

class Analysis():
    """
    This is the top user Class that shall be used to exercise anasymod.
    """
    def __init__(self, input=None, build_root=None, simulator_name=None,
                 synthesizer_name=None, viewer_name=None, preprocess_only=None,
                 op_mode=None, active_target=None):

        # Parse command line arguments
        self.args = None
        self._parse_args()

        # Initialize attributes
        self.float_type = False # Defines which data type is used for functional models; default is fixed-point
        self._plugin_args = {} # Namespace object including all options set for generators

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

        # Load config file
        self.cfgfile_path = os.path.join(self.args.input, 'prj.yaml')

        if os.path.isfile(self.cfgfile_path):
            try:
                self.cfg_file = yaml.safe_load(open(self.cfgfile_path, "r"))
            except yaml.YAMLError as exc:
                raise Exception(exc)
        else:
            self.cfg_file = None
            print(f"Warning: no config file was found for the project, expected path is: {self.cfgfile_path}")

        # Initialize Targets
        self.act_fpga_target = 'fpga'
        self.fpga_targets = [self.act_fpga_target]
        try:
            for custom_target in self.cfg_file[ConfigSections.FPGA_TARGET].keys():
                if custom_target not in self.fpga_targets:
                    self.fpga_targets.append(custom_target)
        except:
            pass

        self.act_cpu_target = 'sim'
        self.cpu_targets = [self.act_cpu_target]
        try:
            for custom_target in self.cfg_file[ConfigSections.CPU_TARGET].keys():
                if custom_target not in self.cpu_targets:
                    self.cpu_targets.append(custom_target)
        except:
            pass

        # Initialize dict for tracking, which targets are already setup.
        self._setup_finished = {}
        for target in self.cpu_targets + self.fpga_targets:
            self._setup_finished[target] = False

        self.project_sources_finalized = False

        # Initialize project config
        self._prj_cfg = EmuConfig(root=self.args.input, cfg_file=self.cfg_file, active_target=self.args.active_target, build_root=build_root)

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

        #Set active target
        self.set_target(self.args.active_target)

        # Initialize filesets, those can later be modified via the add_sources function
        self._setup_filesets()

        # Check which mode is used to run, in case of commandline mode, besides setting up the class, also argument will be processed and executed
        if op_mode in ['commandline']:
            print(f"Running in commandline mode.")


            ###############################################################
            # Process command line arguments for plugins
            ###############################################################

            for plugin in self._plugins:
                # Parse command line arguments and execute all actions for each plugin
                plugin._parse_args()
                args = plugin._return_args()

                for arg in args.__dict__:
                    plugin.set_option(name=arg, value= args.__dict__[arg]) # Set options for the generator according to commandline arguments
                    self._plugin_args[arg] = args.__dict__[arg]

            # Set float type to true, in case floating-point data types are used during simulation.
            # This is needed when converting result files.
            if 'float' in self._plugin_args.keys():
                self.float_type = self._plugin_args['float']

            ###############################################################
            # Set options from to command line arguments
            ###############################################################

            self._prj_cfg.cfg.preprocess_only = self.args.preprocess_only

            ###############################################################
            # Execute actions according to command line arguments
            ###############################################################

            # generate source code, e.g. functional models via msdsl
            if self.args.models:
                self.gen_sources()

            # generate bitstream
            if self.args.build:
                self.set_target(self.act_fpga_target)
                self.build()

            # run FPGA if desired
            if self.args.emulate:
                self.set_target(self.act_fpga_target)
                self.emulate()

            # launch FPGA if desired
            if self.args.launch:
                self.set_target(self.act_fpga_target)
                self.launch()

            # run simulation if desired
            if self.args.sim or self.args.preprocess_only:
                self.set_target(self.act_cpu_target)
                self.simulate(unit=self.args.unit, id=self.args.id)

            # view results if desired
            if self.args.view and (self.args.sim or self.args.preprocess_only):
                self.set_target(self.act_cpu_target)
                self.view()

            if self.args.view and self.args.emulate:
                self.set_target(self.act_fpga_target)
                self.view()

##### Functions exposed for user to exercise on Analysis Object

    def add_sources(self, sources: Union[Sources, Define, list]):
        """
        Function to add sources or defines to filesets. This will also retrigger fileset dict population

        :param sources: Individual source or list of sources, that shall be added to filesets
        """

        if not isinstance(sources, list):
            sources = [sources]
        for source in sources:
            if isinstance(source, VerilogSource):
                self.filesets._verilog_sources.append(source)
            elif isinstance(source, VerilogHeader):
                self.filesets._verilog_headers.append(source)
            elif isinstance(source, VHDLSource):
                self.filesets._vhdl_sources.append(source)
            elif isinstance(source, Define):
                self.filesets._defines.append(source)
            elif isinstance(source, EDIFFile):
                self.filesets._edif_files.append(source)
            elif isinstance(source, FirmwareFile):
                self.filesets._firmware_files.append(source)
            elif isinstance(source, XCIFile):
                self.filesets._xci_files.append(source)
            elif isinstance(source, XDCFile):
                self.filesets._xdc_files.append(source)
            elif isinstance(source, MEMFile):
                self.filesets._mem_files.append(source)
            elif isinstance(source, BDFile):
                self.filesets._bd_files.append(source)
            elif isinstance(source, IPRepo):
                self.filesets._ip_repos.append(source)
            elif isinstance(source, FunctionalModel):
                source.set_gen_files_path(hdl_dir_root=self._prj_cfg.build_root_functional_models)
                self.filesets._functional_models.append(source)
            else:
                print(f'WARNING: Provided source:{source} does not have a valid type, skipping this command!')

        self.project_sources_finalized = False

    def set_target(self, target_name):
        """
        Changes the domainspecific active target to target_name, e.g. the active CPU target to target_name.

        :param target_name: name of target, that shall be set as active for the respective domain.
        """
        self.args.active_target = target_name
        if self.args.active_target in self.fpga_targets:
            self.act_fpga_target = self.args.active_target
        elif self.args.active_target in self.cpu_targets:
            self.act_cpu_target = self.args.active_target
        else:
            raise Exception(f'Active target:{self.args.active_target} is not available for project, please declare the target first in the project configuration.')

        self._prj_cfg._update_build_root(active_target=target_name)

    def set_generator_option(self, generator, name, value):
        """
        Set an option for a source code generator that is added to the project, e.g. msdsl.

        :param generator:   Name of the generator for which an option shall be set. The name needs to be identical to
                            the one provided in the prj.yaml file.
        :param name:        Option name that shall be set
        :param value:       Value the option shall be set to
        """

        valid_plugin = None
        """ : type : Plugin"""

        for plugin in self._plugins:
            if generator == plugin._name:
                valid_plugin = plugin

        # Check if any valid plugin was selected
        if not valid_plugin:
            raise Exception(f'ERROR: Provided plugin/s:{generator} were not registered in the project configuration!')

        # Call the plugin set_option function to propagate the option change
        valid_plugin.set_option(name=name, value=value)

        # Store the option change in analysis object
        self._plugin_args[name] = value

        # In case the float option is set, also update the float_type instance attribute
        # ToDo: A more generic approach how to deal with this kind of change might be needed -> querry self.plugin_args dict instead
        if name == 'float':
            self.float_type = value

    def gen_sources(self, plugins=None):
        """
        Run all plugin generators added to the project ro generate source code. If parameter plugin is set to None,
        all generators will be run. Otherwise only the list of plugins provided will be run.

        :param plugin: List of plugin generator names that shall be run.
        """

        valid_plugins = []
        if plugins is None:
            valid_plugins = self._plugins
        elif isinstance(plugins, str):
            for prj_plugin in self._plugins:
                if plugins == prj_plugin._name:
                    valid_plugins = [prj_plugin]

        elif isinstance(plugins, list):
            for prj_plugin in self._plugins:
                for plugin in plugins:
                    if plugin == prj_plugin._name:
                        valid_plugins.append(prj_plugin)
        else:
            raise Exception(f'Provided data type for parameter plugins is not supported. Expects list, given:{type(plugins)}')

        # Check if any valid plugin was selected
        # TODO: does this need to be more selective? (What happens if we don't want any plugins?)
        if not valid_plugins:
            raise Exception(f'ERROR: Provided plugin/s:{plugins} were not registered in the project configuration!')

        # ToDo: currently, the generator API is under construction, which is why this only works for msdsl right now
        for plugin in valid_plugins:
            if plugin._name == 'msdsl':  # Pass generator inputs to plugin - note this is custom for each plugin
                if not self.filesets._functional_models:
                    # Use default functional models object for generation
                    func_model_default = FunctionalModel(files=os.path.join(self.args.input, 'gen.py'), config_path='',
                                                         name='main')
                    func_model_default.expand_paths()
                    func_model_default.set_gen_files_path(hdl_dir_root=self._prj_cfg.build_root_functional_models)
                    self.filesets._functional_models.append(func_model_default)

            plugin._set_generator_sources(generator_sources=self.filesets._functional_models)
            plugin.models()

    def build(self):
        """
        Generate bitstream for FPGA target
        """

        shutil.rmtree(self._prj_cfg.build_root) # Remove target specific build dir to make sure there is no legacy
        mkdir_p(self._prj_cfg.build_root)
        self._setup_targets(target=self.act_fpga_target, gen_structures=True)

        # Check if active target is an FPGA target
        target = getattr(self, self.act_fpga_target)

        VivadoEmulation(target=target).build()
        statpro.statpro_update(statpro.FEATURES.anasymod_build_vivado)

    def build_firmware(self, *args, **kwargs):
        # create target object, but don't generate instrumentation structure again in case target object does not exist yet
        if not hasattr(self, self.act_fpga_target):
            self._setup_targets(target=self.act_fpga_target)

        # check if bitstream was generated for active fpga target
        target = getattr(self, self.act_fpga_target)
        if not os.path.isfile(getattr(target, 'bitfile_path')):
            raise Exception(f'Bitstream for active FPGA target was not generated beforehand; please do so before running emulation.')

        # build the firmware
        XSCTEmulation(target=target).build(*args, **kwargs)

    def emulate(self, server_addr=None):
        """
        Program bitstream to FPGA and run simulation/emulation on FPGA

        :param server_addr: Address of Vivado hardware server used for communication to FPGA board
        """

        if server_addr is None:
            server_addr = self.args.server_addr

        # create target object, but don't generate instrumentation structure again in case target object does not exist yet
        if not hasattr(self, self.act_fpga_target):
            self._setup_targets(target=self.act_fpga_target)

        # check if bitstream was generated for active fpga target
        target = getattr(self, self.act_fpga_target)
        if not os.path.isfile(getattr(target, 'bitfile_path')):
            raise Exception(f'Bitstream for active FPGA target was not generated beforehand; please do so before running emulation.')

        # create sim result folders
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        if not os.path.exists(os.path.dirname(target.result_path_raw)):
            mkdir_p(os.path.dirname(target.result_path_raw))

        # run the emulation
        VivadoEmulation(target=target).run_FPGA(
            start_time=self.args.start_time, stop_time=self.args.stop_time,
            server_addr=server_addr
        )
        statpro.statpro_update(statpro.FEATURES.anasymod_emulate_vivado)

        # post-process results
        ConvertWaveform(
            result_path_raw=target.result_path_raw,
            result_type_raw=target.cfg.result_type_raw,
            result_path=target.cfg.vcd_path,
            str_cfg=target.str_cfg,
            float_type=self.float_type,
            dt_scale=self._prj_cfg.cfg.dt_scale
        )

    def program_firmware(self, *args, **kwargs):
        # create target object, but don't generate instrumentation structure again in case target object does not exist yet
        if not hasattr(self, self.act_fpga_target):
            self._setup_targets(target=self.act_fpga_target)

        # check if bitstream was generated for active fpga target
        target = getattr(self, self.act_fpga_target)
        if not os.path.isfile(getattr(target, 'bitfile_path')):
            raise Exception(f'Bitstream for active FPGA target was not generated beforehand; please do so before running emulation.')

        # build the firmware
        XSCTEmulation(target=target).program(*args, **kwargs)

    def launch(self, server_addr=None, debug=False):
        """
        Program bitstream to FPGA, setup control infrastructure and wait for interactive commands.

        :param server_addr: Address of Vivado hardware server used for communication to FPGA board
        :param debug: Enable or disable debug mode when running an interactive simulation
        """

        if server_addr is None:
            server_addr = self.args.server_addr

        # create target object, but don't generate instrumentation structure again in case target object does not exist yet
        if not hasattr(self, self.act_fpga_target):
            self._setup_targets(target=self.act_fpga_target, debug=debug)

        # check if bitstream was generated for active fpga target
        target = getattr(self, self.act_fpga_target)
        if not os.path.isfile(getattr(target, 'bitfile_path')):
            raise Exception(f'Bitstream for active FPGA target was not generated beforehand; please do so before running emulation.')

        # create sim result folders
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        if not os.path.exists(os.path.dirname(target.result_path_raw)):
            mkdir_p(os.path.dirname(target.result_path_raw))

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

        shutil.rmtree(self._prj_cfg.build_root) # Remove target speciofic build dir to make sure there is no legacy
        mkdir_p(self._prj_cfg.build_root)
        self._setup_targets(target=self.act_cpu_target, gen_structures=True)

        target = getattr(self, self.act_cpu_target)

        # create sim result folder
        if not os.path.exists(os.path.dirname(target.cfg.vcd_path)):
            mkdir_p(os.path.dirname(target.cfg.vcd_path))

        if not os.path.exists(os.path.dirname(target.result_path_raw)):
            mkdir_p(os.path.dirname(target.result_path_raw))

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

        # post-process results
        ConvertWaveform(result_path_raw=target.result_path_raw,
                        result_type_raw=target.cfg.result_type_raw,
                        result_path=target.cfg.vcd_path,
                        str_cfg=target.str_cfg,
                        float_type=self.float_type,
                        debug=self._prj_cfg.cfg.cpu_debug_mode)

    def probe(self, name, emu_time=False):
        """
        Probe specified signal. Signal will be stored in a numpy array.
        """

        probeobj = self._setup_probeobj(target=getattr(self, self.args.active_target))
        return probeobj._probe(name=name, emu_time=emu_time)

    def probes(self):
        """
        Display all signals that were stored for specified target run (simulation or emulation)
        :return: list of signal names
        """

        probeobj = self._setup_probeobj(target=getattr(self, self.args.active_target))
        return probeobj._probes()

    def preserve(self, wave):
        """
        This function preserve the stepping of the waveform 'wave'. This is necessary, if limit checks should be
        conducted on the waveform later on.

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
            #return np.array(wave_step, dtype='float').transpose()
            return np.array(wave_step, dtype='O').transpose()
        except:
            return np.array(wave_step, dtype='O').transpose()

    def view(self):
        """
        View results from selected target run.
        """

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
        elif isinstance(target, CPUTarget):
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

    def pack_results(self, target=None):
        """
        Pack target-specific build folder into a zip and store it in project root directory. All project related .yaml
        config files will also be stored in the bundle.

        :param target: Specify target, that shall be stored, by default the currently active target will be used.
        """

        # Specify target-specific paths
        if target is None:
            build_target_root = self._prj_cfg.build_root
            clks_file_path = getattr(getattr(getattr(self, self.args.active_target), 'str_cfg'), '_clks_file_path')
            simctrl_file_path = getattr(getattr(getattr(self, self.args.active_target), 'str_cfg'), '_simctrl_file_path')
        elif target in self.fpga_targets + self.cpu_targets:
            self._prj_cfg._update_build_root(active_target=target)
            build_target_root = self._prj_cfg.build_root
            clks_file_path = getattr(getattr(getattr(self, target), 'str_cfg'), '_clks_file_path')
            simctrl_file_path = getattr(getattr(getattr(self, target), 'str_cfg'), '_simctrl_file_path')
            self._prj_cfg._update_build_root(active_target=self.args.active_target)
        else:
            raise Exception(f'ERROR: Provided target:{target} does not exist in current project!')

        # Copy any .yaml config files from project to target-specific build root.
        config_files = [self.cfgfile_path, clks_file_path, simctrl_file_path]
        config_files.append(config for config in self.filesets._config_paths)

        for config_file in config_files:
            if os.path.isfile(config_file):
                dst = os.path.join(build_target_root, 'configs', os.path.relpath(config_file, self.args.input))
                try:
                    shutil.copyfile(config_file, dst)
                except:
                    raise Exception(f'ERROR: File:{config_file} could not be copied to:{dst}!')

        # Zip target-specific build folder and copy to project root
        shutil.make_archive(base_name=os.path.basename(self.args.input) + '_!_' + str(target if target is not None else self.args.active_target) + '_!_bundle',
                            base_dir=build_target_root,
                            format='zip',
                            root_dir=self.args.input)

    def unpack_results(self, bundle_path, force=False):
        """
        Unpack target-specific result bundle to build root, in order to view results or do further post-processing
        without having to run simulations again. In case force attribute is set to true, all .yaml config files stored
        in bundle will copied to project root and overwrite existing ones.

        :param bundle_path: Path to result bundle
        :param force: Set this attribute to True to make sure .yaml configs in bundle will replace currently existing ones.
        """

        # Unpack zip to target-specific root directory, deleting folder in case it already existed
        target = os.path.basename(bundle_path).split('_!_')[1]
        build_target_root = os.path.join(self.args.input, 'build', target)

        if os.path.exists(build_target_root):
            shutil.rmtree(build_target_root)

        with zipfile.ZipFile(bundle_path, "r") as zip_ref:
            zip_ref.extractall(path=build_target_root)

        # Compare if config .yaml files are different in bundle and current project
        bundle_config_files = []
        [bundle_config_files.append(config_file) for config_file in os.path.join(build_target_root, 'configs')]

        if target in self.fpga_targets + self.cpu_targets:
            self._prj_cfg._update_build_root(active_target=target)
            clks_file_path = getattr(getattr(getattr(self, str(target)), 'str_cfg'), '_clks_file_path')
            simctrl_file_path = getattr(getattr(getattr(self, str(target)), 'str_cfg'), '_simctrl_file_path')
            self._prj_cfg._update_build_root(active_target=self.args.active_target)
        else:
            raise Exception(f'ERROR: Provided target:{target} does not exist in current project!')

        orig_config_files = [self.cfgfile_path, clks_file_path, simctrl_file_path]
        orig_config_files.append(config for config in self.filesets._config_paths)

        for orig_config_file in orig_config_files:
            exists = False
            for bundle_config_file in bundle_config_files:
                if os.path.basename(orig_config_file) == os.path.basename(bundle_config_file):
                    exists = True
                    if not filecmp.cmp(orig_config_file, bundle_config_file):
                        print(f'WARNING: Config:{os.path.basename(orig_config_file)} does not match with config in bundle, project setup changed!')
                    if force:  # Depending on force flag overwrite config .yaml files in case they differ from the ones in current project
                        shutil.rmtree(orig_config_file)
                        try:
                            shutil.copyfile(bundle_config_file, orig_config_file)
                        except:
                            raise Exception(f'ERROR: File:{bundle_config_file} could not be copied to:{orig_config_file}!')
            if not exists:
                    print(f'WARNING: Config file:{os.path.basename(orig_config_file)} does not exist in bundle, project setup changed!')

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

        --models: Generate functional models for selected project.

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
        parser.add_argument('--active_target', type=str, default='sim')
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
        parser.add_argument('--models', action='store_true')

        self.args, _ = parser.parse_known_args()

    def _setup_filesets(self):
        """
        Finalize filesets for the project. Before this function is called, all sources should have been added to the
        project, either via source.yaml files/plugin-specific includes, or interactively via the add_sources function.

        Note: Do not add more sources to the project after this function has been run; They will only be considered,
        if this function is executed again afterwards.
        """

        # Read source.yaml files and store in fileset object
        default_filesets = ['default'] + self.cpu_targets + self.fpga_targets
        self.filesets = Filesets(root=self.args.input,
                                 default_filesets=default_filesets,
                                 root_func_models=self._prj_cfg.build_root_functional_models)
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
        config_path = os.path.join(self.args.input, 'source.yaml')

        # Add some default files depending on whether there is a custom top level
        for fileset in self.cpu_targets + self.fpga_targets:
            try:
                custom_top = self.cfg_file[ConfigSections.CPU_TARGET][fileset]['custom_top'] if fileset in self.cpu_targets else self.cfg_file[ConfigSections.FPGA_TARGET][fileset]['custom_top']
                print(f'Using custom top for fileset {fileset}.')
            except:
                custom_top = False

            if not custom_top:
                #ToDo: check if file inclusion should be target specific -> less for simulation only for example
                self.filesets.add_source(source=VerilogSource(files=os.path.join(self.args.input, 'tb.sv'),
                                                              config_path=config_path,
                                                              fileset=fileset,
                                                              name='tb'))

        # Set define variables specifying the emulator control architecture
        # TODO: find a better place for these operations, and try to avoid directly accessing the config dictionary
        for fileset in self.cpu_targets + self.fpga_targets:
            try:
                top_module = self.cfg_file[ConfigSections.CPU_TARGET][fileset]['top_module'] if fileset in self.cpu_targets else self.cfg_file[ConfigSections.FPGA_TARGET][fileset]['top_module']
            except:
                top_module = 'top'

            print(f'Using top module {top_module} for fileset {fileset}.')
            self.filesets.add_define(define=Define(name='CLK_MSDSL', value=f'{top_module}.emu_clk', fileset=fileset))
            self.filesets.add_define(define=Define(name='CKE_MSDSL', value=f'{top_module}.emu_cke', fileset=fileset))
            self.filesets.add_define(define=Define(name='RST_MSDSL', value=f'{top_module}.emu_rst', fileset=fileset))
            self.filesets.add_define(define=Define(name='DT_WIDTH', value=f'{self._prj_cfg.cfg.dt_width}', fileset=fileset))
            self.filesets.add_define(define=Define(name='DT_SCALE', value=f'{self._prj_cfg.cfg.dt_scale}', fileset=fileset))
            self.filesets.add_define(define=Define(name='TIME_WIDTH', value=f'{self._prj_cfg.cfg.time_width}', fileset=fileset))
            self.filesets.add_define(define=Define(name='EMU_DT', value=f'{self._prj_cfg.cfg.dt}', fileset=fileset))
            self.filesets.add_define(define=Define(name='EMU_CLK_FREQ', value=f'{self._prj_cfg.cfg.emu_clk_freq}', fileset=fileset))
            self.filesets.add_define(define=Define(name='DEC_WIDTH', value=f'{self._prj_cfg.cfg.dec_bits}', fileset=fileset))

    def _setup_targets(self, target, gen_structures=False, debug=False):
        """
        Setup targets for project.
        This may differ from one project to another and needs customization.
        1. Create target object for each target that is supported in project
        2. Assign filesets to all target objects of the project
        """

        if not self.project_sources_finalized:
            # Populate the fileset dict which will be used to copy data to target object and store in filesets variable
            self.filesets.populate_fileset_dict()
            self.project_sources_finalized = True

        filesets = self.filesets.fileset_dict

        if target in self.cpu_targets:
            #######################################################
            # Create and setup simulation target
            #######################################################
            self.__setattr__(target, CPUTarget(prj_cfg=self._prj_cfg, plugins=self._plugins, name=target, float_type=self.float_type))
            getattr(getattr(self, target), 'assign_fileset')(fileset=filesets['default'])
            if target in filesets:
                getattr(getattr(self, target), 'assign_fileset')(fileset=filesets[target])

            # Update simulation target specific configuration
            getattr(getattr(getattr(self, target), 'cfg'), 'update_config')(subsection=target)
            getattr(getattr(self, target), 'set_tstop')()
            getattr(getattr(self, target), 'update_structure_config')()
            if (not getattr(getattr(getattr(self, target), 'cfg'), 'custom_top') and gen_structures):
                getattr(getattr(self, target), 'gen_structure')()

        elif target in self.fpga_targets:
            #######################################################
            # Create and setup FPGA target
            #######################################################
            self.__setattr__(target, FPGATarget(prj_cfg=self._prj_cfg, plugins=self._plugins, name=target, float_type=self.float_type))
            getattr(getattr(self, target), 'assign_fileset')(fileset=filesets['default'])
            if target in filesets:
                getattr(getattr(self, target), 'assign_fileset')(fileset=filesets[target])

            # Update fpga target specific configuration
            getattr(getattr(getattr(self, target), 'cfg'), 'update_config')(subsection=target)
            getattr(getattr(self, target), 'set_tstop')()
            getattr(getattr(self, target), 'update_structure_config')()
            if not getattr(getattr(getattr(self, target), 'cfg'), 'custom_top'):
                getattr(getattr(self, target), 'setup_ctrl_ifc')(debug=debug)
                if gen_structures:
                    getattr(getattr(self, target), 'gen_structure')()

            # Generate corresponding firmware and add to sources
            getattr(getattr(self, target), 'gen_firmware')()

        # Copy generated sources by plugin from plugin build_root to target-specific build_root
        for plugin in self._plugins:
            try:
                dst = os.path.join(self._prj_cfg.build_root, os.path.relpath(plugin._build_root, self._prj_cfg.build_root_base))
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(plugin._build_root, dst)
            except OSError as exc:
                if exc.errno == errno.ENOTDIR:
                    shutil.copy(plugin._build_root, self._prj_cfg.build_root)
                else:
                    raise Exception(f'ERROR: Could not copy from root:{plugin._build_root} to {self._prj_cfg.build_root}')

        # Indication that project setup for active target is complete
        self._setup_finished[target] = True

    def _setup_probeobj(self, target: Union[FPGATarget, CPUTarget]):
        """
        Check if the requested probe obj in the target object already exists, in not create one.
        Return the probe object.

        :param target: Target that signals shall be extracted from
        :return: probe object that was selected in target object
        """

        # specify probe obj name, specific to selected simulator/synthesizer
        if isinstance(target, FPGATarget):
            target_name = f"prb_{self.args.synthesizer_name}"
        elif isinstance(target, CPUTarget):
            target_name = f"prb_{self.args.simulator_name}"
        else:
            raise ValueError(f"Provided target type:{target} is not supported")

        # check if probe obj is already existing, if not, instantiate one

        #ToDo: In future it should be also possible to instantiate different probe objects, depending on data format that shall be read in
        if target_name not in target.probes.keys():
            from anasymod.probe import ProbeVCD
            target.probes[target_name] = ProbeVCD(target=target)

        return target.probes[target_name]

def main():
    Analysis(op_mode='commandline')

if __name__ == '__main__':
    main()
