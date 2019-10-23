from anasymod.sim.sim import Simulator
from anasymod.vivado import VivadoControl

class VivadoSimulator(Simulator):
    def simulate(self):
        # set up the simulation commands
        v = VivadoControl()

        # create a new project
        v.create_project(project_name=self.cfg.vivado_config.project_name,
                         project_directory=self.target.project_root,
                         force=True)

        # add all source files to the project (including header files)
        v.add_project_sources(content=self.target.content)

        # define the top module
        v.set_property('top', f"{{{self.target.cfg.top_module}}}", '[get_filesets {sim_1 sources_1}]')

        # set define variables
        v.add_project_defines(content=self.target.content, fileset='[get_filesets {sim_1 sources_1}]')

        # launch the simulation
        v.set_property('{xsim.simulate.runtime}', '{-all}', '[get_fileset sim_1]')
        v.writeln('launch_simulation')

        # run the simulation
        v.run(vivado=self.cfg.vivado_config.vivado, build_dir=self.cfg.build_root, filename='vivado_sim.tcl')