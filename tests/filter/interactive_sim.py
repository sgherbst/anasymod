from anasymod.analysis import Analysis
import os

root = os.path.dirname(__file__)

ana = Analysis(input=root)

# Generate Bitstream for Project
ana.msdsl.models()
ana.setup_filesets()
ana.set_target(target_name='fpga')
ana.build()

# Start Interactive Control