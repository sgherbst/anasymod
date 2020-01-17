import os
from anasymod.sources import Sources, VerilogSource, VerilogHeader, VHDLSource, SubConfig, XCIFile, XDCFile, MEMFile, BDFile
from anasymod.defines import Define

class Filesets():
    def __init__(self, root, default_filesets=['default', 'sim', 'fpga']):
        self._master_cfg_path = os.path.join(root, 'source.config')

        self._verilog_sources = []
        """:type : List[VerilogSource]"""

        self._verilog_headers = []
        """:type : List[VerilogHeader]"""

        self._vhdl_sources = []
        """:type : List[VHDLSource]"""

        self._xci_files = []
        """:type : List[XCIFile]"""

        self._xdc_files = []
        """:type : List[XDCFile]"""

        self._defines = []
        """:type : List[Define]"""

        self._mem_files = []
        """:type : List[MEMFile]"""

        self._bd_files = []
        """:type : List[BDFile]"""

        # init fileset_dict
        self.fileset_dict = {}
        if not default_filesets:
            for fileset in default_filesets:
                self.fileset_dict[fileset] = {}

        self._sub_config_paths = []
        """:type : List[SubConfig]"""

    def read_filesets(self, validate_paths=False):
        if os.path.isfile(self._master_cfg_path):
            with open(self._master_cfg_path, "r") as f:
                mcfg = f.readlines()

            # Read source paths from master config
            self._parseconfig(cfg=mcfg, cfg_path=self._master_cfg_path)

            # Read source paths from sub configs
            while (bool(self._sub_config_paths)):
                for config in self._sub_config_paths:
                    self._sub_config_paths.remove(config)
                    for file in config.files:
                        if os.path.isfile(file):
                            with open(file, "r") as f:
                                cfg = f.readlines()
                            self._parseconfig(cfg=cfg, cfg_path=file)
                        else:
                            print(f"WARNING: provided path:'{config}' does not exist, skipping config file")

            # Check if fileset paths exist
            if validate_paths:
                for key in self.fileset_dict.keys():
                    for path in self.fileset_dict[key]:
                        if not os.path.exists(path):
                            raise ValueError(f"Provided path:{path} of fileset:{key} does not exist")
        else:
            print(f"No config file existing, skipping to read source files.")

    def _parseconfig(self, cfg: list, cfg_path: str):
        """
        Read all lines from config file, according to string infront of '=' sign, the proceeding arguments will either
        be added to the according fileset or will be added to the list of additional config paths, which will be
        investigated in the next iteration.
        :param cfg:
        :param cfg_path:
        :return:
        """

        for k, line in enumerate(cfg):
            line = line.strip()

            if line.startswith('#'):
                # skip comments
                continue

            if line:
                try:
                    line = eval(line)
                    if isinstance(line, VerilogSource):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._verilog_sources.append(line)
                    elif isinstance(line, VerilogHeader):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._verilog_headers.append(line)
                    elif isinstance(line, VHDLSource):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._vhdl_sources.append(line)
                    elif isinstance(line, XCIFile):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._xci_files.append(line)
                    elif isinstance(line, XDCFile):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._xdc_files.append(line)
                    elif isinstance(line, MEMFile):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._mem_files.append(line)
                    elif isinstance(line, BDFile):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._bd_files.append(line)
                    elif isinstance(line, SubConfig):
                        line.config_path = cfg_path
                        line.expand_paths()
                        self._sub_config_paths.append(line)
                    elif isinstance(line, Define):
                        self._defines.append(line)
                    else:
                        raise Exception(f"Line {k+1} of config file: {cfg_path} does not fit do a specified source or config type")
                except:
                    raise Exception(f"Line {k+1} of config file: {cfg_path} could not be processed properely")

    def populate_fileset_dict(self):
        """
        Creates fileset dictionary according to filesets that were provided reading in source and define objects.
        Previously created filesets will be overwritten.
        """

        # Read in verilog source objects to fileset dict
        self._add_to_fileset_dict(name='verilog_sources', container=self._verilog_sources)

        # Read in verilog header objects to fileset dict
        self._add_to_fileset_dict(name='verilog_headers', container=self._verilog_headers)

        # Read in vhdlsource objects to fileset dict
        self._add_to_fileset_dict(name='vhdl_sources', container=self._vhdl_sources)

        # Read in xcifile objects to fileset dict
        self._add_to_fileset_dict(name='xci_files', container=self._xci_files)

        # Read in xdcfile objects to fileset dict
        self._add_to_fileset_dict(name='xdc_files', container=self._xdc_files)

        # Read in define objects to fileset dict
        self._add_to_fileset_dict(name='defines', container=self._defines)

        # Read in mem_files objects to fileset dict
        self._add_to_fileset_dict(name='mem_files', container=self._mem_files)

        # Read in bd_files objects to fileset dict
        self._add_to_fileset_dict(name='bd_files', container=self._bd_files)

    def _add_to_fileset_dict(self, name, container):
        """
        Adds a specified attribute to the fileset_dict, e.g. add the verilog sources or defines.
        """
        for item in container:
            if item.fileset in self.fileset_dict.keys():
                if name in self.fileset_dict[item.fileset]:
                    self.fileset_dict[item.fileset][name].append(item)
                else:
                    self.fileset_dict[item.fileset][name] = [item]
            else:
                print(f"Custom fileset was added:{item.fileset}")
                self.fileset_dict[item.fileset] = {}
                self.fileset_dict[item.fileset][name] = [item]


    def add_source(self, source: Sources):
        if isinstance(source, VerilogSource):
            self._verilog_sources.append(source)
        if isinstance(source, VerilogHeader):
            self._verilog_headers.append(source)
        if isinstance(source, VHDLSource):
            self._vhdl_sources.append(source)

    def add_define(self, define: Define):
        self._defines.append(define)

    def add_xci_file(self, xci_file: XCIFile):
        self._xci_files.append(xci_file)

    def add_xdc_file(self, xdc_file: XDCFile):
        self._xdc_files.append(xdc_file)

    def add_mem_file(self, mem_file: MEMFile):
        self._mem_files.append(mem_file)

    def add_bd_file(self, bd_file: BDFile):
        self._bd_files.append(bd_file)

def main():
    fileset = Filesets(root=r"C:\Inicio_dev\anasymod\tests\filter")
    fileset.read_filesets()
    print(fileset.fileset_dict)

if __name__ == '__main__':
    main()