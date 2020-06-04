import os

from anasymod.generators.codegen import CodeGenerator
from anasymod.util import back2fwd, expand_searchpaths
from typing import Union

class ConfigFileObj(CodeGenerator):
    def __init__(self, files, config_path, name):
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
        self.name = name

    def expand_paths(self):
        """
        Expand environment variables in provided list of paths.
        Check if path is absolute or relative, in case of a relative path, it will be expanded to an absolute path,
        whereas the folder of the config_file will be used to complete the path.
        """

        self.files = expand_searchpaths(paths=self.files, rel_path_reference=os.path.dirname(self.config_path))

class SubConfig(ConfigFileObj):
    def __init__(self, files: Union[list, str], name, config_path=None):
        super().__init__(files=files, config_path=config_path, name=name)

class Sources(ConfigFileObj):
    def __init__(self, files: list, fileset, config_path, name):
        super().__init__(files=files, config_path=config_path, name=name)
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
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None, version=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)
        self.version = version
        """ type(str) : Verilog version, that shall be used when compiling sources. """

    def generate(self):
        self.text = self.files
        return self.dump()

class VerilogHeader(Sources):
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)

    def set_header_files(self):
        file_list = '{ ' + ' '.join('"' + back2fwd(file) + '"' for file in self.files) + ' }'
        self.set_property('file_type', '{Verilog Header}', f'[get_files {file_list}]')

    def generate(self):
        self.dump()

class VHDLSource(Sources):
    def __init__(self, files: Union[list, str], name, library=None, fileset=r"default", config_path=None, version=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)
        self.library = library
        """ type(str) : Library, the source shall be associated with when compiling. """

        self.version = version
        """ type(str) : VHDL version, that shall be used when compiling sources. """


    def generate(self):
        self.dump()

class EDIFFile(Sources):
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)

class FirmwareFile(Sources):
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)

class XCIFile(Sources):
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)

class XDCFile(Sources):
    def __init__(self, files: Union[list, str], name, fileset=r"default", config_path=None):
        super().__init__(files=files, fileset=fileset, config_path=config_path, name=name)

class MEMFile(Sources):
    def __init__(self, files: str, name, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path, name=name)

class BDFile(Sources):
    def __init__(self, files: str, name, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path, name=name)

class IPRepo(Sources):
    def __init__(self, files: str, name, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path, name=name)

class FunctionalModel(Sources):
    def __init__(self, files: str, name, fileset=r"default", config_path=None):
        super().__init__(files=[files], fileset=fileset, config_path=config_path, name=name)
        self.gen_files = None

    def set_gen_files_path(self, hdl_dir_root):
        """
        Set the result HDL path, where generated files can be found after generation was conducted.

        :param hdl_dir_root: Root directory for gen_files, this is usually set in emu config.
        """
        # TODO: Have the model generator declare what files should be included in "gen_files"
        # It is possible that not everything in the hdl_dir_root is an HDL source (e.g.,
        # temporary files generated during processing, memory files that are included, etc.)
        self.gen_files = [os.path.join(hdl_dir_root, self.fileset, self.name, '*.*v')]

    def expand_gen_files_path(self):
        """
        Expand environment variables in provided list of paths.
        Check if path is absolute or relative, in case of a relative path, it will be expanded to an absolute path,
        whereas the folder of the config_file will be used to complete the path.
        """

        self.gen_files = expand_searchpaths(paths=self.gen_files, rel_path_reference=os.path.dirname(self.config_path))