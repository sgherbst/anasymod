import os

class Filesets():
    def __init__(self, root):
        self.fileset_names = [r"sim_only_verilog_sources", r"synth_only_verilog_sources", r"verilog_sources",
                         r"sim_only_verilog_headers", r"synth_only_verilog_headers", r"verilog_headers"]
        self.config_path_key = [r"additional_config_paths"]

        self.master_cfg_path = os.path.join(root, r"source.config")

        self.source_dict = {}
        for fileset_name in self.fileset_names:
            self.source_dict[fileset_name] = []

        self.sub_config_paths = []

    def read_filesets(self, validate_paths=False):
        if os.path.isfile(self.master_cfg_path):
            with open(self.master_cfg_path, "r") as f:
                mcfg = f.readlines()

            # Read source paths from master config
            self._parseconfig(cfg=mcfg, cfg_path=self.master_cfg_path)

            # Read source paths from sub configs
            while (bool(self.sub_config_paths)):
                config_paths = self.sub_config_paths
                self.sub_config_paths = []
                for config_path in config_paths:
                    if os.path.isfile(config_path):
                        with open(config_path, "r") as f:
                            cfg = f.readlines()
                        self._parseconfig(cfg=cfg, cfg_path=config_path)
                    else:
                        print(f"WARNING: provided path:'{config_path}' does not exist, skipping config file")

            # Check if fileset paths exist
            if validate_paths:
                for key in self.source_dict.keys():
                    for path in self.source_dict[key]:
                        if not os.path.exists(path):
                            raise ValueError(f"Provided path:{path} of fileset:{key} does not exist")
        else:
            print(f"No config file existing, skipping to real source files.")

    def _parseconfig(self, cfg: list, cfg_path: str):
        """
        Read all line from config file, according to string infront of '=' sign, the proceeding arguments will either
        be added to the according fileset or will be added to the list of additional config paths, which will be
        investigated in the next iteration.
        :param cfg:
        :param cfg_path:
        :return:
        """
        for line in cfg:
            line = line.strip()
            if line:
                line_split = line.split(r"=")
                if len(line_split) is not 2:
                    raise KeyError(f"Too many '=' in line:{line}")
                if not(line_split[1] is ''):
                    line_name = line_split[0].strip()
                    line_paths = line_split[1].split(",")
                    if line_name in self.fileset_names:
                        self.source_dict[line_name] += self._expand_paths(paths=line_paths, cfg_path=cfg_path)
                    elif line_name in self.config_path_key:
                        self.sub_config_paths += self._expand_paths(paths=line_paths, cfg_path=cfg_path)

    def _expand_paths(self, paths: list, cfg_path: str):
        """
        Expand environment variables in provided list of paths.
        Check if path is absolute or relative, in case of a relative path, it will be expanded to an absolute path,
        whereas the folder of the config_file will be used to complete the path.
        :param paths:
        :param cfg_path:
        :return:
        """
        abs_paths = []
        if not isinstance(paths, list):
            raise TypeError(f"Wrong format used in config file {cfg_path}")
        for path in paths:
            path = os.path.expandvars(path.strip('" '))
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(cfg_path), "".join(path.replace('\\', '/').replace('/', os.sep).split(os.sep)[1:]))
            abs_paths.append(path)
        return abs_paths

def main():
    fileset = Filesets(root=r"C:\Inicio_dev\anasymod\tests\filter")
    fileset.read_filesets()
    print(fileset.source_dict)

if __name__ == '__main__':
    main()