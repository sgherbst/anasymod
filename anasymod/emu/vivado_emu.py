import os.path

from anasymod.generators.vivado import VivadoTCLGenerator
from anasymod.generators.codegen import CodeGenerator
from anasymod.util import back2fwd

from anasymod.templates.dbg_hub import TemplDbgHub
from anasymod.templates.ext_clk import TemplExtClk
from anasymod.templates.clk_wiz import TemplClkWiz
from anasymod.templates.vio_wiz import TemplVIO
from anasymod.templates.execute_FPGA_sim import TemplEXECUTE_FPGA_SIM
from anasymod.templates.launch_FPGA_sim import TemplLAUNCH_FPGA_SIM
from anasymod.templates.probe_extract import TemplPROBE_EXTRACT
from anasymod.templates.ila import TemplILA
from anasymod.targets import FPGATarget
from anasymod.enums import FPGASimCtrl
from anasymod.sim_ctrl.ctrlinfra import ControlInfrastructure


class VivadoEmulation(VivadoTCLGenerator):
    """
    Generate and execute Vivado TCL scripts to generate a bitstream, run an emulation of FPGA for non-interactive mode,
    or launch an FPGA emulation for interactive mode and pass the handle for interactive control.
    """

    def __init__(self, target: FPGATarget):
        super().__init__(target=target)

    def build(self):
        # create a new project
        self.create_project(project_name=self.target.prj_cfg.vivado_config.project_name,
                              project_directory=self.target.project_root,
                              full_part_name=self.target.prj_cfg.board.full_part_name,
                              force=True)

        # add all source files to the project (including header files)
        self.add_project_sources(content=self.target.content)

        # define the top module
        self.set_property('top', f"{{{self.target.cfg.top_module}}}", '[current_fileset]')

        # set define variables
        self.add_project_defines(content=self.target.content, fileset='[current_fileset]')

        # append user constraints
        for xdc_file in self.target.content.xdc_files:
            for file in xdc_file.files:
                self.writeln(f'read_xdc "{back2fwd(file)}"')

        # write constraints to file
        constrs = CodeGenerator()
        constrs.use_templ(TemplExtClk(target=self.target))

        # TODO: allow tracing for custom_top
        if not self.target.cfg.custom_top:
            # generate clock wizard IP core
            self.use_templ(TemplClkWiz(target=self.target))

            # Add IP cores necessary for control interface
            ip_core_templates = self.target.ctrl.add_ip_cores(scfg=self.target.str_cfg, ip_dir=self.target.ip_dir)
            for ip_core_template in ip_core_templates:
                self.use_templ(ip_core_template)

            # Add constraints for additional generated emu_clks
            constrs.writeln('create_generated_clock -name emu_clk -source [get_pins clk_gen_i/clk_wiz_0_i/clk_out1] -divide_by 2 [get_pins gen_emu_clks_i/buf_emu_clk/I]')
            for k in range(len(self.target.str_cfg.clk_o)):
                constrs.writeln(f'create_generated_clock -name clk_other_{k} -source [get_pins clk_gen_i/clk_wiz_0_i/clk_out1] -divide_by 4 [get_pins gen_emu_clks_i/gen_other[{k}].buf_i/I]')

            # Setup ILA for signal probing
            self.use_templ(TemplILA(target=self.target))
    
            # Setup Debug Hub
            constrs.use_templ(TemplDbgHub(target=self.target))

        # write master constraints to file and add to project
        master_constr_path = os.path.join(self.target.prj_cfg.build_root, 'constrs.xdc')
        constrs.write_to_file(master_constr_path)
        self.add_files([master_constr_path], fileset='constrs_1')

        # read user-provided IPs
        self.writeln('# Custom user-provided IP cores')
        for xci_file in self.target.content.xci_files:
            for file in xci_file.files:
                self.writeln(f'read_ip "{back2fwd(file)}"')

        # upgrade IPs as necessary
        self.writeln('upgrade_ip [get_ips]')

        # generate all IPs
        self.writeln('generate_target all [get_ips]')

        # launch the build and wait for it to finish
        self.writeln(f'launch_runs impl_1 -to_step write_bitstream -jobs {min(int(self.target.prj_cfg.vivado_config.num_cores), 8)}')
        self.writeln('wait_on_run impl_1')

        # re-generate the LTX file
        # without this step, the ILA probes are sometimes split into individual bits
        ltx_file_path = os.path.join(self.target.project_root, f'{self.target.prj_cfg.vivado_config.project_name}.runs',
                                     'impl_1',
                                     f"{self.target.cfg.top_module}.ltx")
        self.writeln('open_run impl_1')
        self.writeln(f'write_debug_probes -force {{{back2fwd(ltx_file_path)}}}')

        # run bitstream generation
        self.run(filename=r"bitstream.tcl")

    def run_FPGA(self, start_time: float, stop_time: float, server_addr: str):
        """
        Run the FPGA in non-interactive mode. This means FPGA will run for specified duration, all specified signals
        will be captured and dumped to a file.

        :param start_time: Point in time from which recording run data will start
        :param stop_time: Point in time where FPGA run will be stopped
        :param dt: Update rate of analog behavior calculation
        :param server_addr: Hardware server address for hw server launched by Vivado
        """

        self.use_templ(TemplEXECUTE_FPGA_SIM(target=self.target, start_time=start_time, stop_time=stop_time, server_addr=server_addr))
        self.run(filename=r"run_FPGA.tcl", interactive=False)

    def launch_FPGA(self, server_addr: str):
        """
        Run the FPGA in interactive mode. This means FPGA will be programmed and control interfaces prepared. After that
        interactive communication with FPGA is possible.

        :param server_addr: Hardware server address for hw server launched by Vivado
        """

        self.use_templ(TemplLAUNCH_FPGA_SIM(target=self.target, server_addr=server_addr))
        self.run(filename=r"launch_FPGA.tcl", interactive=True)

        # ToDo: Depending on the fpga_ctrl setting in the project, setup the control interface e.g. UART or VIO, also
        # ToDo: check that VIO only works for linux

        # Return the control interface handle
        # ToDo: include spawnu + Steven's control setup to start Vivado TCL shell and return the shell handle
        #return
