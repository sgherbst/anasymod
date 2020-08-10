import os.path
from argparse import ArgumentParser

from msdsl import MixedSignalModel, VerilogGenerator, AnalogInput, AnalogOutput, AnalogSignal, Deriv
from anasymod import get_full_path

def main(cap=0.16e-6, ind=0.16e-6, res=0.1):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = MixedSignalModel('rlc', AnalogInput('v_in'), AnalogOutput('v_out'), dt=args.dt)
    model.add_analog_state('i_ind', 100)

    # internal variables
    v_l = AnalogSignal('v_l')
    v_r = AnalogSignal('v_r')

    # define dynamics
    eqns = [
        Deriv(model.i_ind) == v_l/ind,
        Deriv(model.v_out) == model.i_ind / cap,
        v_r == model.i_ind*res,
        model.v_in == model.v_out + v_l + v_r
    ]
    model.add_eqn_sys(eqns)

    # define probes
    #model.add_probe(model.i_ind)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()