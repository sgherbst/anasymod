from anasymod.blocks.generic_ip import TemplGenericIp

class VioInput:
    def __init__(self, width=1):
        self.width = width

class VioOutput:
    def __init__(self, width=1, init=None):
        self.width = width
        self.init = init

class TemplVIO(TemplGenericIp):
    def __init__(self, ip_dir, inputs=None, outputs=None, ip_module_name=None):
        # set defaults
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        # initialize VIO properties
        props = {}

        # handle input
        props['CONFIG.C_NUM_PROBE_IN'] = str(len(inputs))
        for k, input in enumerate(inputs):
            props[f'CONFIG.C_PROBE_IN{k}_WIDTH'] = str(input.width)

        # handle output
        props['CONFIG.C_NUM_PROBE_OUT'] = str(len(outputs))
        for k, output in enumerate(outputs):
            if output.init is not None:
                props[f'CONFIG.C_PROBE_OUT{k}_INIT_VAL'] = str(output.init)
            props[f'CONFIG.C_PROBE_OUT{k}_WIDTH'] = str(output.width)

        super().__init__('vio', ip_dir=ip_dir, props=props, ip_module_name=ip_module_name)

def main():
    print(TemplVIO('ip_dir', [], [1]).render())

if __name__ == "__main__":
    main()