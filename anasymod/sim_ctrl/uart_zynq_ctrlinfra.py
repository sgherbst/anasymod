import os
from anasymod.sim_ctrl.ctrlinfra import ControlInfrastructure
from anasymod.structures.module_uartsimctrl import ModuleUARTSimCtrl
from anasymod.structures.module_regmapsimctrl import ModuleRegMapSimCtrl
from anasymod.sources import VerilogSource, BDFile, FirmwareFile
from anasymod.files import get_from_anasymod
from anasymod.structures.structure_config import StructureConfig
from anasymod.structures.firmware_gpio import FirmwareGPIO
from anasymod.structures.uart_zynq_firmware_appcode import UartZynqFirmwareAppCode
#from anasymod.targets import Config as tcfg

class UARTControlInfrastructure(ControlInfrastructure):
    def __init__(self, prj_cfg, scfg: StructureConfig, plugin_includes, tcfg):
        super().__init__(prj_cfg=prj_cfg, plugin_includes=plugin_includes)
        self.scfg = scfg
        self.tcfg = tcfg

        # Initialize internal variables
        self._simctrlregmap_path = os.path.join(prj_cfg.build_root, 'gen_ctrlregmap.sv')

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
           ctrl_file.write(ModuleUARTSimCtrl(scfg=self.scfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlwrap_path, name='simctrlwrap')]

    def gen_ctrl_infrastructure(self, content):
        """
        Generate RTL design for FPGA specific control infrastructure, depending on the interface
        selected for communication. For UART_ZYNQ control a register map, ZYNQ CPU SS block
        diagram and the firmware running on the zynq PS need to be handled.
        """

        # Generate register map according to IO settings stored in structure config and add to target sources
        with (open(self._simctrlregmap_path, 'w')) as ctrl_file:
           ctrl_file.write(ModuleRegMapSimCtrl(scfg=self.scfg).render())

        content.verilog_sources += [VerilogSource(files=self._simctrlregmap_path, name='simctrlregmap')]

        # Generate Hardware Abstraction Layer according to control signals
        # specified in the simctrl.yaml file and add to sources.

        gpio_fw = FirmwareGPIO(scfg=self.scfg)

        # Write header code
        gpio_hdr = os.path.join(self.pcfg.build_root, 'gpio_funcs.h')
        with open(gpio_hdr, 'w') as f:
            f.write(gpio_fw.hdr_text)
        content.firmware_files += [FirmwareFile(files=gpio_hdr, name='gpio_hdr')]

        # Write implementation code
        gpio_src = os.path.join(self.pcfg.build_root, 'gpio_funcs.c')
        with open(gpio_src, 'w') as f:
            f.write(gpio_fw.src_text)
        content.firmware_files += [FirmwareFile(files=gpio_src, name='gpio_src')]

        # Generate application code for UART_ZYNQ control, if no custom code is provided
        if not self.tcfg.custom_zynq_firmware:
            appcode = UartZynqFirmwareAppCode(scfg=self.scfg)
            # Write application code and add to firmware files
            appcode_src = os.path.join(self.pcfg.build_root, 'main.c')
            with open(appcode_src, 'w') as f:
                f.write(appcode.src_text)
            content.firmware_files += [FirmwareFile(files=appcode_src, name='appcode_src')]

    def add_ip_cores(self, scfg, ip_dir):
        """
        Configures and adds IP cores that are necessary for selected IP cores. VIO IP core is configured and added.
        :return rendered template for configuring a vio IP core
        """
        return []