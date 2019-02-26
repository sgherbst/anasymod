import os
from anasymod.read_sources import Sources, VerilogSource, VerilogHeader, VHDLSource, SubConfig

class Filesets():
    def __init__(self, root, default_filesets: list):
        self.default_fileset_names = default_filesets
        self.config_path_key = [r"additional_config_paths"]

        self.master_cfg_path = os.path.join(root, 'source.config')

        self.sources = []
        """:type : List[Sources]"""

        self.fileset_dict = {}

        self.sub_config_paths = []
        """:type : List[SubConfig]"""

    def read_filesets(self, validate_paths=False):
        if os.path.isfile(self.master_cfg_path):
            with open(self.master_cfg_path, "r") as f:
                mcfg = f.readlines()

            # Read source paths from master config
            self._parseconfig(cfg=mcfg, cfg_path=self.master_cfg_path)

            # Read source paths from sub configs
            while (bool(self.sub_config_paths)):
                for config in self.sub_config_paths:
                    self.sub_config_paths.remove(config)
                    for file in config.files:
                        if os.path.isfile(file):
                            with open(file, "r") as f:
                                cfg = f.readlines()
                            self._parseconfig(cfg=cfg, cfg_path=file)
                        else:
                            print(f"WARNING: provided path:'{config_path}' does not exist, skipping config file")

                #config_paths = self.sub_config_paths
                #self.sub_config_paths = []
                #for config_path in config_paths:
                #    if os.path.isfile(config_path):
                #        with open(config_path, "r") as f:
                #            cfg = f.readlines()
                #        self._parseconfig(cfg=cfg, cfg_path=config_path)
                #    else:
                #        print(f"WARNING: provided path:'{config_path}' does not exist, skipping config file")

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
        Read all line from config file, according to string infront of '=' sign, the proceeding arguments will either
        be added to the according fileset or will be added to the list of additional config paths, which will be
        investigated in the next iteration.
        :param cfg:
        :param cfg_path:
        :return:
        """

        #source_v = []
        #files_v = []

        #with(open(os.path.join(args.input, r"source.config"), 'r')) as f:
        #    lines = f.readlines()
        #    for line in lines:
        #        if isinstance(eval(line), Sources):
        #            source_v.append(eval(line))

        for line in cfg:
            line = line.strip()
            if line:
                try:
                    line = eval(line)
                #line_split = line.split(r"=")
                #if len(line_split) is not 2:
                #    raise KeyError(f"Too many '=' in line:{line}")
                #if not(line_split[1] is ''):
                    if isinstance(line, Sources):
                        line.config_path = cfg_path
                        self.sources.append(line)
                    elif isinstance(line, SubConfig):
                        line.config_path = cfg_path
                        self.sub_config_paths.append(line)
                except:
                    print(f"Warning: Line'{line}' of config file: {cfg_path} could not be processed properely")

                    #fileset_name = line_split[0].strip()
                    #fileset_paths = line_split[1].split(",")
                    #if fileset_name in self.fileset_dict.keys():
                    #    self.fileset_dict[fileset_name] += self._expand_paths(paths=fileset_paths, cfg_path=cfg_path)
                    #elif fileset_name in self.config_path_key:
                    #    self.sub_config_paths += self._expand_paths(paths=fileset_paths, cfg_path=cfg_path)
                    #else:
                    #    print(f"Custom fileset was added:{fileset_name}")
                    #    self.fileset_dict[fileset_name] = self._expand_paths(paths=fileset_paths, cfg_path=cfg_path)

    #def _expand_paths(self, paths: list, cfg_path: str):
    #    """
    #    Expand environment variables in provided list of paths.
    #    Check if path is absolute or relative, in case of a relative path, it will be expanded to an absolute path,
    #    whereas the folder of the config_file will be used to complete the path.
    #    :param paths:
    #    :param cfg_path:
    #    :return:
    #    """
    #    abs_paths = []
    #    if not isinstance(paths, list):
    #        raise TypeError(f"Wrong format used in config file {cfg_path}")
    #    for path in paths:
    #        path = os.path.expandvars(path.strip('" '))
    #        if not os.path.isabs(path):
    #            path = os.path.join(os.path.dirname(cfg_path), "".join(path.replace('\\', '/').replace('/', os.sep).split(os.sep)[1:]))
    #        abs_paths.append(path)
    #    return abs_paths

    def create_filesets(self):
        """
        Creates fileset attributes according to filesets that were provided reading in sourcefiles.
        Previously craeted filesets will be overwritten.
        :return:
        """

        for source in self.sources:
            if source.fileset in self.fileset_dict.keys():
                self.fileset_dict[source.fileset].append(source)
            else:
                print(f"Custom fileset was added:{source.fileset}")
                self.fileset_dict[source.fileset] = [source]


def main():
    fileset = Filesets(root=r"C:\Inicio_dev\anasymod\tests\filter")
    fileset.read_filesets()
    print(fileset.fileset_dict)

if __name__ == '__main__':
    main()