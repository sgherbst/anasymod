# coding: utf-8

# NOTE: for interactive debug, add -s to py.test run in order to have stdout and stderr
# no longer captured by py.test!

import os
import pytest
from pathlib import Path
import numpy as np

from anasymod.analysis import Analysis

# get files from "common.py"
from ..common import DEFAULT_SIMULATOR, Waveform


anasymod_test_root = Path(__file__).resolve().parent.parent
build_root = Path(__file__).resolve().parent / 'build'


def run_target(test_name, mode='simulate', simulator_name=DEFAULT_SIMULATOR):
    ana = Analysis(
        input=anasymod_test_root / test_name,
        build_root=build_root / f'test_{test_name}_{mode}_{simulator_name}',
        simulator_name=simulator_name
    )
    ana.gen_sources()

    # run
    if mode in {'simulate'}:
        ana.set_target(target_name='sim')

        # adjust arguments for xrun
        kwargs = {}
        if simulator_name in {'xrun'}:
            kwargs['unit'] = 'main'
            kwargs['id'] = 'xrun'

        # run simulation and return results
        ana.simulate(**kwargs)
        return probe_signals(ana)
    elif mode in {'build', 'emulate', 'build_and_emulate'}:
        ana.set_target(target_name='fpga')
        if mode in {'build_and_emulate', 'build'}:
            ana.build()
        if mode in {'build_and_emulate', 'emulate'}:
            ana.emulate()
            return probe_signals(ana)
        else:
            return None
    else:
        raise Exception(f'Unknown mode: {mode}')


def probe_signals(ana):
    """
    Probes signals from VCD file
    :param ana:
    :type ana: Analysis
    :return:
    """
    
    signal_names = ana.probes()
    signals = {}
    for signal in signal_names:
        name = ''.join(signal.split(".")[-1])
        signals[name] = ana.probe(name=signal, emu_time=True)
        signals[name] = ana.preserve(signals[name])
        # convert x and z values to "0"
        signals[f'{name}_strip_xz'] = np.where(((signals[name] == 'x') |
                                                (signals[name] == 'z')),
                                               0, signals[name]).astype('float')
    return signals


def test_error_recognition():
    # run_target is not used here because we want to catch an error
    # at a specific point in time, rather than allowing an Exception
    # anywhere to pass

    print("Running error_recognition test")

    test_name = 'error_recognition'
    mode = 'simulate'
    simulator_name = DEFAULT_SIMULATOR

    ana = Analysis(
        input=anasymod_test_root / test_name,
        build_root=build_root / f'test_{test_name}_{mode}_{simulator_name}',
        simulator_name=simulator_name
    )
    ana.gen_sources()

    # run
    ana.set_target(target_name='sim')

    # adjust arguments for xrun
    kwargs = {}
    if simulator_name in {'xrun'}:
        kwargs['unit'] = 'main'
        kwargs['id'] = 'xrun'

    with pytest.raises(Exception):
        ana.simulate(**kwargs)

