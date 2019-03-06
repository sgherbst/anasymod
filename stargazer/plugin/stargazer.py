
from argparse import ArgumentParser

from anasymod.enums import ConfigSections
from anasymod.plugins import Plugin
from anasymod.util import read_config, update_config

class CustomPlugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='stargazer')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize stargazer config

        # Update stargazer config with stargazer section in config file
        self.cfg = update_config(cfg=self.cfg, config_section=read_config(cfg_file=self._cfg_file, section=ConfigSections.PLUGIN, subsection=self._name))

        # Add defines according to command line arguments

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # gaze
        if self.args.gaze:
            self.gaze()

        # Setup Defines; after this step, defines shall not be added anymore in MSDSL

##### Functions exposed for user to exercise on Analysis Object

    def gaze(self):
        """
        Convert primitives in starlib into a synthesizable form.
        """
        pass

##### Utility Functions

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--gaze', action='store_true')

        self.args, _ = parser.parse_known_args()