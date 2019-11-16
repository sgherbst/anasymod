import os

from anasymod.util import call, back2fwd
from anasymod.generators.codegen import CodeGenerator
from anasymod.sources import VerilogSource, MEMFile, BDFile
from anasymod.targets import FPGATarget

class VivadoTCLGenerator(CodeGenerator):
    """
    Class for generating a TCL control file to setup Vivado Projects, launch Vivado and execute the generated TCL file.
    """

    def __init__(self, target: FPGATarget):
        super().__init__()
        self.target = target

    def create_project(self, project_name, project_directory, force=False, full_part_name=None):
        cmd = ['create_project']
        if force:
            cmd.append('-force')
        cmd.append('"'+project_name+'"')
        cmd.append('"'+back2fwd(project_directory)+'"')
        if full_part_name is not None:
            cmd.extend(['-part', full_part_name])
        self.writeln(' '.join(cmd))

    def add_project_sources(self, content):
        """
        Add sources to project.
        :param content: List of dicts that store all target specific source and define objects.
        """

        # add verilog sources
        self.add_verilog_sources(ver_src=content.verilog_sources)

        # add verilog headers
        self.add_verilog_headers(ver_hdr=content.verilog_headers)

        # add vhdl sources
        self.add_vhdl_sources(vhdl_src=content.vhdl_sources)

        # add mem file
        self.add_mem_file(mem_files=content.mem_files)

        # add bd file
        self.add_bd_file(bd_files=content.bd_files)

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
            if src.library is not None:
                self.set_property('library', '"' + src.library + '"', f'[get_files {file_list}]')

    def add_mem_file(self, mem_files: [MEMFile]):
        for mem_file in mem_files:
            self.add_files(mem_file.files)

    def add_bd_file(self, bd_files: [BDFile]):
        for bd_file in bd_files:
            cmd = ['read_bd']
            cmd.append('{ ' + ' '.join('"' + back2fwd(file) + '"' for file in bd_file.files) + ' }')
            self.writeln(' '.join(cmd))


    def add_project_defines(self, content, fileset):
        """
        Add defines to project.
        :param content: List of dicts that store all target specific source and define objects.
        """
        define_list = []
        for define in content.defines:
            for k, v in define.define.items():
                if v is not None:
                    define_list.append(f"{k}={v}")
                else:
                    define_list.append(f"{k}")

        self.set_property('verilog_define', f"{{{' '.join(define_list)}}}", fileset)

    def add_files(self, files, norecurse=True, fileset=None):
        cmd = ['add_files']
        if fileset is not None:
            cmd.extend(['-fileset', fileset])
        if norecurse:
            cmd.append('-norecurse')
        cmd.append('{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }')
        self.writeln(' '.join(cmd))

    def set_property(self, name, value, objects):
        self.writeln(' '.join(['set_property', '-name', name, '-value', value, '-objects', objects]))

    def run(self, filename=r"run.tcl", nolog=True, nojournal=True, interactive=False):
        # write the TCL script
        tcl_script = os.path.join(self.target.prj_cfg.build_root, filename)
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = [self.target.prj_cfg.vivado_config.vivado, '-mode', 'tcl' if interactive else 'batch', '-source', tcl_script]
        if nolog:
            cmd.append('-nolog')
        if nojournal:
            cmd.append('-nojournal')

        # run the script
        call(args=cmd, cwd=self.target.prj_cfg.build_root)