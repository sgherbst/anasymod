import os
from anasymod.sim_ctrl.ctrlinfra import ControlInfrastructure
from anasymod.structures.module_uartsimctrl import ModuleUARTSimCtrl
from anasymod.structures.module_regmapsimctrl import ModuleRegMapSimCtrl
from anasymod.sources import VerilogSource, BDFile
from anasymod.files import get_from_anasymod
from anasymod.structures.structure_config import StructureConfig

class UARTControlInfrastructure(ControlInfrastructure):
    def __init__(self, prj_cfg):
        super().__init__(prj_cfg=prj_cfg)

        # Initialize internal variables
        self._simctrlregmap_path = os.path.join(prj_cfg.build_root, 'gen_ctrlregmap.sv')

        # Program Zynq PS for UART access
        self._program_zynq_ps()

        #TODO: add path to elf file and add structure for storing ctrl ifc dependent files,
        # also including the BD; later test if .tcl script for creating BD would be
        # beneficial/at least there should be a script for creating the .bd file for a
        # new Vivado version, also add binary path to xsct interface

    def gen_ctrlwrapper(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for control infrastructure. This will generate the register map, add the
        block diagram including the zynq PS and add the firmware running on the zynq PS.
        """

        # Generate simulation control wrapper and add to target sources
        with (open(self._simctrlwrap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleUARTSimCtrl(scfg=str_cfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlwrap_path, name='simctrlwrap')]

    def gen_ctrl_infrastructure(self, str_cfg: StructureConfig, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface
        selected for communication. For UART_ZYNQ control a register map, ZYNQ CPU SS block
        diagram and the firmware running on the zynq PS need to be handled.
        """

        # Generate register map according to IO settings stored in structure config and add to target sources
        with (open(self._simctrlregmap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleRegMapSimCtrl(scfg=str_cfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlregmap_path, name='simctrlregmap')]

        #TODO: Add firmware part here -> generate FW if needed and add it to target sources

    def _program_zynq_ps(self):
        """
        Program UART control application to Zynq PS to enable UART control interface.
        """

        pass

    def add_ip_cores(self, scfg, ip_dir):
        """
        Configures and adds IP cores that are necessary for selected IP cores. No IP core is
        configured and added, so this just returns an empty list.
        :return rendered template for configuring a vio IP core
        """

        return []