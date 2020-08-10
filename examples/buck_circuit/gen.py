import os.path
from argparse import ArgumentParser

from msdsl import RangeOf, AnalogSignal, MixedSignalModel, VerilogGenerator
from anasymod import get_full_path

class BuckConverter(MixedSignalModel):
    def __init__(self, name='buck', dt=0.1e-6, ind=2.2e-6, c_load=10e-6, r_load=5.5, r_snub=300, c_snub=100e-12,
                 r_sw_on=1.0, r_sw_off=10e3):

        # call the super constructor
        super().__init__(name, dt=dt)

        self.add_digital_input('hs')
        self.add_digital_input('ls')
        self.add_analog_input('v_in')
        self.add_analog_output('v_out')
        self.add_analog_output('i_ind')

        # define the circuit
        c = self.make_circuit()
        gnd = c.make_ground()

        # input voltage
        c.voltage('net_v_in', gnd, self.v_in)

        # switches
        c.switch('net_v_in', 'net_v_sw', self.hs, r_on=r_sw_on, r_off=r_sw_off)
        c.switch('net_v_sw', gnd, self.ls, r_on=r_sw_on, r_off=r_sw_off)

        # snubber network
        v_snub = c.capacitor('net_v_sw', 'net_v_x', c_snub, voltage_range=10*RangeOf(self.v_out))
        c.resistor('net_v_x', gnd, r_snub)
        self.bind_name('v_snub', v_snub)
        self.add_probe(self.v_snub)

        # inductor + current measurement
        c.inductor('net_v_sw', 'net_v_l', ind, current_range=RangeOf(self.i_ind))
        i_ind = c.voltage('net_v_l', 'net_v_out', 0)

        # output load
        c.capacitor('net_v_out', gnd, c_load, voltage_range=RangeOf(self.v_out))
        c.resistor('net_v_out', gnd, r_load)

        # assign outputs
        c.add_eqns(
            self.v_out == AnalogSignal('net_v_out'),
            self.i_ind == i_ind
        )


def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = BuckConverter(dt=args.dt)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)


if __name__ == '__main__':
    main()
