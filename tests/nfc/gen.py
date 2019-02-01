import os.path
import numpy as np

from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, AnalogSignal, DigitalSignal

from anasymod.util import DictObject

from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', default='.', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = DictObject.load_json(config_file_path)

    # calculate derived parameters
    m = cfg.coupling*sqrt(cfg.l_tx*cfg.l_rx)

    # create the model
    model = MixedSignalModel('nfc', AnalogInput('v_in'), AnalogOutput('v_out'), dt=cfg.dt)
    model.add_signal(AnalogSignal('i_tx', 1))
    model.add_signal(AnalogSignal('i_rx', 1))
    model.add_signal(AnalogSignal('v_res_tx', 10))
    model.add_signal(AnalogSignal('v_res_rx', 1000))

    # model dynamics

    # build up the dynamics matrices
    # input: v_in
    # states: [i_tx, i_rx, v_res_tx, v_res_rx]
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)

    a = (1/(cfg.l_tx-m**2))
    b = m/(cfg.l_rx*(cfg.l_tx-m**2))
    c = (1/(cfg.l_rx-m**2))
    d = m/(cfg.l_tx*(cfg.l_rx-m**2))

    A[0, :] = np.array([-a*cfg.r_q_tx, +b*cfg.r_q_rx, -a, -b])
    A[1, :] = np.array([+d*cfg.r_q_tx, -c*cfg.r_q_rx, +d, +c])
    A[2, :] = np.array([+1/cfg.c_res_tx, 0, 0, 0])
    A[3, :] = np.array([0, -1/cfg.c_res_rx, 0, 0])

    B[0, 0] = +a
    B[1, 0] = -d
    B[2, 0] = 0
    B[3, 0] = 0

    model.add_lds((A, B, 0, 0), inputs=[model.v_in], states=[model.i_tx, model.i_rx, model.v_res_tx, model.v_res_rx])

    # coils
    #model.set_deriv(model.i_tx, (1/(cfg.l_tx-m**2))*model.v_tx - (m/(cfg.l_rx*(cfg.l_tx-m**2))*model.v_rx))
    #model.set_deriv(model.i_rx, (1/(cfg.l_rx-m**2))*model.v_rx - (m/(cfg.l_tx*(cfg.l_rx-m**2))*model.v_tx))
    #model.set_deriv(model.v_res_tx, model.i_tx/cfg.c_res_tx)
    #model.set_deriv(model.v_res_rx, -model.i_rx/cfg.c_res_rx)
    #model.set_this_cycle(model.v_tx, model.v_in - cfg.r_q_tx*model.i_tx - model.v_res_tx)
    #model.set_this_cycle(model.v_rx, model.v_res_rx - cfg.r_q_rx*model.i_rx)

    # model output
    model.set_this_cycle(model.v_out, model.v_res_tx)

    # probe signals of interest
    model.add_probe(model.i_tx)
    model.add_probe(model.i_rx)
    model.add_probe(model.v_res_tx)
    model.add_probe(model.v_res_rx)

    # determine the output filename
    if args.output is not None:
        filename = os.path.join(get_full_path(args.output), 'nfc.sv')
        print('Model will be written to: ' + filename)
    else:
        filename = None

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()