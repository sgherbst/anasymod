from anasymod.templates.generic_ip import TemplGenericIp
from anasymod.util import next_pow_2
from anasymod.targets import FPGATarget

class TemplILA(TemplGenericIp):
    def __init__(self, target: FPGATarget, depth=4096):
        # set defaults

        # Sanity checking for ILA depth
        assert next_pow_2(depth) == depth, 'The ILA depth must be a power of 2.'
        assert depth >= 1024, 'The ILA depth must be at least 1024.'

        self.inst_name = target.prj_cfg.vivado_config.ila_inst_name

        self.width_ila_clk = '1'
        self.conn_ila_clk = target.str_cfg.clk_m[0].name

        props = {}

        # set the number samples per signal
        props['C_DATA_DEPTH'] = str(depth)

        # add a pipelined input to reduce burden on timing closure
        props['C_INPUT_PIPE_STAGES'] = '1'

        # enable capture control
        props['C_EN_STRG_QUAL'] = 'true'

        # two comparators per probe are recommended when using capture control (per UG908, p 40)
        props['ALL_PROBE_SAME_MU_CNT'] = '2'

        # specify all signals to be probed
        self.probes = {}
        signals = target.str_cfg.probes
        print(f"Signals: {[f'{signal.name}' for signal in signals]}")

        # Set number of probes in total
        props['ALL_PROBE_SAME_MU_CNT'] = str(len(signals))

        for k, signal in enumerate(signals):
            # Add depth for ila signal
            props[f'C_PROBE{k}_WIDTH'] = str(signal.width)

        super().__init__(ip_name='ila', props=props, ip_dir=target.ip_dir)


def main():
    print(TemplILA(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()