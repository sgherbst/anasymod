# Introduction

**anasymod** is a Python package for running FPGA emulations of mixed-signal systems.  It supports digital blocks described with Verilog or VHDL and synthesizable analog models created using [msdsl](https://github.com/sgherbst/msdsl).

# Installation

1. Open a terminal, and note the current directory, since the **pip** commands below will clone some code from GitHub and place it in a subdirectory called **src**.  If you prefer to place the cloned code in a different directory, you can specify that by providing the **--src** flag to **pip**.
2. If you haven't already, install **msdsl** and **svreal**:
```shell
> pip install -e git+https://github.com/sgherbst/svreal.git#egg=svreal
> pip install -e git+https://github.com/sgherbst/msdsl.git#egg=msdsl
```
3. Then install **anasymod**.
```shell
pip install -e git+https://github.com/sgherbst/anasymod.git#egg=anasymod
```

If you get a permissions error when running one of the **pip** commands, you can try adding the **--user** flag to the **pip** command.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.
```shell
pip install -e . --user
```

Also, if you're on Linux, you may need to add "\~/.local/bin" to your PATH variable in order for the "anasymod" script to be found.  For example, in the TCSH shell you can run **set path=(\~/.local/bin $path)**. 

# Prerequites to run the examples

The examples included with **anasymod** use [Icarus Verilog](http://iverilog.icarus.com) for running simulations, [Xilinx Vivado](https://www.xilinx.com/products/design-tools/vivado.html) for running synthesis and place-and-route, and [GTKWave](http://gtkwave.sourceforge.net) for viewing the simulation and emulation results.  The instructions for setting up these tools are included below for various platforms

## Windows



GTKwave and Icarus Verilog can be installed at the same time using the latest Icarus binary [here](http://bleyer.org/icarus/).  Please make sure to add the binary directory containing **iverilog**, **vvp**, and **gtkwave** to the system path.

## Linux

Install Xilinx Vivado by going to the [downloads page](https://www.xilinx.com/support/download.html).  Scroll to the latest version of the "Full Product Installation", and download the Linux self-extracting web installer.  Then, in a terminal:

```shell
> sudo ./Xilinx_Vivado_SDK_Web_*.bin
```

A GUI will pop up and guide you through the rest of the installation.  Note that you'll need a Xilinx account (free), and that you can select the free WebPACK license option if you're planning to work with relatively small FPGAs like the one on the Pynq-Z1 board.

After the Xilinx installation finishes, please add the binary directory containing **vivado** to the system path (the default location is **/tools/Xilinx/Vivado/\*/bin/**).

To install GTKWave and Icarus Verilog, run the following in a terminal:
```shell
> sudo apt-get install gtkwave
> sudo apt-get install iverilog
```

## Installing Vivado

## Installing Icarus Verilog

## Installing 

Please make sure that those tools are installed, and note that on Windows, GTKwave and Icarus Verilog can be installed at the same time using the latest Icarus binary [here](http://bleyer.org/icarus/).

After installing those tools, please make sure that the binary directories for Icarus Verilog, GTKWave, and Vivado are in your system path.  (The tool locations can also be defined with special environment variables, but this is usually not as convenient as just adding the tools to your system path.)

## Running the Simulation Example

From within the folder **anasymod/tests**, run

```shell
> anasymod -i buck --models --sim --view
```

This will generate a synthesizable model for a buck converter, run a simulation, and display the results.

## Running the Emulation Example

For this test, you'll need a [Pynq-Z1](https://store.digilentinc.com/pynq-z1-python-productivity-for-zynq-7000-arm-fpga-soc/) board.  Other FPGA boards can be used in a straightforward manner, but this is the default board.

1. To start, make sure that your Pynq board is set up correctly:
    1. Jumper JP4 should be set for "JTAG"
    2. Jumper "JP5" should be set for "USB"
2. Plug the Pynq board into your computer using a micro USB cable.
3. Move the Pynq board power switch to "ON"
4. Go to the folder **anasymod/tests** and run the following command.  This will take ~10 min to build the bitstream.
```shell
> anasymod -i filter --models --build
```
5. Run the emulation with the following command
```shell
> anasymod -i filter --emulate
```
6. View the results with the following command:
```shell
> anasymod -i filter --view
```
7. Note that you can adjust the emulation time using the --start_time and/or --stop_time options:
```shell
> anasymod -i filter --emulate --start_time 1.23e-6 --stop_time 4.56e-6
```
