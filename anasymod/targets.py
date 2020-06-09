import os

from anasymod.defines import Define
from anasymod.config import EmuConfig
from anasymod.base_config import BaseConfig
from anasymod.enums import ConfigSections, FPGASimCtrl, ResultFileTypes
from anasymod.structures.structure_config import StructureConfig
from anasymod.structures.module_top import ModuleTop
from anasymod.structures.module_clk_manager import ModuleClkManager
from anasymod.sources import VerilogSource, VerilogHeader, FirmwareFile
from anasymod.sim_ctrl.uart_ctrlinfra import UARTControlInfrastructure
from anasymod.sim_ctrl.vio_ctrlinfra import VIOControlInfrastructure
from anasymod.structures.module_traceport import ModuleTracePort
from anasymod.structures.module_emu_clks import ModuleEmuClks
from anasymod.structures.module_time_manager import ModuleTimeManager
from anasymod.sim_ctrl.vio_ctrlapi import VIOCtrlApi
from anasymod.sim_ctrl.uart_ctrlapi import UARTCtrlApi
from anasymod.files import anasymod_root, anasymod_header
from anasymod.util import expand_searchpaths
from anasymod.structures.firmware_gpio import FirmwareGPIO

from anasymod.structures.module_viosimctrl import ModuleVIOSimCtrl

