from anasymod.templates.generic_ip import TemplGenericIp
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig
from anasymod.sim_ctrl.datatypes import DigitalCtrlInput, DigitalCtrlOutput, DigitalSignal, AnalogSignal, AnalogCtrlInput, AnalogCtrlOutput

class TemplVIO(TemplGenericIp):
    def __init__(self, scfg: StructureConfig, ip_dir):

        ####################################################
        # Generate ip core config for vio wizard
        ####################################################

        crtl_inputs = scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs
        ctrl_outputs = scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs

        props = {}

        # handle input ports
        for k, input in enumerate(ctrl_outputs):
            # check that the signal type can be handled
            if not isinstance(input, (AnalogCtrlOutput, DigitalCtrlOutput)):
                raise Exception(f"Provided signal type:{type(input)} is not supported!")
            # set signal width
            props[f'CONFIG.C_PROBE_IN{k+0}_WIDTH'] = str(input.width)

        # handle output ports
        for k, output in enumerate(crtl_inputs):
            # check that the signal type can be handled
            if not isinstance(output, (AnalogCtrlInput, DigitalCtrlInput)):
                raise Exception(f"Provided signal type:{type(output)} is not supported!")
            # set signal width
            props[f'CONFIG.C_PROBE_OUT{k + 0}_WIDTH'] = str(output.width)
            # set initial value of probe
            if output.init_value is not None:
                init_value = output.init_value
                if isinstance(output, AnalogCtrlInput):
                    init_value = output.float_to_fixed(init_value)
                props[f'CONFIG.C_PROBE_OUT{k+0}_INIT_VAL'] = str(init_value)

        props['CONFIG.C_NUM_PROBE_IN'] = str(len(ctrl_outputs))
        props['CONFIG.C_NUM_PROBE_OUT'] = str(len(crtl_inputs))

        ####################################################
        # Prepare Template substitutions
        ####################################################

        super().__init__(ip_name='vio', ip_dir=ip_dir, props=props)

def main():
    from anasymod.targets import FPGATarget
    print(TemplVIO(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()