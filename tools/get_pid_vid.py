"""
 Copyright (c) 2025 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,f
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

This Python 3 script will prompt you for the device ID
(/dev/ttyACM0, COM3, etc)  of a connected
Raspberry Pi Pico device. It will then print the PID (Product ID) and the
VID (Vendor ID).

You may use these values to set the PID and VID when instantiating the
telemetrix_rpi_pico_2w class

"""


import serial
from serial.serialutil import SerialException
from serial.tools import list_ports
import sys

# Ask user for com port
com_port = input("Enter the COM port of a connected Raspberry Pi Pico device (i.e. "
          "/dev/ttyACM0, COM3, etc): ")

# attempt to open the comport

try:
    device = serial.Serial(com_port, 115200,
                                     timeout=1, writeTimeout=0)
except SerialException:
    print("Serial port could not be opened.")
    sys.exit(0)

for port in serial.tools.list_ports.comports():
    try:
        if port.device == com_port:
            print(f'PID = {port.pid}' )
            print(f'VID = {port.vid}')
    except SerialException:
        print("Did not find comport in ports list")
        sys.exit(0)


device.close()

