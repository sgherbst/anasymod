#from anasymod.targets import FPGATarget, Target
from anasymod.enums import PortDir
from anasymod.gen_api import SVAPI
from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig

class ModuleTop(JinjaTempl):
    """
    This is the generator for top.sv.
    """
    def __init__(self, target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        self.str_cfg = target.str_cfg

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        for port in self.str_cfg.clk_i_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        #####################################################
        # Instantiate clk management
        #####################################################

        # Add clk in signals for simulation case
        self.clk_in_sim_sigs = SVAPI()

        for port in self.str_cfg.clk_i_ports:
            self.clk_in_sim_sigs.gen_signal(port=port)

        # Add dbg clk signals
        self.dbg_clk_sigs = SVAPI()

        for port in self.str_cfg.clk_d_ports:
            self.dbg_clk_sigs.gen_signal(port=port)

        self.clk_ifc = SVAPI()

        for port in self.str_cfg.clk_i_ports + self.str_cfg.clk_o_ports + self.str_cfg.clk_m_ports + self.str_cfg.clk_d_ports + self.str_cfg.clk_g_ports:
            port.connection = port.name
            self.clk_ifc.println(f".{port.name}({port.connection})")

        #####################################################
        # Instantiate vio
        #####################################################
        self.vio_sigs = SVAPI()

        for port in self.str_cfg.vio_s_ports:
            self.vio_sigs.gen_signal(port=port)

        self.vio_ifc = SVAPI()

        for port in self.str_cfg.vio_i_ports + self.str_cfg.vio_o_ports + self.str_cfg.vio_s_ports + self.str_cfg.vio_r_ports:
            port.connection = port.name
            self.vio_ifc.println(f".{port.name}({port.connection})")

        # add master clk to vio instantiation
        vio_clk_port = self.str_cfg.clk_m_ports[0]
        vio_clk_port.connect = vio_clk_port.name
        self.vio_ifc.println(f".{vio_clk_port.name}({vio_clk_port.connection})")

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_ifc = SVAPI()

        tb_ports = self.str_cfg.clk_o_ports
        for port in tb_ports:
            port.connection = port.name
            self.tb_ifc.println(f".{port.name}({port.connection})")

    TEMPLATE_TEXT = '''
`timescale 1ns/1ps

`include "msdsl.sv"

`default_nettype none

module top(
    `ifndef SIMULATION_MODE_MSDSL
    {% for line in subst.module_ifc.text.splitlines() %}
        {{line}}{{ "," if not loop.last }}
    {% endfor %}
    `endif // `ifndef SIMULATION_MODE_MSDSL
);

// create ext_clk signal when running in simulation mode
`ifdef SIMULATION_MODE_MSDSL
    logic ext_clk;
    {% for line in subst.clk_in_sim_sigs.text.splitlines() %}
        {{line}}
    {% endfor %}
`endif // `ifdef SIMULATION_MODE_MSDSL

// debug clk declaration
{% for line in subst.dbg_clk_sigs.text.splitlines() %}
    {{line}}
{% endfor %}

// emulation clock and reset declarations
logic emu_clk, emu_rst;

// VIO
{% for line in subst.vio_sigs.text.splitlines() -%}
    {{line}}
{% endfor %}
vio_gen vio_gen_i(
{% for line in subst.vio_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// Clock generator
clk_gen clk_gen_i(
{% for line in subst.clk_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// make probes needed for emulation control
`MAKE_EMU_CTRL_PROBES;

// instantiate testbench
tb tb_i(
{% for line in subst.tb_ifc.text.splitlines() %}
    {{line}}{{ "," if not loop.last }}
{% endfor %}
);

// simulation control
`ifdef SIMULATION_MODE_MSDSL
    // stop simulation after some time
    initial begin
        #((`TSTOP_MSDSL)*1s);
        $finish;
    end

    // dump waveforms to a specified VCD file
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"
    initial begin
        $dumpfile(`ADD_QUOTES_TO_MACRO(`VCD_FILE_MSDSL));
    end
`endif // `ifdef SIMULATION_MODE_MSDSL

endmodule

`default_nettype wire
'''

def main():
    print(ModuleTop(target=FPGATarget(prj_cfg=EmuConfig(root='test', cfg_file=''))).render())

if __name__ == "__main__":
    main()