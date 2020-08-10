import os

from anasymod.viewer.viewer import Viewer
from anasymod.util import call

class GtkWaveViewer(Viewer):
    def view(self, result_file=None):
        vcd_path = result_file if result_file is not None else self.target.cfg.vcd_path

        # build command
        if os.path.isfile(vcd_path):
            cmd = [self.cfg.gtkwave_config.gtkwave, vcd_path]
            cmd[1:1] = self.cfg.gtkwave_config.lsf_opts.split()
            # add waveform file if it exists
            if self.cfg.gtkwave_config.gtkw_config is not None:
                if os.path.isfile(self.cfg.gtkwave_config.gtkw_config):
                    cmd.append(self.cfg.gtkwave_config.gtkw_config)

            # run command
            call(cmd)
        else:
            raise Exception(f'ERROR: Result file: {vcd_path} does not exist; cannot open waveforms!')