class Target():
    """
    This class inherits all source and define objects necessary in order to run actions for a specific target.
    """
    def __init__(self, prj_cfg: EmuConfig, plugins: list, name, target_type, float_type):
        self.prj_cfg = prj_cfg
        self.plugins = plugins
        self.float_type = float_type

        # Instantiate Simulation ControlInfrastructure Interface
        self.ctrl = None
        """ :type : ControlInfrastructure"""

        self._name = name

        # Initialize Probe Objs; there can be a probe obj for each supported simulator and synthesizer
        self.probes = {}
        """ :type : dict(Probe)"""

        # Initialize content dict  to store design sources and defines
        self.content = Content()

        # Initialize target_config
        self.cfg = Config(cfg_file=self.prj_cfg.cfg_file, prj_cfg=self.prj_cfg, name=self._name, target_type=target_type)

        # Update config options by reading from config file
        self.cfg.update_config(subsection=self._name)

        # Initialize structure configuration
        self.str_cfg = StructureConfig(prj_cfg=self.prj_cfg, tstop=self.cfg.tstop, simctrl_path= self.expanded_simctrl_path)

    def set_tstop(self):
        """
        Add define statement to specify tstop
        """
        if self.cfg.tstop is not None:
            self.content.defines.append(Define(name='TSTOP_MSDSL', value=self.cfg.tstop))

    def assign_fileset(self, fileset: dict):
        """
        Add a fileset to the target by adding defines and sources to the according attributes

        :param fileset: fileset that shall be added to target
        :type fileset: dict
        """

        for k in fileset.keys():
            setattr(self.content, k, getattr(self.content, k) + fileset[k])

    def update_structure_config(self):
        self.str_cfg.cfg.update_config(subsection=self._name)

    def gen_structure(self):
        """
        Generate toplevel, IPCore wrappers, debug infrastructure and clk manager.
        """

        # Add anasymod header
        self.content.verilog_headers += [VerilogHeader(str(anasymod_header()), name='anasymod_header')]

        # Generate toplevel and add to target sources
        toplevel_path = os.path.join(self.prj_cfg.build_root, 'gen_top.sv')
        with (open(toplevel_path, 'w')) as top_file:
            top_file.write(ModuleTop(target=self).render())
        self.content.verilog_sources += [VerilogSource(files=toplevel_path, name='top')]

        # Build control structure and add all sources to project
        if self.ctrl is not None:
            self.ctrl.gen_ctrlwrapper(str_cfg=self.str_cfg, content=self.content)
        else:
            #ToDO: needs to be cleaned up, should have individual module for pc simulation control
            with (open(os.path.join(self.prj_cfg.build_root, 'gen_ctrlwrap.sv'), 'w')) as ctrl_file:
                ctrl_file.write(ModuleVIOSimCtrl(scfg=self.str_cfg).render())
            self.content.verilog_sources += [VerilogSource(files=os.path.join(self.prj_cfg.build_root, 'gen_ctrlwrap.sv'),
                                                           name='gen_ctrlwrap')]

        # Include the source code for an oscillator if needed
        if self.str_cfg.use_default_oscillator:
            osc_model_anasymod = anasymod_root() / 'verilog' / 'osc_model_anasymod.sv'
            self.content.verilog_sources += [VerilogSource(files=str(osc_model_anasymod), name='osc_model_anasymod')]

        # Include the source code for the anasymod control block
        ctrl_anasymod = anasymod_root() / 'verilog' / 'ctrl_anasymod.sv'
        self.content.verilog_sources += [VerilogSource(files=str(ctrl_anasymod), name='ctrl_anasymod')]

        # Generate clk management wrapper and add to target sources
        clkmanagerwrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_clkmanager_wrap.sv')
        with (open(clkmanagerwrapper_path, 'w')) as clkm_file:
            clkm_file.write(ModuleClkManager(scfg=self.str_cfg).render())
        self.content.verilog_sources += [VerilogSource(files=clkmanagerwrapper_path,
                                                       name='gen_clkmanager_wrap')]

        # Generate traceport wrapper and add to target sources
        trapwrapper_path = os.path.join(self.prj_cfg.build_root, 'gen_traceport_wrap.sv')
        with (open(trapwrapper_path, 'w')) as trap_file:
            trap_file.write(ModuleTracePort(scfg=self.str_cfg).render())
        self.content.verilog_sources += [VerilogSource(files=trapwrapper_path,
                                                       name='gen_traceport_wrap')]

        # Generate emulation clk gen module and add to target sources
        gen_emu_clks_path = os.path.join(self.prj_cfg.build_root, 'gen_emu_clks.sv')
        with (open(gen_emu_clks_path, 'w')) as emu_clks_file:
            emu_clks_file.write(ModuleEmuClks(scfg=self.str_cfg, pcfg=self.prj_cfg).render())
        self.content.verilog_sources += [VerilogSource(files=gen_emu_clks_path,
                                                       name='gen_emu_clks')]

        # Generate time manager and add to target sources
        timemanager_path = os.path.join(self.prj_cfg.build_root, 'gen_time_manager.sv')
        with (open(timemanager_path, 'w')) as timemanager_file:
            timemanager_file.write(ModuleTimeManager(scfg=self.str_cfg, pcfg=self.prj_cfg).render())
        self.content.verilog_sources += [VerilogSource(files=timemanager_path,
                                                       name='gen_time_manager')]

    def gen_firmware(self):
        # Generate firmware
        gpio_fw = FirmwareGPIO(scfg=self.str_cfg)

        # Write header code
        gpio_hdr = os.path.join(self.prj_cfg.build_root, 'gpio_funcs.h')
        with open(gpio_hdr, 'w') as f:
            f.write(gpio_fw.hdr_text)
        self.content.firmware_files += [FirmwareFile(files=gpio_hdr, name='gpio_hdr')]

        # Write implementation code
        gpio_src = os.path.join(self.prj_cfg.build_root, 'gpio_funcs.c')
        with open(gpio_src, 'w') as f:
            f.write(gpio_fw.src_text)
        self.content.firmware_files += [FirmwareFile(files=gpio_src, name='gpio_src')]

    @property
    def project_root(self):
        return os.path.join(self.prj_cfg.build_root, self.prj_cfg.vivado_config.project_name)

    @property
    def result_name_raw(self):
        return f"{self.cfg.top_module}_{self._name}.{self.cfg.result_type_raw}"

    @property
    def result_path_raw(self):
        return os.path.join(self.prj_cfg.build_root, r"raw_results", self.result_name_raw)

    @property
    def expanded_simctrl_path(self):
        """
        Path used to load simctrl file. This allows to use a custom simctrl configuration for a target.

        :return: str
        """
        return "".join(expand_searchpaths(paths=self.cfg.simctrl_path, rel_path_reference=self.prj_cfg.root))

class CPUTarget(Target):
    def __init__(self, prj_cfg: EmuConfig, plugins: list, float_type:bool, name=r"sim"):
        target_type = ConfigSections.CPU_TARGET
        super().__init__(prj_cfg=prj_cfg, plugins=plugins, name=name, target_type=target_type, float_type=float_type)

        self.cfg.result_type_raw = ResultFileTypes.VCD

