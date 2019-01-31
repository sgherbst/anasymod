import os.path

from anasymod.vivado import VivadoControl
from anasymod.codegen import CodeGenerator
from anasymod.config import EmuConfig
from anasymod.util import back2fwd

from anasymod.blocks.ila import TemplILA
from anasymod.blocks.dbg_hub import TemplDbgHub
from anasymod.blocks.ext_clk import TemplExtClk
from anasymod.blocks.clk_wiz import TemplClkWiz
from anasymod.blocks.vio import TemplVIO, VioOutput

class VivadoBuild():
    def __init__(self, cfg: EmuConfig):
        # save settings
        self.cfg = cfg

        # TCL generators
        self.v = VivadoControl()

    def build(self):
        # create a new project
        self.v.create_project(project_name=self.cfg.vivado_config.project_name,
                              project_directory=self.cfg.vivado_config.project_directory,
                              full_part_name=self.cfg.fpga_board_config.full_part_name,
                              force=True)

        # add all source files to the project (including header files)
        self.v.add_project_contents(sources=self.cfg.synth_verilog_sources,
                                    headers=self.cfg.synth_verilog_headers)

        # define the top module
        self.v.set_property('top', f'{{{self.cfg.top_module}}}', '[current_fileset]')

        # set define variables
        self.v.set_property('verilog_define', f"{{{' '.join(self.cfg.synth_verilog_defines)}}}", '[current_fileset]')

        # write constraints to file
        constrs = CodeGenerator()

        constrs.use_templ(TemplExtClk(ext_clk_pin=self.cfg.fpga_board_config.clk_pin,
                                      ext_clk_io_std=self.cfg.fpga_board_config.clk_io,
                                      ext_clk_freq=self.cfg.fpga_board_config.clk_freq))

        constrs.use_templ(TemplILA(depth=self.cfg.ila_depth,
                                   signals=self.cfg.probe_signals))

        constrs.use_templ(TemplDbgHub(dbg_hub_clk_freq=self.cfg.dbg_hub_clk_freq))

        cpath = os.path.join(self.cfg.build_dir, 'constrs.xdc')
        constrs.write_to_file(cpath)

        # add constraints to project
        self.v.add_files([back2fwd(cpath)], fileset='constrs_1')

        # generate the IP blocks
        self.v.use_templ(TemplClkWiz(input_freq=self.cfg.fpga_board_config.clk_freq,
                                     output_freqs=[self.cfg.emu_clk_freq, self.cfg.dbg_hub_clk_freq],
                                     ip_dir=self.ip_dir))
        self.v.use_templ(TemplVIO(outputs=[VioOutput(width=1)], ip_dir=self.ip_dir))

        # generate all IPs
        self.v.println('generate_target all [get_ips]')

        # launch the build and wait for it to finish
        self.v.println('launch_runs impl_1 -to_step write_bitstream -jobs 2')
        self.v.println('wait_on_run impl_1')

        # self.v.println('refresh_design')
        # self.v.println('puts [get_nets - hier - filter {MARK_DEBUG}]')

        # run the simulation
        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_dir)

    @property
    def ip_dir(self):
        return os.path.join(
            self.cfg.build_dir,
            self.cfg.vivado_config.project_directory,
            f'{self.cfg.vivado_config.project_name}.srcs',
            'sources_1',
            'ip'
        )