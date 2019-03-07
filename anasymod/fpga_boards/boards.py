class FPGABoard():
    def __init__(self):
        self.cfg = {
        'clk_pin' : None,
        'clk_io' : None,
        'clk_freq' : None,
        'full_part_name' : None,
        'short_part_name' : None
        }

class PYNQ_Z1():
    def __init__(self):
        self.cfg = {
        'clk_pin' : 'H16',
        'clk_io' : 'LVCMOS33',
        'clk_freq' : 125e6,
        'full_part_name' : 'xc7z020clg400-1',
        'short_part_name' : 'xc7z020'
        }

class VC707():
    def __init__(self):
        self.cfg = {
        'clk_pin_p' : 'E19',
        'clk_pin_n': 'E18',
        'clk_io' : 'LVDS',
        'clk_freq' : 200e6,
        'full_part_name' : 'XC7VX485T-2FFG1761C',
        'short_part_name' : 'XC7VX485T'
        }