class FPGATarget(Target):
    def __init__(self, prj_cfg: EmuConfig, plugins: list,  float_type:bool, name=r"fpga"):
        target_type = ConfigSections.FPGA_TARGET
        super().__init__(prj_cfg=prj_cfg, plugins=plugins, name=name, target_type=target_type, float_type=float_type)

        self.cfg.result_type_raw = ResultFileTypes.CSV

        # use a different default TSTOP value, which should provide about 0.1 ps timing resolution and plenty of
        # emulation time for most purposes.
        self._ip_cores = []

    def gen_structure(self):
        """
        Generate toplevel, IPCore wrappers, debug/ctrl infrastructure for FPGA and clk manager.
        """
        super().gen_structure()
        self.ctrl.gen_ctrl_infrastructure(str_cfg=self.str_cfg, content=self.content)

    def setup_ctrl_ifc(self, debug=False):
        """
        Setup the control interface according to what was provided in the project configuration. default is VIVADO_VIO
        mode, which does not possess a direct control interface via anasymod.

        :rtype: ControlInfrastructure
        """
        #ToDo: This should only be executed for FPGA simulation!

        if self.cfg.fpga_sim_ctrl == FPGASimCtrl.VIVADO_VIO:
            print("No direct control interface from anasymod selected, Vivado VIO interface enabled.")
            self.ctrl = VIOControlInfrastructure(prj_cfg=self.prj_cfg)
            self.ctrl_api = VIOCtrlApi(result_path=self.cfg.vcd_path, result_path_raw=self.result_path_raw,
                                       result_type_raw=self.cfg.result_type_raw, pcfg=self.prj_cfg, scfg=self.str_cfg,
                                       bitfile_path=self.bitfile_path, ltxfile_path=self.ltxfile_path,
                                       float_type=self.float_type, debug=debug)
        elif self.cfg.fpga_sim_ctrl == FPGASimCtrl.UART_ZYNQ:
            print("Direct anasymod FPGA simulation control via UART enabled.")
            self.ctrl = UARTControlInfrastructure(prj_cfg=self.prj_cfg)
            self.ctrl_api = UARTCtrlApi(prj_cfg=self.prj_cfg)
        else:
            raise Exception("ERROR: No FPGA simulation control was selected, shutting down.")

    @property
    def probe_cfg_path(self):
        return os.path.join(self.project_root, 'probe_config.txt')

    @property
    def bitfile_path(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.runs', 'impl_1',
                            f"{self.cfg.top_module}.bit")

    @property
    def ltxfile_path(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.runs', 'impl_1',
                            f"{self.cfg.top_module}.ltx")

    @property
    def ip_dir(self):
        return os.path.join(self.project_root, f'{self.prj_cfg.vivado_config.project_name}.srcs', 'sources_1', 'ip')

class Config(BaseConfig):
    """
    Container to store all config attributes.
    """
    def __init__(self, cfg_file, prj_cfg, name, target_type):
        super().__init__(cfg_file=cfg_file, section=target_type)
        self.tstop = 10.0
        """ type(float) : simulation duration for target in seconds. """

        self.emu_clk_freq =25e6
        """ type(float) : emulation frequency in Hz, that is used as main independent clk in the design. """

        self.top_module = 'top'
        """ type(str) : name ot the top-level module, that is used for this target. """

        self.custom_top = False
        """ type(bool) : indicates, whether or not a custom top is used. """

        self.vcd_name = f"{self.top_module}_{name}.vcd"
        """ type(str) : name of the converted vcd simulation result file. """

        self.vcd_path = os.path.join(prj_cfg.build_root, r"vcd", self.vcd_name)
        """ type(str) : path used to store converted vcd simulation result file. """
        # TODO: move these paths to toolchain specific config, which shall be instantiated in the target class

        self.result_type_raw = None
        """ type(float) : simulation result format used for the selected target. """

        self.fpga_sim_ctrl = FPGASimCtrl.VIVADO_VIO
        """ type(float) : FPGA simulation control interface used for this target. """

        self.simctrl_path = os.path.join(prj_cfg.root, 'simctrl.yaml')
        """ type(str) : Path used to load simctrl file. This allows to use a custom simctrl configuration for a target. """

class Content():
    """
    Container storing all Project specific source files, such as RTL, eSW code, blockdiagrams, IP core configs,
    constraint files, ... .
    """

    def __init__(self):
        self.verilog_sources = []
        """:type : List[VerilogSource]"""
        self.verilog_headers = []
        """:type : List[VerilogHeader]"""
        self.vhdl_sources = []
        """:type : List[VHDLSource]"""
        self.defines = []
        """:type : List[Define]"""
        self.edif_files = []
        """:type : List[EDIFFile]"""
        self.firmware_files = []
        """:type : List[FirmwareFile]"""
        self.xci_files = []
        """:type : List[XCIFile]"""
        self.xdc_files = []
        """:type : List[XDCFile]"""
        self.mem_files = []
        """:type : List[MEMFile]"""
        self.bd_files = []
        """:type : List[BDFile]"""
        self.ip_repos = []
        """:type : List[IPRepo]"""
        self.functional_models = []
        """:type : List[FunctionalModel]"""
