import os
from glob import glob

from anasymod.util import call, back2fwd
from anasymod.codegen import CodeGenerator

class VivadoControl(CodeGenerator):

    def add_project_contents(self, sources=None, headers=None):
        # set defaults
        sources = sources if sources is not None else []
        headers = headers if headers is not None else []

        # build lists of all source and header files
        source_files = [f for source in sources for f in glob(source)]
        header_files = [f for header in headers for f in glob(header)]

        # add all source files to the project (including header files)
        self.add_files(source_files+header_files)

        # specify which files are header files
        self.set_header_files(header_files)

    def create_project(self, project_name, project_directory, force=False, full_part_name=None):
        cmd = ['create_project']
        if force:
            cmd.append('-force')
        cmd.append('"'+project_name+'"')
        cmd.append('"'+back2fwd(project_directory)+'"')
        if full_part_name is not None:
            cmd.extend(['-part', full_part_name])
        self.println(' '.join(cmd))

    def add_files(self, files, norecurse=True, fileset=None):
        cmd = ['add_files']
        if fileset is not None:
            cmd.extend(['-fileset', fileset])
        if norecurse:
            cmd.append('-norecurse')
        cmd.append('{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }')
        self.println(' '.join(cmd))

    def set_header_files(self, files):
        file_list = '{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def set_property(self, name, value, objects):
        self.println(' '.join(['set_property', '-name', name, '-value', value, '-objects', objects]))

    def set_vhdl_library(self, files):
        file_list = '{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def run(self, vivado, build_dir, filename=r"run.tcl", nolog=True, nojournal=True):
        # write the TCL script
        tcl_script = os.path.join(build_dir, filename)
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = [vivado, '-mode', 'batch', '-source', tcl_script]
        if nolog:
            cmd.append('-nolog')
        if nojournal:
            cmd.append('-nojournal')

        # run the script
        call(args=cmd, cwd=build_dir)