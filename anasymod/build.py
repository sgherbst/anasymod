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
from anasymod.blocks.probe_extract import TemplPROBE_EXTRACT
from anasymod.blocks.execute_FPGA_sim import TemplEXECUTE_FPGA_SIM
from anasymod.targets import FPGATarget

class VivadoBuild():
    def __init__(self, cfg: EmuConfig, target: FPGATarget):
        # save settings
        self.cfg = cfg
        self.target = target

        # TCL generators
        self.v = VivadoControl()

    def build(self):
        # create a new project
        self.v.create_project(project_name=self.cfg.vivado_config.project_name,
                              project_directory=self.target.project_root,
                              full_part_name=self.cfg.fpga_board_config.board.cfg['full_part_name'],
                              force=True)

        # add all source files to the project (including header files)
        self.v.add_project_sources(content=self.target.content)

        # define the top module
        self.v.set_property('top', f"{{{self.target.cfg['top_module']}}}", '[current_fileset]')

        # set define variables
        self.v.add_project_defines(content=self.target.content, fileset='[current_fileset]')
        #self.v.set_property('verilog_define', f"{{{' '.join(self.cfg.synth_verilog_defines)}}}", '[current_fileset]')

        # write constraints to file
        constrs = CodeGenerator()

        # generate the clock constraints
        ext_clk_pin_p = self.cfg.fpga_board_config.board.cfg['clk_pin_p']
        ext_clk_pin_n = self.cfg.fpga_board_config.board.cfg['clk_pin_n']
        constrs.use_templ(TemplExtClk(clk_pin_p=ext_clk_pin_p,
                                      clk_pin_n=ext_clk_pin_n,
                                      io_std=self.cfg.fpga_board_config.board.cfg['clk_io'],
                                      clk_freq=self.cfg.fpga_board_config.board.cfg['clk_freq']))

        # append user constraints
        constrs.println('##################################')
        constrs.println('# Custom user-supplied constraints')
        constrs.println('##################################')
        for xdc_file in self.target.content['xdc_files']:
            for file in xdc_file.files:
                constrs.println(f'# Constraints from file: {file}')
                constrs.read_from_file(file)

        cpath = os.path.join(self.cfg.build_root, 'constrs.xdc')
        constrs.write_to_file(cpath)

        # add constraints to project
        self.v.add_files([cpath], fileset='constrs_1')

        # generate clock wizard IP block

        # determine if the clock wizard input is differential
        if ext_clk_pin_p is not None:
            if ext_clk_pin_n is not None:
                # both are set
                clk_wiz_diff_input = True
            else:
                # only the positive clock is set
                clk_wiz_diff_input = False
        else:
            raise Exception('Cannot determine if the clock wizard input is differential or single-ended.  Note that the positive clock pin must always be specified.')

        # determine clock wizard outputs
        clk_wiz_outputs = []
        clk_wiz_outputs += [(self.cfg.cfg['emu_clk_freq'], False)]
        clk_wiz_outputs += [(self.cfg.cfg['dbg_hub_clk_freq'], False)]
        clk_wiz_outputs += [(self.cfg.cfg['emu_clk_freq'], True) for _ in range(self.cfg.cfg['emu_gated_clocks'])]

        self.v.use_templ(TemplClkWiz(input_freq=self.cfg.fpga_board_config.board.cfg['clk_freq'],
                                     clk_wiz_outputs=clk_wiz_outputs,
                                     ip_dir=self.target.ip_dir,
                                     clk_wiz_diff_input=clk_wiz_diff_input))

        # generate the VIO IP block
        self.v.use_templ(TemplVIO(outputs=[VioOutput(width=1), VioOutput(width=self.cfg.cfg['dec_bits'])],
                                  ip_dir=self.target.ip_dir, ip_module_name=self.cfg.vivado_config.vio_name))

        # read user-provided IPs
        constrs.println('# Custom user-provided IP cores')
        for xci_file in self.target.content['xci_files']:
            for file in xci_file.files:
                self.v.println(f'read_ip "{file}"')

        # upgrade IPs
        # TODO: make this more selective; only upgrade IPs that have to be upgraded
        self.v.println('upgrade_ip [get_ips]')

        # generate all IPs
        self.v.println('generate_target all [get_ips]')

        # run synthesis
        self.v.println('reset_run synth_1')
        self.v.println('launch_runs synth_1 -jobs {0}'.format(self.cfg.vivado_config.num_cores))
        self.v.println('wait_on_run synth_1')

        # extact probes from design
        self.v.use_templ(TemplPROBE_EXTRACT(cfg=self.cfg, target=self.target))

        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_root, filename=r"synthesis.tcl")

        # append const file with ILA according to extracted probes
        constrs.read_from_file(cpath)
        constrs.use_templ(TemplILA(probe_cfg_path=self.target.probe_cfg_path, depth=self.cfg.ila_depth,
                                   inst_name=self.cfg.vivado_config.ila_inst_name))

        constrs.use_templ(TemplDbgHub(dbg_hub_clk_freq=self.cfg.cfg['dbg_hub_clk_freq']))
        constrs.write_to_file(cpath)

        # Open project
        project_path = os.path.join(self.target.project_root, self.cfg.vivado_config.project_name + '.xpr')
        self.v.println(f'open_project "{back2fwd(project_path)}"')

        # launch the build and wait for it to finish
        self.v.println('launch_runs impl_1 -to_step write_bitstream -jobs {0}'.format(self.cfg.vivado_config.num_cores))
        self.v.println('wait_on_run impl_1')

        # self.v.println('refresh_design')
        # self.v.println('puts [get_nets - hier - filter {MARK_DEBUG}]')

        # re-generate the LTX file
        # without this step, the ILA probes are sometimes split into individual bits
        ltx_file_path = os.path.join(self.target.project_root, f'{self.cfg.vivado_config.project_name}.runs', 'impl_1',
                                     f"{self.target.cfg['top_module']}.ltx")
        self.v.println('open_run impl_1')
        self.v.println(f'write_debug_probes -force {{{back2fwd(ltx_file_path)}}}')

        # run bitstream generation
        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_root, filename=r"bitstream.tcl")

    def run_FPGA(self, decimation):
        self.v.use_templ(TemplEXECUTE_FPGA_SIM(cfg=self.cfg, target=self.target, decimation=decimation))
        self.v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_root, filename=r"run_FPGA.tcl")