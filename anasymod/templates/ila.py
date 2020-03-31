from anasymod.templates.generic_ip import TemplGenericIp
from anasymod.util import next_pow_2
from anasymod.targets import FPGATarget

class TemplILA(TemplGenericIp):
    def __init__(self, target: FPGATarget, depth=4096):
        # set defaults
        scfg = target.str_cfg

        # Sanity checking for ILA depth
        assert next_pow_2(depth) == depth, 'The ILA depth must be a power of 2.'
        assert depth >= 1024, 'The ILA depth must be at least 1024.'

        self.inst_name = target.prj_cfg.vivado_config.ila_inst_name

        self.width_ila_clk = '1'
        self.conn_ila_clk = target.str_cfg.emu_clk.name

        props = {}

        # set the number samples per signal
        props['CONFIG.C_DATA_DEPTH'] = str(depth)

        # add a pipelined input to reduce burden on timing closure
        props['CONFIG.C_INPUT_PIPE_STAGES'] = '1'

        # enable capture control
        props['CONFIG.C_EN_STRG_QUAL'] = 'true'

        # two comparators per probe are recommended when using capture control (per UG908, p 40)
        props['CONFIG.ALL_PROBE_SAME_MU_CNT'] = '2'

        # specify all signals to be probed
        signals = (scfg.digital_probes + scfg.analog_probes + [target.str_cfg.time_probe] +
                   [target.str_cfg.dec_cmp])
        print(f"Signals: {[f'{signal.name}' for signal in signals]}")

        # Set number of probes in total
        props['CONFIG.C_NUM_OF_PROBES'] = str(len(signals))

        for k, signal in enumerate(signals):
            # Add depth for ila signal
            props[f'CONFIG.C_PROBE{k}_WIDTH'] = str(signal.width)

        super().__init__(ip_name='ila', props=props, ip_dir=target.ip_dir)


def main():
    print(TemplILA(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()