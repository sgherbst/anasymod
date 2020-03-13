import os

from anasymod.viewer.viewer import Viewer
from anasymod.util import call

class GtkWaveViewer(Viewer):
    def view(self):
        # build command
        if os.path.isfile(self.target.cfg.vcd_path):
            cmd = [self.cfg.gtkwave_config.gtkwave, self.target.cfg.vcd_path]
            cmd[1:1] = self.cfg.gtkwave_config.lsf_opts.split()
            # add waveform file if it exists
            if self.cfg.gtkwave_config.gtkw_config is not None:
                if os.path.isfile(self.cfg.gtkwave_config.gtkw_config):
                    cmd.append(self.cfg.gtkwave_config.gtkw_config)

            # run command
            call(cmd)
        else:
            raise Exception(f'ERROR: Result file: {self.target.cfg.vcd_path} does not exist; cannot open waveforms!')