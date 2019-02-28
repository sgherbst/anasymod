from anasymod.sim.sim import Simulator
from anasymod.vivado import VivadoControl

class VivadoSimulator(Simulator):
    def simulate(self):
        # set up the simulation commands
        v = VivadoControl()

        # create a new project
        v.create_project(project_name=self.cfg.vivado_config.project_name,
                         project_directory=self.cfg.vivado_config.project_root,
                         force=True)

        # add all source files to the project (including header files)
        v.add_project_contents(sources=self.sources,
                               headers=self.headers)

        # define the top module
        v.set_property('top', f'{{{self.cfg.top_module}}}', '[get_fileset sim_1]')

        # dirty fix set library
        # v.set_property('library', 'ipdb_common_cell_lib', '[get_files C:/Users/tulupov/Documents/ANA_MODEL_FPGA/des_adc/singlecell/src/ipdb_common_cells/*.vhd ]')

        # set define variables
        v.set_property('verilog_define', f"{{{' '.join(self.cfg.sim_verilog_defines)}}}", '[get_fileset sim_1]')

        # launch the simulation
        v.set_property('{xsim.simulate.runtime}', '{-all}', '[get_fileset sim_1]')
        v.println('launch_simulation')

        # run the simulation
        v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_root, filename='vivado_sim.tcl')