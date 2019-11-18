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

        # write constraints to file
        constrs = CodeGenerator()
        constrs.use_templ(TemplExtClk(target=self.target))

        if not self.target.cfg.custom_top:
            # Add constraints for additional generated emu_clks
            constrs.writeln(
                'create_generated_clock -name emu_clk -source [get_pins clk_gen_i/clk_wiz_0_i/clk_out1] -divide_by 2 [get_pins gen_emu_clks_i/buf_emu_clk/I]')
            for k in range(len(self.target.str_cfg.clk_o)):
                constrs.writeln(
                    f'create_generated_clock -name clk_other_{k} -source [get_pins clk_gen_i/clk_wiz_0_i/clk_out1] -divide_by 4 [get_pins gen_emu_clks_i/gen_other[{k}].buf_i/I]')

        cpath = os.path.join(self.target.prj_cfg.build_root, 'constrs.xdc')
        #constrs.write_to_file(cpath)

        # add master constraints file to project
        self.add_files([cpath], fileset='constrs_1')

        #ToDo: Test if these xdc files should rather be just appended to the project as constr files

        # append user constraints
        for xdc_file in self.target.content.xdc_files:
            for file in xdc_file.files:
                self.writeln(f'read_xdc "{back2fwd(file)}"')

        #ToDo: This needs some refactoring, basically it is on the one hand target dependent-> template generation
        #ToDo: should be run while setting up the target, on the other hand it is dependent which kind of sim control
        #ToDo: interface shall be used

        if not self.target.cfg.custom_top:
            # generate clock wizard IP block
            self.use_templ(TemplClkWiz(target=self.target))

            #ToDo: tidy up this sequential build script and in doing so, create a wrapper class that takes care of this conditional structure

            if self.target.cfg.fpga_sim_ctrl is FPGASimCtrl.VIVADO_VIO:
                # generate vio IP block
                self.use_templ(TemplVIO(scfg=self.target.str_cfg, ip_dir=self.target.ip_dir))

        # read user-provided IPs
        self.writeln('# Custom user-provided IP cores')
        for xci_file in self.target.content.xci_files:
            for file in xci_file.files:
                self.writeln(f'read_ip "{back2fwd(file)}"')

        # upgrade IPs as necessary
        self.writeln('upgrade_ip [get_ips]')

        # generate all IPs
        self.writeln('generate_target all [get_ips]')

        # self.v.writeln('reset_run synth_1')
        # self.v.writeln(f'launch_runs synth_1 -jobs {min(int(self.target.prj_cfg.vivado_config.num_cores), 8)}')
        # self.v.writeln('wait_on_run synth_1')

        # TODO: make more general
        # TODO: allow tracing for custom_top
        if not self.target.cfg.custom_top:
            # run synthesis
            self.writeln('reset_run synth_1')
            self.writeln(f'launch_runs synth_1 -jobs {min(int(self.target.prj_cfg.vivado_config.num_cores), 8)}')
            self.writeln('wait_on_run synth_1')

            # extact probes from design
            #self.use_templ(TemplPROBE_EXTRACT(target=self.target))
            #self.run(filename=r"synthesis.tcl")

            # append const file with ILA according to extracted probes
            #constrs.read_from_file(cpath)
            constrs.use_templ(TemplILA(target=self.target))
    
            # write constraints to file
            constrs.use_templ(TemplDbgHub(target=self.target))
            constrs.write_to_file(cpath)

            # Open project
            # project_path = os.path.join(self.target.project_root, self.target.prj_cfg.vivado_config.project_name + '.xpr')
            # self.v.writeln(f'open_project "{back2fwd(project_path)}"')

        # launch the build and wait for it to finish
        self.writeln(f'launch_runs impl_1 -to_step write_bitstream -jobs {min(int(self.target.prj_cfg.vivado_config.num_cores), 8)}')
        self.writeln('wait_on_run impl_1')

        # self.v.println('refresh_design')
        # self.v.println('puts [get_nets - hier - filter {MARK_DEBUG}]')

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
