#from anasymod.targets import FPGATarget, Target
from anasymod.enums import PortDir
from anasymod.gen_api import SVAPI
from anasymod.templ import JinjaTempl
from anasymod.config import EmuConfig
from anasymod.structures.structure_config import StructureConfig

class ModuleTop(JinjaTempl):
    """
    This is the generator for top.sv.
    """
    def __init__(self, target):
        super().__init__(trim_blocks=True, lstrip_blocks=True)
        scfg = target.str_cfg
        """ :type: StructureConfig """

        #####################################################
        # Create module interface
        #####################################################
        self.module_ifc = SVAPI()

        for port in scfg.clk_i_ports:
            port.direction = PortDir.IN
            self.module_ifc.gen_port(port)

        #####################################################
        # Instantiate clk management
        #####################################################

        # Add clk in signals for simulation case
        self.clk_in_sim_sigs = SVAPI()

        for port in scfg.clk_i_ports:
            self.clk_in_sim_sigs.gen_signal(port=port)

        # Add dbg clk signals
        self.dbg_clk_sigs = SVAPI()

        for port in scfg.clk_d_ports:
            self.dbg_clk_sigs.gen_signal(port=port)

        self.clk_ifc = SVAPI()

        for port in scfg.clk_i_ports + scfg.clk_o_ports + scfg.clk_m_ports + scfg.clk_d_ports + scfg.clk_g_ports:
            port.connection = port.name
            self.clk_ifc.println(f".{port.name}({port.connection})")

        #####################################################
        # Ctrl Module
        #####################################################

        # Instantiate internal ctrl signals
        self.inst_itl_ctlsigs = SVAPI()

        for ctrl_io in scfg.dec_thr_ctrl:
            self.inst_itl_ctlsigs._gen_signal(io_obj=ctrl_io)

        for port in self.str_cfg.vio_i_ports + self.str_cfg.vio_r_ports + self.str_cfg.vio_s_ports + self.str_cfg.vio_o_ports:
            port.connection = port.name
            self.vio_ifc.println(f".{port.name}({port.connection})")

        # Instantiate ctrl module
        self.ctrl_module_ifc = SVAPI()

        for ctrl_io in scfg.reset_ctrl + scfg.dec_thr_ctrl + scfg.analog_ctrl_inputs + scfg.digital_ctrl_inputs + scfg.analog_ctrl_outputs + scfg.digital_ctrl_outputs:
            self.ctrl_module_ifc.println(f".{ctrl_io.name}({ctrl_io.name})")

        # add master clk to ctrl module
        vio_clk_port = scfg.clk_m_ports[0]
        vio_clk_port.connect = vio_clk_port.name
        self.ctrl_module_ifc.println(f".{vio_clk_port.name}({vio_clk_port.connection})")

        # Instantiate abs paths into design for ctrl signals
        self.inst_assign_custom_ctlsigs = SVAPI()
        for ctrl_io in scfg.digital_ctrl_inputs + scfg.digital_ctrl_outputs + scfg.analog_ctrl_inputs + scfg.analog_ctrl_outputs:
            self.inst_assign_custom_ctlsigs._gen_signal(io_obj=ctrl_io)
            self.inst_assign_custom_ctlsigs.assign_to_signal(io_obj=ctrl_io)

        #####################################################
        # Instantiate testbench
        #####################################################
        self.tb_ifc = SVAPI()

        tb_ports = scfg.clk_o_ports
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
// absolute paths to ctrl signals in the design
{{subst.inst_assign_custom_ctlsigs.text}}

// VIO
{% for line in subst.inst_itl_ctlsigs.text.splitlines() -%}
    {{line}}
{% endfor %}
vio_gen vio_gen_i(
{% for line in subst.ctrl_module_ifc.text.splitlines() %}
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