# ANASYMOD: A framework for FPGA emulation of mixed-signal systems

## Requirements
1. Python
2. Vivado
3. GTKwave
4. Icarus Verilog

On Windows, GTKwave and Icarus Verilog can be installed at the same time using the latest Icarus binary [here](http://bleyer.org/icarus/).

## Path setup

Make sure that **pip**, **python**, **gtkwave**, **iverilog**, and **vvp** are in your system path.

## Installation
1. Open a terminal and navigate to a convenient directory.
```shell
> ???????????????????????????????????
```
2. Install all of the Python packages in the project.  From the top-level **anasymod** directory.
```shell
> pip install -e .
> cd msdsl
> pip install -e .
> cd ..
> cd svreal
> pip install -e .
> cd ..
```

## Running the Simulation Example

From within the folder **anasymod/tests**, run

```shell
> anasymod -i filter --models --sim --view
```

This will generate the models, run the simulation

## Running the Emulation Example
1. Make sure that your Pynq board is set up correctly:
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