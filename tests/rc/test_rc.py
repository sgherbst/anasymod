import os
import pytest

from time import sleep
from math import exp

from ..common import run_simulation, run_emulation, CommonArgParser, DEFAULT_SIMULATOR

root = os.path.dirname(__file__)

def test_rc_sim(simulator_name=DEFAULT_SIMULATOR):
    run_simulation(root=root, simulator_name=simulator_name)

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_rc_emu(gen_bitstream=True):
    run_emulation(root=root, gen_bitstream=gen_bitstream, emu_ctrl_fun=emu_ctrl_fun)

def emu_ctrl_fun(ctrl):
    # routine to pulse clock
    def pulse_clock():
        ctrl.set_param(name='go_vio', value=0b1)
        sleep(0.1)
        ctrl.set_param(name='go_vio', value=0b0)
        sleep(0.1)

    # reset emulator
    ctrl.set_reset(1)
    sleep(0.1)
    ctrl.set_reset(0)
    sleep(0.1)

    # reset everything else
    ctrl.set_param(name='go_vio', value=0)
    ctrl.set_param(name='rst_vio', value=1)
    ctrl.set_param(name='v_in', value=1.0)

    # pulse the clock
    pulse_clock()

    # release from reset
    ctrl.set_param(name='rst_vio', value=0)
    sleep(0.1)

    # walk through simulation values
    t_sim = 0.0
    tau = 1.0e-6
    abs_tol = 1e-3
    for _ in range(25):
        # get readings
        ctrl.refresh_param('vio_0_i')
        v_out = ctrl.get_param('v_out')

        # print readings
        print(f't_sim: {t_sim}, v_out: {v_out}')

        # check results
        meas_val = v_out
        expt_val = 1.0 - exp(-t_sim / tau)
        assert (expt_val - abs_tol) <= meas_val <= (expt_val + abs_tol), 'Measured value is out of range.'

        # pulse clock
        pulse_clock()

        # update the time variable
        t_sim += 0.1e-6

if __name__ == '__main__':
    CommonArgParser(sim_fun=test_rc_sim, emu_fun=test_rc_emu)
