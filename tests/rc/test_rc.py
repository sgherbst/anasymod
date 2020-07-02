import os
import pytest
from pathlib import Path
from math import exp

root = Path(__file__).resolve().parent

from ..common import run_simulation, run_emulation, CommonArgParser, DEFAULT_SIMULATOR

def test_rc_sim(simulator_name=DEFAULT_SIMULATOR):
    run_simulation(root=root, simulator_name=simulator_name)

@pytest.mark.skipif(
    'FPGA_SERVER' not in os.environ,
    reason='The FPGA_SERVER environment variable must be set to run this test.'
)
def test_rc_emu(gen_bitstream=True, emulate=True):
    run_emulation(root=root, gen_bitstream=gen_bitstream,
                  emu_ctrl_fun=emu_ctrl_fun, emulate=emulate)

def emu_ctrl_fun(ctrl, v_in=1.0, n_steps=25, dt=0.1e-6, tau=1.0e-6, abs_tol=1e-3):
    # initialize values
    ctrl.stall_emu()
    ctrl.set_param(name='v_in', value=v_in)

    # reset emulator
    ctrl.set_reset(1)
    ctrl.set_reset(0)

    # walk through simulation values
    for _ in range(n_steps):
        # get readings
        ctrl.refresh_param('vio_0_i')
        v_out = ctrl.get_param('v_out')
        t_sim = ctrl.get_emu_time()

        # print readings
        print(f't_sim: {t_sim}, v_out: {v_out}')

        # check results
        meas_val = v_out
        expt_val = v_in*(1 - exp(-t_sim/tau))
        assert (expt_val - abs_tol) <= meas_val <= (expt_val + abs_tol), \
            'Measured value is out of range.'

        # wait a certain amount of time
        ctrl.sleep_emu(dt)

if __name__ == '__main__':
    CommonArgParser(sim_fun=test_rc_sim, emu_fun=test_rc_emu)
