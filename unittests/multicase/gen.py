import os.path
from argparse import ArgumentParser

from msdsl import MixedSignalModel, VerilogGenerator, AnalogInput, DigitalInput, AnalogOutput, eqn_case, Deriv
from anasymod import get_full_path

def main(tau=1e-6):
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    parser.add_argument('--dt', type=float)
    args = parser.parse_args()

    # create the model
    model = MixedSignalModel('filter', DigitalInput('ctrl'), AnalogInput('v_in'), AnalogOutput('v_out'), dt=args.dt)

    # define dynamics
    model.add_eqn_sys([
        Deriv(model.v_out) == eqn_case([0, 1/tau], [model.ctrl])*model.v_in - model.v_out/tau
    ])

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), f'{model.module_name}.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()