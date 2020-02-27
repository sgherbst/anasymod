import os

from anasymod.analysis import Analysis
from argparse import ArgumentParser

from time import sleep
from math import exp

root = os.path.dirname(__file__)

ANALOG_EXPONENT = -18

def float_to_fixed(x):
    return int(x * (2.0**(-ANALOG_EXPONENT)))

def fixed_to_float(x):
    return x * (2.0**(ANALOG_EXPONENT))

def parse():
    parser = ArgumentParser()
    parser.add_argument('--gen_bitstream', action='store_true')
    return parser.parse_args()

def main():
    args = parse()
    ana = Analysis(input=root)                              # create analysis object to host prototyping project

    ana.msdsl.models()                                      # generate functional models
    ana.setup_filesets()                                    # setup project's filesets
    ana.set_target(target_name='fpga')                      # set the active target to 'fpga'

    if args.gen_bitstream:
        ana.build()                                         # generate bitstream for project

    ctrl_handle = ana.launch(debug=True)                    # start interactive control

    # routine to pulse clock
    def pulse_clock():
        ctrl_handle.set_param(name='go_vio', value=0b1)
        sleep(0.1)
        ctrl_handle.set_param(name='go_vio', value=0b0)
        sleep(0.1)

    # program FPGA
    print('Programming FPGA.')
    ctrl_handle.source('program.tcl')

    # reset emulator
    ctrl_handle.set_reset(1)
    sleep(0.1)
    ctrl_handle.set_reset(0)
    sleep(0.1)

    # reset everything else
    ctrl_handle.set_param(name='go_vio', value=0)
    ctrl_handle.set_param(name='rst_vio', value=1)
    ctrl_handle.set_param(name='v_in_vio', value=float_to_fixed(1.0))

    # pulse the clock
    pulse_clock()

    # release from reset
    ctrl_handle.set_vio(name='rst_vio', value=0)
    sleep(0.1)

    # walk through simulation values
    t_sim = 0.0
    tau = 1.0e-6
    abs_tol = 1e-3
    for _ in range(25):
        # get readings
        ctrl_handle.refresh_param('vio_0_i')
        v_out_vio = fixed_to_float(int(ctrl_handle.get_param('v_out_vio')))

        # print readings
        print(f't_sim: {t_sim}, v_out_vio: {v_out_vio}')

        # check results
        meas_val = v_out_vio
        expt_val = 1.0 - exp(-t_sim / tau)
        assert (expt_val - abs_tol) <= meas_val <= (expt_val + abs_tol), 'Measured value is out of range.'

        # pulse clock
        pulse_clock()

        # update the time variable
        t_sim += 0.1e-6

if __name__ == "__main__":
    main()