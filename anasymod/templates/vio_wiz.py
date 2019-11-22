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
            if isinstance(input, AnalogCtrlOutput):
                #ToDo: currently the width is set to 25 bit for all analog signals, this might be adjusted, ideally
                # value should be set from same souce as the real.sv define for LONG_WIDTH_REAL
                width = 25
            elif isinstance(input, DigitalCtrlOutput):
                width = input.width
            else:
                raise Exception(f"Provided signal type:{type(input)} is not supported!")

            props[f'CONFIG.C_PROBE_IN{k+0}_WIDTH'] = str(width)

        # handle output ports
        for k, output in enumerate([scfg.reset_ctrl] + [scfg.dec_thr_ctrl] + crtl_inputs):
            if isinstance(output, AnalogCtrlInput):
                # ToDo: currently the width is set to 25 bit for all analog signals, this might be adjusted, ideally
                #  value should be set from same souce as the real.sv define for LONG_WIDTH_REAL
                width = 25
            elif isinstance(output, DigitalCtrlInput):
                width = output.width
            else:
                raise Exception(f"Provided signal type:{type(output)} is not supported!")
            props[f'CONFIG.C_PROBE_OUT{k+0}_WIDTH'] = str(width)
            if output.init_value is not None:
                props[f'CONFIG.C_PROBE_OUT{k+0}_INIT_VAL'] = str(output.init_value)

        props['CONFIG.C_NUM_PROBE_IN'] = str(len(ctrl_outputs))
        props['CONFIG.C_NUM_PROBE_OUT'] = str(len([scfg.reset_ctrl] + [scfg.dec_thr_ctrl] + crtl_inputs))

        ####################################################
        # Prepare Template substitutions
        ####################################################

        super().__init__(ip_name='vio', ip_dir=ip_dir, props=props)

def main():
    from anasymod.targets import FPGATarget
    print(TemplVIO(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()