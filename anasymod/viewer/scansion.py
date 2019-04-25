from anasymod.viewer.viewer import Viewer
from anasymod.util import call

class ScansionViewer(Viewer):
    def view(self):
        # build command
        #cmd = ['open', '/Applications/Scansion.app', self.target.cfg['vcd_path']]
        cmd = ['open', '/Applications/Scansion.app']

        # run command
        call(cmd)