import pytest
import importlib
import numpy as np
from pathlib import Path

root = Path(__file__).resolve().parent

from ..common import run_simulation, run_emulation, CommonArgParser, DEFAULT_SIMULATOR

def test_func_sim(simulator_name=DEFAULT_SIMULATOR):
    run_simulation(root=root, simulator_name=simulator_name)

@pytest.mark.skip(
   reason="This test takes a long time to run and largely covers the same features as test_rc."
)
@pytest.mark.skipif(not importlib.util.find_spec("cvxpy"),
                    reason="cvxpy is not available in python distribution")
def test_func_emu(gen_bitstream=True, emulate=True):
    run_emulation(root=root, gen_bitstream=gen_bitstream,
                  emu_ctrl_fun=emu_ctrl_fun, emulate=emulate)

def emu_ctrl_fun(ctrl):
    # reset emulator
    ctrl.set_reset(1)
    ctrl.set_reset(0)

    # reset everything else
    ctrl.set_param(name='in_', value=0.0)

    # save the outputs
    inpts = np.random.uniform(-1.2 * np.pi, +1.2 * np.pi, 100)
    apprx = np.zeros(shape=inpts.shape, dtype=float)
    for k, in_ in enumerate(inpts):
        ctrl.set_param(name='in_', value=in_)
        ctrl.refresh_param('vio_0_i')
        apprx[k] = ctrl.get_param('out')

    # compute the exact response to inputs
    def myfunc(x):
        # clip input
        x = np.clip(x, -np.pi, +np.pi)
        # apply function
        return np.sin(x)
    exact = myfunc(inpts)

    # check the result
    err = np.sqrt(np.mean((exact - apprx)**2))
    assert err <= 0.001

if __name__ == '__main__':
    CommonArgParser(sim_fun=test_func_sim, emu_fun=test_func_emu)
