# general imports
import yaml
import numpy as np
from math import floor
from scipy.interpolate import interp1d
from pathlib import Path
from argparse import ArgumentParser

# msdsl imports
from msdsl import VerilogGenerator
from svreal import RealType
from msdsl.templates.lds import CTLEModel
from msdsl.templates.saturation import SaturationModel
from msdsl.templates.channel import ChannelModel
from msdsl.rf import s4p_to_step
from msdsl.templates.uniform import UniformRandom
from msdsl.templates.oscillator import OscillatorModel

# anasymod imports
from anasymod.analysis import Analysis

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'
TOP_DIR = THIS_DIR.parent.parent

def run_target(target, interactive=False, debug=False):
    if target.startswith('models'):
        create_models()
    elif target.startswith('sim'):
        simulator = target.split('_')[1]
        ana = setup_target('sim', simulator=simulator)
        ana.simulate()
    elif target.startswith('build'):
        ana = setup_target('fpga', synthesizer='vivado')
        ana.build()
    elif target.startswith('emulate'):
        ana = setup_target('fpga', synthesizer='vivado')
        if interactive:
            return ana.launch(debug=debug)
        else:
            ana.emulate()
    else:
        raise Exception(f'Unsupported target: {target}')


def setup_target(target, simulator=None, synthesizer=None, viewer=None):
    ana = Analysis(input=str(THIS_DIR), build_root=str(BUILD_DIR),
                   simulator_name=simulator, synthesizer_name=synthesizer,
                   viewer_name=viewer)
    (BUILD_DIR / 'models').mkdir(exist_ok=True, parents=True)
    ana.set_target(target_name=target)
    return ana


def create_models(ui=62.5e-12, gbw=40e9, npts=4, func_numel=512, dt_width=32, dt_scale=1e-15,
                  real_type=RealType.FixedPoint):
    print('Running model generator...')

    # generate channel step response
    t_orig, v_orig = s4p_to_step(TOP_DIR / 'peters_01_0605_B1_thru.s4p', dt=0.1e-12, T=10e-9)
    t_step = np.linspace(2e-9, 6e-9, func_numel)
    v_step = interp1d(t_orig, v_orig)(t_step)
    t_step -= t_step[0]

    # calculate number of terms needed for memory
    t_dur = t_step[-1] - t_step[0]
    num_terms = int(round(0.6 * t_dur/ui))
    print(f'num_terms: {num_terms}')

    # list of all modules to be generated
    models = [
        ('unfm', UniformRandom, dict(real_type=real_type)),
        ('osc', OscillatorModel, dict(
            dt_width=dt_width, dt_scale=dt_scale, init=int(floor(ui/dt_scale)), real_type=real_type)),
        ('ctle1', CTLEModel, dict(fz=0.8e9, fp1=1.6e9, gbw=gbw, num_spline=npts, dtmax=ui, real_type=real_type)),
        ('ctle2', CTLEModel, dict(fz=3.5e9, fp1=7e9, gbw=gbw, num_spline=npts, dtmax=ui, real_type=real_type)),
        ('ctle3', CTLEModel, dict(fz=5e9, fp1=10e9, gbw=gbw, num_spline=npts, dtmax=ui, real_type=real_type)),
        ('nonlin', SaturationModel, dict(compr=-1, units='dB', veval=1.0, numel=64, real_type=real_type)),
        ('channel', ChannelModel, dict(t_step=t_step, v_step=v_step, dtmax=ui, num_spline=npts, num_terms=num_terms,
                                       func_order=1, func_numel=func_numel, real_type=real_type))
    ]

    # generate modules
    for module_name, module_cls, module_kwargs in models:
        print(f'Building model: {module_name}')
        build_dir = BUILD_DIR / module_name
        build_dir.mkdir(exist_ok=True, parents=True)
        model = module_cls(**module_kwargs, module_name=module_name, build_dir=build_dir, clk='emu_clk', rst='emu_rst')
        model.compile_to_file(VerilogGenerator())

    # generate simctrl.yaml
    generate_sim_ctrl(npts=npts)

def generate_sim_ctrl(npts):
    # generate simctrl
    simctrl = {'analog_probes': {}, 'digital_probes': {}, 'analog_ctrl_inputs': {}}
    for sig, rng in [
        ('chan_o', 1.5),
        ('ctle1_o', 1.5),
        ('nl1_o', 1.5),
        ('ctle2_o', 1.5),
        ('nl2_o', 1.5),
        ('ctle3_o', 1.5),
        ('nl3_o', 1.5)
    ]:
        for k in range(npts):
            simctrl['analog_probes'][f'{sig}_{k}'] = {'abspath': f'tb_i.{sig}_{k}', 'range': rng}
    for sig, path, rng in [
        ('tx_drv_o', 'tx_drv_o', 1.1),
        ('dt_rel', 'dt_rel', 1.1),
        ('dt', 'dt', 62.5e-12)
    ]:
        simctrl['analog_probes'][sig] = {'abspath': f'tb_i.{path}', 'range': rng}
    for sig, path, rng, init in [
        ('tlo', 'tlo', 62.5e-12, 62.5e-12),
        ('thi', 'thi', 62.5e-12, 62.5e-12)
    ]:
        simctrl['analog_ctrl_inputs'][sig] = {'abspath': f'tb_i.{sig}', 'range': rng, 'init_value': init}
    for sig, path, width in [
        ('prbs_o', 'prbs_o', 1),
        ('clk_en', 'clk_en', 1),
    ]:
        simctrl['digital_probes'][sig] = {'abspath': f'tb_i.{path}', 'width': width}

    yaml.dump(simctrl, open(THIS_DIR / 'simctrl.yaml', 'w'))

if __name__ == '__main__':
    # parse arguments
    parser = ArgumentParser()
    parser.add_argument('--target')
    args = parser.parse_args()

    # run the intended target
    run_target(target=args.target)
