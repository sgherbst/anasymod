# anasymod
[![BuildKite Status](https://badge.buildkite.com/7f10348afca3b631bbbb2175919b9039101c2a5e55c3371460.svg)](https://buildkite.com/stanford-aha/anasymod)
[![Code Coverage](https://codecov.io/gh/sgherbst/anasymod/branch/master/graph/badge.svg)](https://codecov.io/gh/sgherbst/anasymod)
[![License:BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

**anasymod** is a tool for running FPGA emulations of mixed-signal systems.  It supports digital blocks described with Verilog or VHDL and synthesizable analog models created using [msdsl](https://github.com/sgherbst/msdsl) and [svreal](https://github.com/sgherbst/svreal).

# Installation

```shell
> pip install anasymod
```

If you get a permissions error when running one of the **pip** commands, you can try adding the **--user** flag to the **pip** command.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.

Check to see if the **anasymod** command-line script is accessible by running:
```shell
> anasymod -h
```

If the **anasymod** script isn't found, then you'll have to add the directory containing it to the path.  On Windows, a typical location is **C:\\Python3\*\\Scripts**, while on Linux or macOS you might want to check **~/.local/bin** (particularly if you used the **--user** flag).

# Prerequites to run the examples

The examples included with **anasymod** use [Icarus Verilog](http://iverilog.icarus.com) for running simulations, [Xilinx Vivado](https://www.xilinx.com/products/design-tools/vivado.html) for running synthesis and place-and-route, and [GTKWave](http://gtkwave.sourceforge.net) for viewing the simulation and emulation results.  The instructions for setting up these tools are included below for various platforms.

## Windows

Install Xilinx Vivado by going to the [downloads page](https://www.xilinx.com/support/download.html).  Scroll to the latest version of the "Full Product Installation", and download the Windows self-extracting web installer.  Launch the installer and follow the instructions.  You'll need a Xilinx account (free), and will have to select a license, although the free WebPACK license option is fine you're just planning to work with small FPGAs like the one on the Pynq-Z1 board.

GTKwave and Icarus Verilog can be installed at the same time using the latest Icarus binary [here](http://bleyer.org/icarus/).

## Linux

Install Xilinx Vivado by going to the [downloads page](https://www.xilinx.com/support/download.html).  Scroll to the latest version of the "Full Product Installation", and download the Linux self-extracting web installer.  Then, in a terminal:

```shell
> sudo ./Xilinx_Vivado_SDK_Web_*.bin
```

A GUI will pop up and guide you through the rest of the installation.  Note that you'll need a Xilinx account (free), and that you can select the free WebPACK license option if you're planning to work with relatively small FPGAs like the one on the Pynq-Z1 board.

Next, the Xilinx cable drivers must be installed ([AR #66440](https://www.xilinx.com/support/answers/66440.html)):
```shell
> cd <YOUR_XILINX_INSTALL>/data/xicom/cable_drivers/lin(32|64)/install_script/install_drivers
> sudo ./install_drivers
```

Finally, some permissions cleanup is required ([AR #62240](https://www.xilinx.com/support/answers/62240.html))

```shell
> cd ~/.Xilinx/Vivado
> sudo chown -R $USER *
> sudo chmod -R 777 *
> sudo chgrp -R $USER *
```

Installing GTKWave and Icarus Verilog is much simpler; just run the following in a terminal:
```shell
> sudo apt-get install gtkwave iverilog
```

## macOS

Unfortunately Xilinx Vivado does not run natively on macOS.  But running Windows or Linux through a virtual machine on macOS should work.

## Running the Simulation Example

From within the folder **anasymod/tests**, run

```shell
> anasymod -i buck --models --sim --view
```

This will generate a synthesizable model for a buck converter, run a simulation, and display the results.

## Running the Emulation Example

For this test, you'll need a [Pynq-Z1](https://store.digilentinc.com/pynq-z1-python-productivity-for-zynq-7000-arm-fpga-soc/) board.

1. To start, make sure that your board is set up correctly:
    1. Jumper JP4 should be set for "JTAG"
    2. Jumper "JP5" should be set for "USB"
2. Plug the Pynq board into your computer using a micro USB cable.
3. Move the Pynq board power switch to "ON"
4. Go to the folder **anasymod/tests** and run the following command.  It will take ~10 min to build the bitstream.
```shell
> anasymod -i buck --models --build
```
5. Run the emulation with the following command:
```shell
> anasymod -i buck --emulate
```
6. View the results with the following command:
```shell
> anasymod -i buck --view
```
7. Note that you can adjust the emulation time using the --start_time and/or --stop_time options:
```shell
> anasymod -i buck --emulate --start_time 1.23e-6 --stop_time 4.56e-6
```

## Contributing

To improve the quality of the software, users are encouraged to share modifications, enhancements or bug fixes with Infineon Technologies AG under Gabriel.Rutsch@infineon.com.
