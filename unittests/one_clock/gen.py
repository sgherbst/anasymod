from pathlib import Path
from argparse import ArgumentParser
from msdsl import MixedSignalModel, VerilogGenerator, to_uint, clamp_op
from msdsl.expr.extras import if_

def main():
    print('Running model generator...')

    # parse command line arguments
    parser = ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='build')
    parser.add_argument('--dt', type=float, default=0.1e-6)
    a = parser.parse_args()

    # create the model
    m = MixedSignalModel('osc', dt=a.dt)
    m.add_digital_input('emu_clk')
    m.add_digital_input('emu_rst')
    m.add_digital_output('dt_req', 32)
    m.add_digital_input('emu_dt', 32)
    m.add_digital_output('clk_val')
    m.add_digital_input('t_lo', 32)
    m.add_digital_input('t_hi', 32)

    # determine if the request was granted
    m.bind_name('req_grant', m.dt_req == m.emu_dt)

    # update the clock value
    m.add_digital_state('prev_clk_val')
    m.set_next_cycle(m.prev_clk_val, m.clk_val, clk=m.emu_clk, rst=m.emu_rst)
    m.set_this_cycle(m.clk_val, if_(m.req_grant, ~m.prev_clk_val, m.prev_clk_val))

    # determine the next period
    m.bind_name('dt_req_next', if_(m.prev_clk_val, m.t_lo, m.t_hi))

    # increment the time request
    m.bind_name('dt_req_incr', m.dt_req - m.emu_dt)

    # determine the next period
    m.bind_name('dt_req_imm', if_(m.req_grant, m.dt_req_next, m.dt_req_incr))
    m.set_next_cycle(m.dt_req, m.dt_req_imm, clk=m.emu_clk, rst=m.emu_rst, check_format=False)

    # determine the output filename
    filename = Path(a.output).resolve() / f'{m.module_name}.sv'
    print(f'Model will be written to: {filename}')

    # generate the model
    m.compile_to_file(VerilogGenerator(), filename)

if __name__ == '__main__':
    main()
