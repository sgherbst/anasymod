import os

from anasymod.viewer.viewer import Viewer
from anasymod.util import call

class SimVisionViewer(Viewer):
    def view(self):
        # build command
        if os.path.isfile(self.target.cfg.vcd_path):
            cmd = [self.cfg.simvision_config.simvision, '-wave', self.target.cfg.vcd_path]
            cmd[1:1] = self.cfg.simvision_config.lsf_opts.split()
            # add waveform file if it exists
            if self.cfg.simvision_config.svcf_config is not None:
                if os.path.isfile(self.cfg.simvision_config.svcf_config):
                    cmd.extend(['-input', self.cfg.simvision_config.svcf_config])

            # run command
            call(cmd)
        else:
            raise Exception(f'ERROR: Result file: {self.target.cfg.vcd_path} does not exist; cannot open waveforms!')