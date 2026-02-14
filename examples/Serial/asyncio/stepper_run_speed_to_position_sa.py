"""
 Copyright (c) 2022-2026 Alan Yorinks All rights reserved.

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

"""
import asyncio
import sys
import time

from telemetrix_rpi_pico_2w_serial_aio import telemetrix_rpi_pico_2w_serial_aio

"""
Run a motor using runSpeedToPosition

Motor used to test is a NEMA-17 size - 200 steps/rev, 12V 350mA.
And the driver is a TB6600 4A 9-42V Nema 17 Stepper Motor Driver.

The driver was connected as follows:
VCC 12 VDC
GND Power supply ground
ENA- Not connected
ENA+ Not connected
DIR-  GND
DIR+ GPIO Pin 1 
PUL-  GND
PUL+ GPIO Pin 0
A-, A+ Coil 1 stepper motor
B-, B+ Coil 2 stepper motor
"""

EXIT_FLAG = 0


async def the_callback(data):
    global EXIT_FLAG
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[2]))
    print(f'Motor {data[1]} runSpeedToPosition motion completed at: {date}.')
    EXIT_FLAG = 1


async def run_speed_to_position(board):
    # create an accelstepper instance for a TB6600 motor driver
    motor = await board.set_pin_mode_stepper(interface=1, pin1=0, pin2=1)

    # set the max speed and target position
    await board.stepper_set_max_speed(motor, 800)
    await board.stepper_move_to(motor, 2000)

    # set the motor speed
    await board.stepper_set_speed(motor, 400)

    print('Running speed to position...')
    # run the motor
    await board.stepper_run_speed_to_position(motor, completion_callback=the_callback)

    # keep application running
    while EXIT_FLAG == 0:
        try:
            await asyncio.sleep(.1)
        except KeyboardInterrupt:
            await board.shutdown()
            sys.exit(0)


# get the event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# instantiate telemetrix
my_board = telemetrix_rpi_pico_2w_serial_aio.TelemetrixRpiPico2WSerialAIO(loop=loop)
try:
    # start the main function
    loop.run_until_complete(run_speed_to_position(my_board))
    loop.run_until_complete(my_board.shutdown())

except KeyboardInterrupt:
    loop.run_until_complete(my_board.shutdown())
    sys.exit(0)
