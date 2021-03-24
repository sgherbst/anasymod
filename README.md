# anasymod
[![Actions Status](https://github.com/sgherbst/anasymod/workflows/Regression/badge.svg)](https://github.com/sgherbst/anasymod/actions)
[![BuildKite status](https://badge.buildkite.com/7f10348afca3b631bbbb2175919b9039101c2a5e55c3371460.svg?branch=master)](https://buildkite.com/stanford-aha/anasymod)
[![Code Coverage](https://codecov.io/gh/sgherbst/anasymod/branch/master/graph/badge.svg)](https://codecov.io/gh/sgherbst/anasymod)
[![License:BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Join the chat at https://gitter.im/sgherbst/anasymod](https://badges.gitter.im/sgherbst/anasymod.svg)](https://gitter.im/sgherbst/anasymod?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**anasymod** is a tool for running FPGA emulations of mixed-signal systems.  It supports digital blocks described with Verilog or VHDL and synthesizable analog models created using [msdsl](https://github.com/sgherbst/msdsl) and [svreal](https://github.com/sgherbst/svreal).

# Installation

## From PyPI

```shell
> pip install anasymod
```

If you get a permissions error when running one of the **pip** commands, you can try adding the **--user** flag to the **pip** command.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.


## From GitHub

If you are a developer of **anasymod**, it is more convenient to clone and install the GitHub repository:

```shell
> git clone https://github.com/sgherbst/anasymod.git
> cd anasymod 
> pip install -e .
```

## Testing Installation

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

The simulation part of this example should work if you install Icarus Verilog and GTKWave:

```shell
> brew install icarus-verilog
> brew install --cask gtkwave
```

Unfortunately Xilinx Vivado does not run natively on macOS.  However, running Vivado on a Windows or Linux virtual machine on macOS does seem to work.

## Running a Simulation

From within the folder **anasymod/unittests**, run

```shell
> anasymod -i buck --models --sim --view
```

This will generate a synthesizable model for a buck converter, run a simulation, and display the results.

![gtkwave_sim](https://user-images.githubusercontent.com/19254098/112363360-a538a980-8c92-11eb-84e2-aee73765e1c4.png)

### Command-line options
Here's a breakdown of what the options mean:
* The **-i buck** option indicates that the folder ``buck`` contains the emulation files
* **--models** means that **anasymod** should look for a file called **gen.py** and run it.  In this case the **gen.py** script uses [msdsl](https://git.io/msdsl) to generate a synthesizable model for the buck converter.
* **--sim** means that a simulation should be run on the computer, rather than building the emulator bitstream.  This is helpful for debugging.  You can also pass the option **--simulator_name NAME** to specify which simulator should be used.  Currently supported simulators are **icarus**, **vivado**, and **xrun** (Cadence Xcelium),
* **--view** means that the resuls should be displayed after running the simulation.  The viewer can be specified with the **--viewer_name NAME** option.  Only **gtkwave** is supported at the moment.  When a file called **view.gtkw** is in the folder with emulator sources, **anasymod** will load it to configure the GTKWave display.  You can generate your own **view.gtkw** file using ``File`` → ``Write Save File`` in GTKWave.

### Source files

Looking into the ``buck`` folder, you'll notice there are a bunch of files.  Some have special meanings for the **anasymod** tool (i.e., if you have a file with one of these names, it **anasymod** will treat it in a certain way)
*  ``gen.py``: Generates synthesizable emulation models.  **anasymod** expects to run this as a command-line script that has arguments ``-o`` (output directory) and ``-dt`` (fixed timestep).  **anasymod** fills those arguments based on user settings when it runs **gen.py**.
* ``prj.yaml``: YAML file containing settings for the project, like the FPGA board to use, build options, emulator control infrastructure to use, etc.  In this case, one of the key options is **dt**, which indicates that each emulator cycle corresponds to a fixed timestep of 50 ns.
* ``simctrl.yaml``: YAML file containing signals to probe.  The signals indicated will be probed for both simulation and emulation (in the latter case, using a Xilinx Integrated Logic Analyzer instance).  This file can also specify signals to be written and read in interactive tests.
* ``tb.sv``: Top-level file for simulation and synthesis, representing a synthesizable testbench.

**anasymod** has other special files (e.g., ``clks.yaml` for controlling clock generation), but they are not used in this example. 

## Running an Emulation

At this point, we have run a simulation of the emulator design, but haven't built a bitstream of programmed the FPGA.  This section shows how to run those tasks.

For this test to work as-is, you'll need a [Pynq-Z1](https://store.digilentinc.com/pynq-z1-python-productivity-for-zynq-7000-arm-fpga-soc/) board.  However, if you uncomment the ``board_name`` option in ``prj.yaml``, you can specify a different board; currently supported options are ``PYNQ_Z1``, ``ARTY_A7``, ``VC707``, ``ZC702``, ``ZC706``, ``ZCU102``, and ``ZCU106``.  We are always interested to add support for new boards, so please let us know if your board isn't listed here (feel free to file a GitHub Issue).  

Go to the folder **anasymod/unittests** and run the following command.  It will take about 11 minutes to build the bitstream.
```shell
> anasymod -i buck --models --build
```

If you are using the Pynq-Z1 board, then please make sure it is set up correctly:
1. Jumper JP4 should be set for "JTAG"
2. Jumper "JP5" should be set for "USB"
Then, plug the Pynq board into your computer using a micro USB cable.  Move the Pynq board power switch to "ON".

Run the emulation and view the results with the following command:
```shell
> anasymod -i buck --emulate --view
```

![gtkwave_emu](https://user-images.githubusercontent.com/19254098/112367656-707b2100-8c97-11eb-8496-3fcb9cfb3a6b.png)

## Timestep Management

## Firmware

## Interactive Tests

## Contributing

To improve the quality of the software, users are encouraged to share modifications, enhancements or bug fixes with Infineon Technologies AG under Gabriel.Rutsch@infineon.com.