@pytest.mark.parametrize('mode',
    ['simulate'] + (['build_and_emulate'] if 'FPGA_SERVER' in os.environ else [])
)
def test_filter(mode):
    print("Running filter sim")

    signals = run_target('filter', mode=mode)

    wave_v_out = Waveform(
        data=signals['v_out_probe_strip_xz'][1],
        time=signals['v_out_probe_strip_xz'][0]
    )

    high_limit = [
        0.0,0.01,2.8413774247451245e-09,0.009945820794713432,9.309273070463006e-08,0.1916629730491373,
        2.7520940854679694e-07,0.35000637390135797,7.73390766604486e-07,0.616421190692346,
        1.3234660161265176e-06,0.8162323032855869,2.2990711756561586e-06,0.9594302673107433,
        4.28637988667479e-06,1.0192001953843686,9.916080825508866e-06,1.025864273869302
    ]

    low_limit = [
        0.0,-0.01,1.281348876174954e-07,-0.01,3.136773684060609e-07,0.1,
        5.352261331899046e-07,0.3284088495207527,1.0495251394323723e-06,0.5900322492601223,
        1.707677070399699e-06,0.7792847235122319,2.4126785008224645e-06,0.8858316774454128,
        4.267059312253798e-06,0.9701267213345307,9.867283730842193e-06,0.9821452549545097
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_v_out.check_in_limits(wave_low_limit, wave_high_limit)


def test_bitwise():
    # TODO: How can we test this test?
    print("Running bitwise sim")
    run_target('bitwise')


def test_buck():
    print("Running buck sim")

    signals = run_target('buck')

    wave_v_out = Waveform(
        data=signals['v_out_probe_strip_xz'][1],
        time=signals['v_out_probe_strip_xz'][0]
    )

    high_limit = [
        1.7344856126921826e-06, 0.14757446882933967, 5.684713760834015e-06, 0.7577402547754788,
        1.0382642131379072e-05, 1.5089533615192294, 1.5377281767259277e-05, 1.9321050482293167,
        2.091589205654998e-05, 2.1603216882527336, 3.120188259386758e-05, 2.3124661149350123,
        5.217276486546574e-05, 2.47157965304491, 9.995741898460864e-05, 2.4960664487779995
    ]

    low_limit = [
        1.7282830626848378e-06, -0.08102210694198542, 5.3190723985692236e-06, 0.46112372603965923,
        1.0573389104772703e-05, 1.2453772299318864, 1.4573400026547293e-05, 1.5741751937960369,
        1.9533768944991127e-05, 1.78260292681244, 2.9417763308408857e-05, 1.9203771910097234,
        5.020656928244895e-05, 2.0534861870175045, 9.993950980892452e-05, 2.1321794077208813
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_v_out.check_in_limits(wave_low_limit, wave_high_limit)


def test_inertial():
    print("Running inertial sim")
    signals = run_target('inertial')

    wave_out = Waveform(
        data=signals['out_probe_strip_xz'][1],
        time=signals['out_probe_strip_xz'][0]
    )

    high_limit = [
        -2.4004620768390355e-07, 0.01669602100558476, 8.843624335767863e-05, 0.0155961566117081,
        8.917852047391721e-05, 1.0095526190461808, 0.00010261525497318442, 1.0099069786033308,
        0.00010565950429106729, 0.016569714127444124, 0.00018716178625196014, 0.01286398257240473,
        0.00018893366836051514, 1.010781343891796, 0.00020291255403458034, 1.010781343891796,
        0.00020474827084392358, 0.012965998070409435, 0.0002864469100288768, 0.009158251017365004,
        0.00028856297047026125, 1.0110570211541963, 0.0003035975882976378, 1.0134294567337019,
        0.00030500169684267097, 0.009313277448042556
    ]

    low_limit = [
        -3.1974808574238153e-07, -0.018412438625204586, 9.351296106554284e-05, -0.01671767249335876,
        9.459358933069264e-05, 0.9816754054068763, 9.736003875749392e-05, 0.981675405406876,
        9.850073454362191e-05, -0.014318397933956617, 0.00019391910148524309, -0.014060376806462216,
        0.00019498528764618167, 0.9825113062121106, 0.00019794314149107597, 0.9815284090633604,
        0.00019883651520149104, -0.013903929659042968, 0.0002934477871607928, -0.012452773425596586,
        0.0002943079877246215, 0.9806605109854217, 0.00029770349437047855, 0.9809784631258188,
        0.0002982548078002079, -0.010355352557716968, 0.00030526254640431155, -0.0139162518127538
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_out.check_in_limits(wave_low_limit, wave_high_limit)


def test_multicase():
    print("Running multicase sim")
    signals = run_target('multicase')

    wave_out = Waveform(
        data=signals['v_out_probe_strip_xz'][1],
        time=signals['v_out_probe_strip_xz'][0]
    )

    high_limit = [
        3.34962252542877e-09, 0.010817928101748087, 1.75580821453272e-06, 0.010746257860567043,
        2.2014466285577004e-06, 0.4781265755718688, 2.941536996561877e-06, 0.7469160421009357,
        3.625691182992205e-06, 0.8449099430015575, 4.2669701721597764e-06, 0.4620248882990968,
        5.122767511991505e-06, 0.18753511357117747, 5.620693668879983e-06, 0.5087013672813337,
        6.203175044552685e-06, 0.7446919992782245, 7.000617278766725e-06, 0.8635485949554907,
        7.606988984257434e-06, 0.4254601049960923, 8.418432899053952e-06, 0.1960129644726062,
        8.90638533413989e-06, 0.539234044081612, 9.766686802670409e-06, 0.82
    ]

    low_limit = [
        0.0, -0.005071129093666055, 1.9088332258904226e-06, -0.01582642216396682, 2.4795281354570584e-06,
        0.39305527528222917, 2.9479053069648825e-06, 0.6231600673274025, 3.439550047624293e-06,
        0.775821599293627, 3.916432538170918e-06, 0.4474167574483633, 4.553125186578735e-06,
        0.21115023259304186, 5.290468177512146e-06, 0.10706361604823897, 5.889356082375659e-06,
        0.49267278941947945, 6.30657785625346e-06, 0.6642516375076556, 6.757562704094439e-06,
        0.7828122769792349, 7.03520301032725e-06, 0.543473412465884, 7.708156031653259e-06,
        0.25057055770087977, 8.58737320247998e-06, 0.09898533422842445, 9.202825222058684e-06,
        0.5089544613471104, 9.866985509192334e-06, 0.7475891010562503
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_out.check_in_limits(wave_low_limit, wave_high_limit)


def test_rlc():
    print("Running rlc sim")
    signals = run_target('rlc')

    wave_out = Waveform(
        data=signals['v_out_probe_strip_xz'][1],
        time=signals['v_out_probe_strip_xz'][0]
    )

    high_limit = [
        -3.172267808097714e-09, 0.13954594566543688, 8.666098377579087e-07, 4.169961709387263,
        3.166313182150491e-06, 8.740508479320797, 5.135813561319485e-06, 11.01828764356925,
        7.762915450361847e-06, 12.115560361622533, 9.982972698200696e-06, 12.316888036387873
    ]

    low_limit = [
        0.0, -0.20976615348281058, 8.774665000255496e-07, -4.355705190002341, 3.1702233759310403e-06,
        -8.697016017692087, 5.0783397002233064e-06, -11.024405992567946, 7.736642295533657e-06,
        -12.777706447646654, 9.819030374495852e-06, -12.972812217480179
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_out.check_in_limits(wave_low_limit, wave_high_limit)


def test_tf():
    print("Running tf sim")
    signals = run_target('tf')

    wave_out = Waveform(
        data=signals['v_out_probe_strip_xz'][1],
        time=signals['v_out_probe_strip_xz'][0]
    )

    high_limit = [
        3.3926668744800594e-09, 0.014811799919102309, 2.513805548614408e-07, 0.030015349470419728,
        3.749625670771657e-07, 0.06308790265746878, 5.334010442768138e-07, 0.13813715796654147,
        2.123769329346928e-06, 1.017593211817592, 2.761785051922788e-06, 1.2190820493826546,
        3.3887028022265564e-06, 1.2892729490088692, 3.981502579724678e-06, 1.2695852576502973,
        5.0476892299011556e-06, 1.1446112168524016, 5.947550762650103e-06, 1.0222051357969297,
        6.759873846444238e-06, 0.9760530747494472, 7.79620727041577e-06, 0.9897488600423671,
        8.845334934189425e-06, 1.022276350113052, 9.863538063973205e-06, 1.0484836619596365
    ]

    low_limit = [
        1.2675078175971642e-08, -0.006360106382124808, 2.8717872819620994e-07, -0.00044796749808305447,
        5.271390757073921e-07, 0.0335188254917598, 7.916115445590874e-07, 0.12255250330816525,
        2.2654967828388897e-06, 0.9225995044324696, 2.908222606482445e-06, 1.1474367837730524,
        3.4180724849404125e-06, 1.2156588369682906, 3.912472367081472e-06, 1.2017043260874465,
        4.862647140571321e-06, 1.0683612221149352, 5.8746218993288025e-06, 0.9396696217693722,
        6.7320966949172015e-06, 0.8993565903358223, 7.813596437100768e-06, 0.9210636072615799,
        8.871921184808974e-06, 0.9613766386951298, 9.874268057431242e-06, 0.9824998415591326
    ]

    wave_high_limit = Waveform(data=high_limit[1::2], time=high_limit[::2])
    wave_low_limit = Waveform(data=low_limit[1::2], time=low_limit[::2])

    # check if waveform is within limits
    wave_out.check_in_limits(wave_low_limit, wave_high_limit)
