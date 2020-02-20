from anasymod.enums import ConfigSections

class BaseConfig():
    """
    Base class for a config container class. Includes all the base functions that shall be applicable on a config class,
    e.g. update from the prj_config file, read from prj_config file ... .
    """

    def __init__(self, cfg_file: dict, section):
        self.cfg_file = cfg_file
        if section in ConfigSections.__dict__.keys():
            self.section = section
        else:
            raise KeyError(f"provided section key:{section} is not supported")

    def update_config(self, subsection=None):
        """ Update config by entries from config file; datatype is a dict.
        Using subsection argument, it is possible to read an object specific config section, this
        is necessary if multiple objects of one class are in use, e.g. for multiple targets.

        :param subsection: subsection to use from config file
        """
        if self.cfg_file is not None:
            if self.section in self.cfg_file:
                if subsection is not None:
                    config_section = self.cfg_file[self.section].get(subsection)
                else:
                    config_section = self.cfg_file.get(self.section)

                # update attributes from config class
                if config_section is not None:
                    for k, v in config_section.items():
                        if hasattr(self, k):
                            setattr(self, k, v)
                        else:
                            print(f"Warning: Processing config section:{config_section}; provided key: {k} does not exist in config")
