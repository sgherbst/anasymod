import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from msdsl import MixedSignalModel, VerilogGenerator

def myfunc(x):
    # clip input
    x = np.clip(x, -np.pi, +np.pi)
    # apply function
    return np.sin(x)

def gen_model(order, numel, build_dir):
    # settings:
    # order=0, numel=512 => rms_error <= 0.0600
    # order=1, numel=128 => rms_error <= 0.0012
    # order=2, numel= 32 => rms_error <= 0.0010

    # create mixed-signal model
    m = MixedSignalModel('model', build_dir=build_dir)
    m.add_analog_input('in_')
    m.add_analog_output('out')

    # create function
    real_func = m.make_function(myfunc, domain=[-np.pi, +np.pi],
                                order=order, numel=numel)

    # apply function
    # TODO: clean up with update to MSDSL
    class ce:
        name = '`CKE_MSDSL'
    m.set_from_sync_func(m.out, real_func, m.in_, ce=ce)

    # write the model
    return m.compile_to_file(VerilogGenerator())

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='build')
    parser.add_argument('--dt', type=float, default=0.1e-6)
    parser.add_argument('--order', type=int, default=2)
    parser.add_argument('--numel', type=int, default=32)

    # parse arguments
    args = parser.parse_args()

    # call the model generator
    build_dir = Path(args.output).resolve()
    gen_model(order=args.order, numel=args.numel, build_dir=build_dir)

if __name__ == '__main__':
    main()
