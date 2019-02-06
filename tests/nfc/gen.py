import os.path
import numpy as np

from argparse import ArgumentParser
from math import sqrt

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, AnalogOutput, AnalogSignal, Deriv, DigitalInput, Case

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
    m = cfg.coupling*sqrt(cfg.ind_tx*cfg.ind_rx)

    # create the model
    model = MixedSignalModel('nfc', AnalogInput('v_in'), AnalogOutput('v_out'), DigitalInput('tx'),
                             DigitalInput('rx'), dt=cfg.dt)
    model.add_signal(AnalogSignal('i_ind_tx', 1.0))
    model.add_signal(AnalogSignal('i_ind_rx', 1.0))
    model.add_signal(AnalogSignal('v_cap_tx', 100))
    model.add_signal(AnalogSignal('v_cap_rx', 100))

    # internal signals
    v_ind_rx = AnalogSignal('v_ind_rx')
    v_ind_tx = AnalogSignal('v_ind_tx')

    # determine TX and RX resistances as a function of digital state
    res_tx = Case([cfg.res_tx_comm_0, cfg.res_tx_comm_1], sel_bits=[model.tx]) + cfg.res_coil_tx
    cond_load_rx = Case([cfg.cond_rx_comm_0, cfg.cond_rx_comm_1], sel_bits=[model.rx])

    # implement dynamics
    model.add_eqn_sys([
        # coupled inductor dynamics
        v_ind_tx == cfg.ind_tx * Deriv(model.i_ind_tx) + m * Deriv(model.i_ind_rx),
        v_ind_rx == m * Deriv(model.i_ind_tx) + cfg.ind_rx * Deriv(model.i_ind_rx),
        # capacitor dynamics
        Deriv(model.v_cap_tx) == +model.i_ind_tx/cfg.cap_tx,
        Deriv(model.v_cap_rx) == (-model.i_ind_rx - cond_load_rx*model.v_cap_rx)/cfg.cap_rx,
        # KVL
        model.v_in == res_tx*model.i_ind_tx + v_ind_tx + model.v_cap_tx,
        model.v_cap_rx == cfg.res_coil_rx*model.i_ind_rx + v_ind_rx,
        # output
        model.v_out == model.v_cap_rx
    ],
        internals=[v_ind_rx, v_ind_tx],
        inputs=[model.v_in],
        outputs=[model.v_out],
        states=[model.i_ind_tx, model.i_ind_rx, model.v_cap_tx, model.v_cap_rx],
        sel_bits=[model.rx, model.tx]
    )

    # probe signals of interest
    model.add_probe(model.i_ind_tx)
    model.add_probe(model.i_ind_rx)
    model.add_probe(model.v_cap_tx)
    model.add_probe(model.v_cap_rx)

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