import os

from anasymod.util import call, back2fwd
from anasymod.generators.codegen import CodeGenerator
from anasymod.sources import VerilogSource, MEMFile, BDFile, IPRepo, EDIFFile
from anasymod.targets import FPGATarget

class VivadoTCLGenerator(CodeGenerator):
    """
    Class for generating a TCL control file to setup Vivado Projects, launch Vivado and execute the generated TCL file.
    """

    def __init__(self, target: FPGATarget):
        super().__init__()
        self.target = target

    def create_project(self, project_name, project_directory, force=False, full_part_name=None,
                       board_part=None):
        # create the project
        cmd = ['create_project']
        if force:
            cmd.append('-force')
        cmd.append('"'+project_name+'"')
        cmd.append('"'+back2fwd(project_directory)+'"')
        if full_part_name is not None:
            cmd.extend(['-part', full_part_name])
        self.writeln(' '.join(cmd))

        # specify the board part if known
        if board_part is not None:
            self.writeln(f'set_property board_part {board_part} [current_project]')

    def add_project_sources(self, content):
        """
        Add sources to project.
        :param content: List of dicts that store all target specific source and define objects.
        """

        # add verilog sources
        self.add_verilog_sources(ver_src=content.verilog_sources)

        # add verilog headers
        self.add_verilog_headers(ver_hdr=content.verilog_headers)

        # add functional model HDL sources
        self.add_functional_models(fm_src=content.functional_models)

        # add vhdl sources
        self.add_vhdl_sources(vhdl_src=content.vhdl_sources)

        # add edif file
        self.add_edif_file(edif_files=content.edif_files)

        # add mem file
        self.add_mem_file(mem_files=content.mem_files)

        # add ip repo
        self.add_ip_repo(ip_repos=content.ip_repos)

        # add bd file
        self.add_bd_file(bd_files=content.bd_files)

    def add_verilog_sources(self, ver_src: [VerilogSource]):
        for src in ver_src:
            if src.files:
                self.add_files(src.files)
                if src.version is not None:
                    file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in src.files) + ' }'
                    self.set_property('file_type', value=f'{{{src.version}}}', objects=f'[get_files {file_list}]')

    def add_verilog_headers(self, ver_hdr):
        for src in ver_hdr:
            if src.files:
                self.add_files(src.files)
                file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in src.files) + ' }'
                self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def add_functional_models(self, fm_src):
        for src in fm_src:
            if src.gen_files:
                files = []
                for file in src.gen_files:
                    files.append(file)
                self.add_files(files)

    def add_vhdl_sources(self, vhdl_src):
        for src in vhdl_src:
            if src.files:
                self.add_files(src.files)
                if src.library is not None:
                    file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in src.files) + ' }'
                    self.set_property('library', value=f'{{{src.library}}}', objects=f'[get_files {file_list}]')
                if src.version is not None:
                    file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in src.files) + ' }'
                    self.set_property('file_type', value=f'{{{src.version}}}', objects=f'[get_files {file_list}]')

    def add_edif_file(self, edif_files: [EDIFFile]):
        for edif_file in edif_files:
            if edif_file.files:
                self.add_files(edif_file.files)

    def add_mem_file(self, mem_files: [MEMFile]):
        for mem_file in mem_files:
            if mem_file.files:
                self.add_files(mem_file.files)

    def add_bd_file(self, bd_files: [BDFile]):
        for bd_file in bd_files:
            if bd_file.files:
                cmd = ['read_bd']
                cmd.append('{ ' + ' '.join('"' + back2fwd(file) + '"' for file in bd_file.files) + ' }')
                self.writeln(' '.join(cmd))

    def add_ip_repo(self, ip_repos: [IPRepo]):
        for ip_repo in ip_repos:
            if ip_repo.files:
                self.set_property(name='ip_repo_paths', value='{ ' + ' '.join('"' + back2fwd(file) + '"' for file in ip_repo.files) + ' }', objects='[current_project]')
        self.writeln('update_ip_catalog -rebuild')

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
        if files is None or len(files) == 0:
            # don't generate a command because add_files does not work with
            # an empty list of files
            return

        cmd = ['add_files']
        if fileset is not None:
            cmd.extend(['-fileset', fileset])
        if norecurse:
            cmd.append('-norecurse')
        cmd.append('{ '+' '.join('"'+back2fwd(file)+'"' for file in files)+' }')
        self.writeln(' '.join(cmd))

    def set_property(self, name, value, objects):
        self.writeln(' '.join(['set_property', '-name', name, '-value', value, '-objects', objects]))

    def run(self, filename=r"run.tcl", nolog=True, nojournal=True, interactive=False, err_str=None):
        # write the TCL script
        tcl_script = os.path.join(self.target.prj_cfg.build_root, filename)
        self.write_to_file(tcl_script)

        # assemble the command
        cmd = [self.target.prj_cfg.vivado_config.vivado, '-mode', 'tcl' if interactive else 'batch', '-source', tcl_script]
        # inserting lsf_opts after vivado call:
        cmd[1:1] = self.target.prj_cfg.vivado_config.lsf_opts.split()

        if nolog:
            cmd.append('-nolog')
        if nojournal:
            cmd.append('-nojournal')

        # run the script
        call(args=cmd, cwd=self.target.prj_cfg.build_root, err_str=err_str)

    @property
    def version_year(self):
        return self.target.prj_cfg.vivado_config.version_year

    @property
    def version_number(self):
        return self.target.prj_cfg.vivado_config.version_number