import os, yaml
from anasymod.sources import Sources, VerilogSource, VerilogHeader, VHDLSource, SubConfig, XCIFile, XDCFile, MEMFile, BDFile
from anasymod.defines import Define

class Filesets():
    def __init__(self, root, default_filesets):
        self._master_cfg_path = os.path.join(root, 'source.yaml')
        self.default_filesets = default_filesets

        # Store all config file paths in list for packing purposes
        self._config_paths = [self._master_cfg_path]

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
            try:
                mcfg = yaml.safe_load(open(self._master_cfg_path, "r"))
            except yaml.YAMLError as exc:
                raise Exception(exc)

            # Read source paths from master config
            self._parseconfig(cfg=mcfg, cfg_path=self._master_cfg_path)

            # Read source paths from sub configs
            while (bool(self._sub_config_paths)):
                for config in self._sub_config_paths:
                    self._sub_config_paths.remove(config)
                    for file in config.files:
                        if os.path.isfile(file):
                            try:
                                cfg = yaml.safe_load(open(file, "r"))
                            except yaml.YAMLError as exc:
                                raise Exception(exc)
                            self._parseconfig(cfg=cfg, cfg_path=file)
                            self._config_paths.append(config)  #Store processed config path
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

    def _parseconfig(self, cfg: dict, cfg_path: str):
        """
        Store all entries from source.yaml to the according fileset or added to the list of additional config paths,
        which will be read and stored in the next iteration.
        :param cfg: source.yaml stored as dict
        :param cfg_path: path to source.yaml file
        """

        if 'verilog_sources' in cfg.keys(): # Add verilog sources to filesets
            print(f'Verilog Sources: {[key for key in cfg["verilog_sources"].keys()]}')
            for verilog_source in cfg['verilog_sources'].keys():
                self._verilog_sources.append(VerilogSource(files=cfg['verilog_sources'][verilog_source]['files'],
                                                           fileset=cfg['verilog_sources'][verilog_source]['fileset'] if 'fileset' in cfg['verilog_sources'][verilog_source].keys() else 'default',
                                                           config_path=cfg_path,
                                                           version=cfg['verilog_sources'][verilog_source]['version'] if 'verilog_version' in cfg['verilog_sources'][verilog_source].keys() else None))
        if 'verilog_headers' in cfg.keys(): # Add verilog headers to filesets
            print(f'Verilog Headers: {[key for key in cfg["verilog_headers"].keys()]}')
            for verilog_header in cfg['verilog_headers'].keys():
                self._verilog_headers.append(VerilogHeader(files=cfg['verilog_headers'][verilog_header]['files'],
                                                           fileset=cfg['verilog_headers'][verilog_header]['fileset'] if 'fileset' in cfg['verilog_headers'][verilog_header].keys() else 'default',
                                                           config_path=cfg_path))
        if 'vhdl_sources' in cfg.keys(): # Add VHDL sources to filesets
            print(f'VHDL Sources: {[key for key in cfg["vhdl_sources"].keys()]}')
            for vhdl_source in cfg['vhdl_sources'].keys():
                self._vhdl_sources.append(VHDLSource(files=cfg['vhdl_sources'][vhdl_source]['files'],
                                                     fileset=cfg['vhdl_sources'][vhdl_source]['fileset'] if 'fileset' in cfg['vhdl_sources'][vhdl_source].keys() else 'default',
                                                     config_path=cfg_path,
                                                     library=cfg['vhdl_sources'][vhdl_source]['library'] if 'library' in cfg['vhdl_sources'][vhdl_source].keys() else None,
                                                     version = cfg['vhdl_sources'][vhdl_source]['version'] if 'version' in cfg['vhdl_sources'][vhdl_source].keys() else None))
        if 'xci_files' in cfg.keys(): # Add xci files to filesets
            print(f'XCI Files: {[key for key in cfg["xci_files"].keys()]}')
            for xci_file in cfg['xci_files'].keys():
                self._xci_files.append(XCIFile(files=cfg['xci_files'][xci_file]['files'],
                                               fileset=cfg['xci_files'][xci_file]['fileset'] if 'fileset' in cfg['xci_files'][xci_file].keys() else 'default',
                                               config_path=cfg_path))
        if 'xdc_files' in cfg.keys(): # Add constraint files to filesets
            print(f'XDC Files: {[key for key in cfg["xdc_files"].keys()]}')
            for xdc_file in cfg['xdc_files'].keys():
                self._xdc_files.append(XDCFile(files=cfg['xdc_files'][xdc_file]['files'],
                                               fileset=cfg['xdc_files'][xdc_file]['fileset'] if 'fileset' in cfg['xdc_files'][xdc_file].keys() else 'default',
                                               config_path=cfg_path))
        if 'mem_files' in cfg.keys():  # Add mem files to filesets
            print(f'Mem Files: {[key for key in cfg["mem_files"].keys()]}')
            for mem_file in cfg['mem_files'].keys():
                self._mem_files.append(MEMFile(files=cfg['mem_files'][mem_file]['files'],
                                               fileset=cfg['mem_files'][mem_file]['fileset'] if 'fileset' in cfg['mem_files'][mem_file].keys() else 'default',
                                               config_path=cfg_path))
        if 'bd_files' in cfg.keys():  # Add block diagram files to filesets
            print(f'Block Diagram Files: {[key for key in cfg["bd_files"].keys()]}')
            for bd_file in cfg['bd_files'].keys():
                self._bd_files.append(BDFile(files=cfg['bd_files'][bd_file]['files'],
                                             fileset=cfg['bd_files'][bd_file]['fileset'] if 'fileset' in cfg['bd_files'][bd_file].keys() else 'default',
                                             config_path=cfg_path))
        if 'sub_configs' in cfg.keys():  # Add sub config files to filesets
            for sub_config in cfg['sub_configs'].keys():
                self._sub_config_paths.append(SubConfig(files=cfg['sub_configs'][sub_config]['files'], config_path=cfg_path))
        if 'defines' in cfg.keys():  # Add defines to filesets
            print(f'Defines: {[key for key in cfg["defines"].keys()]}')
            for define in cfg['defines'].keys():
                self._defines.append(Define(name=cfg['defines'][define]['name'],
                                            value=cfg['defines'][define]['value'] if 'value' in cfg['defines'][define].keys() else None,
                                            fileset=cfg['defines'][define]['fileset'] if 'fileset' in cfg['defines'][define].keys() else 'default'))

    def populate_fileset_dict(self):
        """
        Creates fileset dictionary according to filesets that were provided reading in source and define objects.
        Previously created filesets will be overwritten.
        """

        # Initialize all filesets
        self.fileset_dict = {}
        if not self.default_filesets:
            for fileset in self.default_filesets:
                self.fileset_dict[fileset] = {}

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