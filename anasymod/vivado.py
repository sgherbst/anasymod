import os
from glob import glob

from anasymod.util import call, back2fwd
from anasymod.codegen import CodeGenerator
from anasymod.sources import Sources, VerilogSource, VerilogHeader, VHDLSource

class VivadoControl(CodeGenerator):

    def create_project(self, project_name, project_directory, force=False, full_part_name=None):
        cmd = ['create_project']
        if force:
            cmd.append('-force')
        cmd.append('"'+project_name+'"')
        cmd.append('"'+back2fwd(project_directory)+'"')
        if full_part_name is not None:
            cmd.extend(['-part', full_part_name])
        self.println(' '.join(cmd))

    def add_project_sources(self, content):
        """
        Add sources to project.
        :param content: List of dicts that store all target specific source and define objects.
        """

        # add verilog sources
        self.add_verilog_sources(ver_src=content['verilog_sources'])

        # add verilog headers
        self.add_verilog_headers(ver_hdr=content['verilog_headers'])

        # add verilog sources
        self.add_vhdl_sources(vhdl_src=content['vhdl_sources'])

    def add_verilog_sources(self, ver_src: [VerilogSource]):
        f_list = []
        for src in ver_src:
            f_list += src.files
        self.add_files(f_list)

    def add_verilog_headers(self, ver_hdr):
        f_list = []
        for src in ver_hdr:
            f_list += src.files
        self.add_files(f_list)
        file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in f_list) + ' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def add_vhdl_sources(self, vhdl_src):
        for src in vhdl_src:
            self.add_files(src.files)
            file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in src.files) + ' }'
            self.set_property('library', '"' + src.library + '"', f'[get_files {file_list}]')

    def add_project_defines(self, content):
        """
        Add defines to project.
        :param content: List of dicts that store all target specific source and define objects.
        """
        define_list = []
        for define in content['defines']:
            for k, v in define.define.items():
                if v is not None:
                    define_list.append(f"{k}={v}")
                else:
                    define_list.append(f"{k}")

        self.set_property('verilog_define', f"{{{' '.join(define_list)}}}", '[get_fileset sim_1]')

    def add_files(self, files, norecurse=True, fileset=None):
        cmd = ['add_files']
        if fileset is not None:
            cmd.extend(['-fileset', fileset])
        if norecurse:
            cmd.append('-norecurse')
        cmd.append('{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }')
        self.println(' '.join(cmd))

    def set_property(self, name, value, objects):
        self.println(' '.join(['set_property', '-name', name, '-value', value, '-objects', objects]))

    def set_vhdl_library(self, files):
        file_list = '{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')
        # dirty fix set library
        self.set_property('library', 'ipdb_common_cell_lib', '[get_files C:/Users/tulupov/Documents/ANA_MODEL_FPGA/des_adc/singlecell/src/ipdb_common_cells/*.vhd ]')

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