import os

from anasymod.generators.codegen import CodeGenerator
from anasymod.util import back2fwd, expand_searchpaths
from typing import Union

class ConfigFileObj(CodeGenerator):
    def __init__(self, files, config_path):
        super().__init__()
        self.files = None
        """ type(str) : mandatory setting; defines the path to sources. The path can be relative, absolute and 
            contain wildcards. """

        if isinstance(files, list):
            self.files = files
        elif isinstance(files, str):
            self.files = [files]
        else:
            raise TypeError(f"Type of config_paths variable provided to SubConfig class is not a list, is:{type(files)} instead.")

        self.config_path = config_path

        # In case config_path was not specified yet (default is None) path expansion needs to be performed later manually after setting config_path
        # This is necessary to improve conveniency of providing sources in config file
        if config_path is not None:
            self.expand_paths()

    def expand_paths(self):
        """
        Expand environment variables in provided list of paths.
        Check if path is absolute or relative, in case of a relative path, it will be expanded to an absolute path,
        whereas the folder of the config_file will be used to complete the path.
        """

        self.files = expand_searchpaths(paths=self.files, rel_path_reference=os.path.dirname(self.config_path))

class SubConfig(ConfigFileObj):
    def __init__(self, files: Union[list, str], config_path=None):
        super().__init__(files=files, config_path=config_path)

class Sources(ConfigFileObj):
    def __init__(self, files: list, fileset, config_path):
        super().__init__(files=files, config_path=config_path)
        self.fileset = fileset
        """ type(str) : Fileset, the source shall be associsted with. """


    def generate(self):
        pass

    def set_property(self, name, value, objects):
        self.writeln(' '.join(['set_property', '-name', name, '-value', value, '-objects', objects]))

class VerilogSource(Sources):
    """
    Container for source of type Verilog/SystemVerilog.

    :param files: Path to source file, could be relative/absolute and contain wildcards
    :type files: str

    """
    def __init__(self, files: Union[list, str], fileset=r"default", config_path=None, version=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path)
        self.version = version
        """ type(str) : Verilog version, that shall be used when compiling sources. """

    def generate(self):
        self.text = self.files
        return self.dump()

class VerilogHeader(Sources):
    def __init__(self, files: Union[list, str], fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path)

    def set_header_files(self):
        file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in self.files) + ' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def generate(self):
        self.dump()

class VHDLSource(Sources):
    def __init__(self, files: Union[list, str], library=None, fileset=r"default", config_path=None, version=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path)
        self.library = library
        """ type(str) : Library, the source shall be associated with when compiling. """

        self.version = version
        """ type(str) : VHDL version, that shall be used when compiling sources. """


    def generate(self):
        self.dump()

class XCIFile(Sources):
    def __init__(self, files: Union[list, str], fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path)

class XDCFile(Sources):
    def __init__(self, files: Union[list, str], fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path)

class MEMFile(Sources):
    def __init__(self, files: str, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path)

class BDFile(Sources):
    def __init__(self, files: str, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path)
