import os.path
from argparse import ArgumentParser

from msdsl.model import MixedSignalModel
from msdsl.verilog import VerilogGenerator
from msdsl.expr import AnalogInput, DigitalInput, AnalogOutput, Case, Deriv, AnalogSignal

from anasymod.util import DictObject
from anasymod.files import get_full_path

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str)
    args = parser.parse_args()

    # load config options
    config_file_path = os.path.join(os.path.dirname(get_full_path(__file__)), 'config.json')
    cfg = DictObject.load_json(config_file_path)

    # create the model
    model = MixedSignalModel('buck', DigitalInput('hs'), DigitalInput('ls'), AnalogInput('v_in'), AnalogOutput('v_out'),
                             AnalogOutput('i_ind'), dt=cfg.dt)

    # internal state variable
    model.add_signal(AnalogSignal('v_snub', 1000))

    # dynamics
    i_snub = AnalogSignal('i_snub')
    v_sw = AnalogSignal('v_sw')

    cond_hs = Case([0, 1/cfg.r_sw], [model.hs])
    cond_ls = Case([0, 1/cfg.r_sw], [model.ls])

    model.add_eqn_sys([
        # Current into snubber capacitor
        i_snub == (v_sw - model.v_snub) / cfg.r_snub,

        # KCL at switch node
        (cond_hs*(model.v_in - v_sw)) == cond_ls*v_sw + i_snub + model.i_ind,

        # Inductor behavior
        Deriv(model.i_ind) == (v_sw - model.v_out)/cfg.ind,
        
        # Capacitors
        Deriv(model.v_snub) == i_snub/cfg.c_snub,
        Deriv(model.v_out) == (model.i_ind-model.v_out/cfg.r_load)/cfg.c_load
    ], states=[model.i_ind, model.v_out, model.v_snub], inputs=[model.v_in], sel_bits=[model.hs, model.ls],
       internals=[v_sw, i_snub]
    )

    # add probes
    model.add_probe(model.v_snub)

    # determine the output filename
    filename = os.path.join(get_full_path(args.output), 'buck.sv')
    print('Model will be written to: ' + filename)

    # generate the model
    model.compile_model(VerilogGenerator(filename))

if __name__ == '__main__':
    main()