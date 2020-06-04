class TemplXSCTBuild:
    def __init__(self, sdk_path, proc_name='ps7_cortexa9_0',
                 hw_name='hw', top_name='top', sw_name='sw'):

        self.text = f'''\
# set the work directory
setws "{sdk_path}"

# create the hardware configuration
createhw \\
    -name {hw_name} \\
    -hwspec "{sdk_path / top_name}.hdf"

# create the software configuration
createapp \\
    -name {sw_name} \\
    -hwproject {hw_name} \\
    -proc {proc_name} \\
    -app "Empty Application"

# build application
projects -build'''
