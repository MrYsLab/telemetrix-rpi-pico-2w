"""
 Copyright (c) 2021-2025 Alan Yorinks All rights reserved.

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
import struct
import sys
import time

from serial.serialutil import SerialException
from serial.tools import list_ports

from telemetrix_rpi_pico_2w_common.private_constants import PrivateConstants
from telemetrix_rpi_pico_2w_serial_aio.telemtrix_aio_serial import TelemetrixAioSerial


# noinspection PyPep8,PyMethodMayBeStatic,GrazieInspection
class TelemetrixRpiPico2WSerialAIO:
    """
    This class exposes and implements a Telemetrix type
    API for the Raspberry Pi Pico using Python asyncio.
    """

    def __init__(self, com_port=None, pico_instance_id=None,
                 sleep_tune=0.000001,
                 autostart=True,
                 loop=None,
                 shutdown_on_exception=True,
                 close_loop_on_shutdown=True,
                 reset_on_shutdown=True,
                 pid = 61455,
                 vid = 11914):
        """

        :param com_port: e.g. COM3 or /dev/ttyACM0.
                         Only use if you wish to bypass auto com port
                         detection.

        :param pico_instance_id: If not specified, than don't do id check.
                                 Else contains a board' s pico unique ID.
                                 This is passed as an array.

        :param sleep_tune: A tuning parameter (typically not changed by user)

        :param autostart: If you wish to call the start method within
                          your application, then set this to False.

        :param loop: optional user provided event loop

        :param shutdown_on_exception: call shutdown before raising
                                      a RunTimeError exception, or
                                      receiving a KeyboardInterrupt exception

        :param close_loop_on_shutdown: stop and close the event loop loop
                                       when a shutdown is called or a serial
                                       error occurs

        :para reset_on_shutdown: Reset the board upon shutdown

        :para pid: Raspberry Pi Pico Product ID (Not checked if com port is specified)

        :para vid: Raspberry Pi Pico Vendor ID (Not checked if com port is specified)
        """

        # check to make sure that Python interpreter is version 3.7 or greater
        python_version = sys.version_info
        if python_version[0] >= 3:
            if python_version[1] >= 8:
                if python_version[2] >= 3:
                    pass
            else:
                raise RuntimeError("ERROR: Python 3.8.3 or greater is "
                                   "required for use of this program.")

        # save input parameters as instance variables
        self.com_port = com_port
        self.pico_instance_id = pico_instance_id
        self.sleep_tune = sleep_tune
        self.shutdown_on_exception = shutdown_on_exception
        self.reset_on_shutdown = reset_on_shutdown
        self.autostart = autostart
        self.close_loop_on_shutdown = close_loop_on_shutdown
        self.pid = pid
        self.vid = vid
        # set the event loop
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        # The report_dispatch dictionary is used to process
        # incoming report messages by looking up the report message
        # and executing its associated processing method.

        self.report_dispatch = {}

        # To add a command to the command dispatch table, append here.
        self.report_dispatch.update(
            {PrivateConstants.LOOP_COMMAND: self._report_loop_data})
        self.report_dispatch.update(
            {PrivateConstants.DEBUG_PRINT: self._report_debug_data})
        self.report_dispatch.update(
            {PrivateConstants.DIGITAL_REPORT: self._digital_message})
        self.report_dispatch.update(
            {PrivateConstants.ANALOG_REPORT: self._analog_message})
        self.report_dispatch.update(
            {PrivateConstants.CPU_TEMP_REPORT: self._cpu_temp_message})
        self.report_dispatch.update(
            {PrivateConstants.UNIQUE_ID_REPORT: self._report_unique_id})
        self.report_dispatch.update(
            {PrivateConstants.FIRMWARE_REPORT: self._report_firmware_version})
        self.report_dispatch.update(
            {PrivateConstants.SERVO_UNAVAILABLE: self._servo_unavailable})
        self.report_dispatch.update(
            {PrivateConstants.I2C_READ_REPORT: self._i2c_read_report})
        self.report_dispatch.update(
            {PrivateConstants.I2C_TOO_FEW_BYTES_RECEIVED: self._i2c_too_few_bytes_received})
        self.report_dispatch.update(
            {PrivateConstants.I2C_TOO_MANY_BYTES_RECEIVED: self._i2c_too_many_bytes_received})
        self.report_dispatch.update(
            {PrivateConstants.SONAR_DISTANCE: self._sonar_distance_report})
        self.report_dispatch.update({PrivateConstants.DHT_REPORT: self._dht_report})
        self.report_dispatch.update({PrivateConstants.SPI_REPORT: self._spi_report})

        # up to 16 pwm pins may be simultaneously active
        self.pwm_active_count = 0

        # dictionaries to store the callbacks for each pin
        self.analog_callbacks = {}

        self.cpu_temp_active = False
        self.cpu_temp_callback = None

        self.digital_callbacks = {}

        self.i2c_callback = None
        self.i2c_callback2 = None

        self.i2c_0_active = False
        self.i2c_1_active = False

        # there are 2 spi ports available
        # these values help support both
        self.spi_callback = None
        self.spi_callback2 = None

        self.spi_0_active = False
        self.spi_1_active = False

        self.spi0_chip_select = 17
        self.spi1_chip_select = 13

        # the trigger pin will be the key to retrieve
        # the callback for a specific HC-SR04
        self.sonar_callbacks = {}

        self.sonar_count = 0

        self.dht_callbacks = {}

        self.dht_count = 0

        # serial port in use
        self.serial_port = None

        # generic asyncio task holder
        self.the_task = None

        # flag to indicate we are in shutdown mode
        self.shutdown_flag = False

        # debug loopback callback method
        self.loop_back_callback = None

        # flag to indicate the start of a new report
        # self.new_report_start = True

        # firmware version to be stored here
        self.firmware_version = []

        # reported pico_id
        self.reported_pico_id = []

        # maximum pwm duty cycle - 20000
        self.maximum_pwm_duty_cycle = PrivateConstants.MAX_PWM_DUTY_CYCLE

        # flag to indicate if i2c was previously enabled
        self.i2c_enabled = False

        # Create a dictionary to store the pins in use.
        # Notice that gpio pins 23, 24 and 25 are not included
        # because the Pico does not support these GPIOs.

        # This dictionary is a list of gpio pins updated with the pin mode when a pin mode
        # is set.
        # It is created initially using a dictionary comprehension.
        self.pico_pins = {gpio_pin: PrivateConstants.AT_MODE_NOT_SET for gpio_pin in
                          range(23)}

        # skip over unavailable pins
        for pin in range(25, 29):
            self.pico_pins[pin] = PrivateConstants.AT_MODE_NOT_SET

        self.pico_pins[64] = PrivateConstants.AT_MODE_NOT_SET

        # creating a list of available sda and scl pins for i2c. If assigned the pins
        # value will be set to either 0 or 1 depending upon the i2c selected.
        self.i2c_sda_pins = {n: 255 for n in range(2, 21, 2)}
        self.i2c_sda_pins[26] = 255

        self.i2c_scl_pins = {n: 255 for n in range(3, 22, 2)}
        self.i2c_scl_pins[27] = 255

        # create a dictionary that holds all the servo ranges
        self.servo_ranges = {gpio_pin: [1000, 2000] for gpio_pin in
                             range(23)}

        # skip over unavailable pins
        for gpio_pin in range(25, 29):
            self.servo_ranges[gpio_pin] = [1000, 2000]

        # neopixel data
        self.number_of_pixels = None

        self.neopixels_initiated = False

        print(f"TelemetrixRpiPico2WAio:  Version"
              f" {PrivateConstants.TELEMETRIX_VERSION}\n\n"
              f"Copyright (c) 2021 Alan Yorinks All Rights Reserved.\n")

        if autostart:
            self.loop.run_until_complete(self.start_aio())

    async def start_aio(self):
        """
        This method may be called directly, if the autostart
        parameter in __init__ is set to false.

        This method instantiates the serial interface.

        Use this method if you wish to start TelemetrixRPiPicoAIO manually from
        an asyncio function.
         """
        self.the_task = self.loop.create_task(self._pico_report_dispatcher())
        if not self.com_port:
            # user did not specify a com_port
            try:
                await self._find_pico()
            except (KeyboardInterrupt, RuntimeError):
                if self.shutdown_on_exception:
                    print('No viable com ports found - shutting down')
                    sys.exit(0)
        else:
            # com_port specified - set com_port and baud rate
            try:
                await self._manual_open()
            except KeyboardInterrupt:
                if self.shutdown_on_exception:
                    await self.shutdown()

            if self.com_port:
                print(f'TelemetrixRpiPico2W found and connected to {self.com_port}')
            # no com_port found - raise a runtime exception
            else:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('No Pico Found or User Aborted Program')

        print('Retrieving pico ID...')
        await self._get_pico_id()

        # get Telemetrix4RPiPico firmware version and print it
        firmware_version = await self._get_firmware_version()
        if not firmware_version:
            raise RuntimeError(f'Telemetrix4pico2W Sketch Firmware Version Not Found')
        else:
            print(f'Telemetrix4RPiPico2wSerialAIO Version Number: {firmware_version[0]}.'
                  f'{firmware_version[1]}')

    async def _find_pico(self):
        """
        This method will search all potential serial ports for a pico
        board using its USB PID and VID.
        """

        print('Opening all potential serial ports...')
        the_ports_list = list_ports.comports()
        for port in the_ports_list:
            if port.pid != self.pid or port.vid != self.vid:
                continue
            try:
                self.serial_port = TelemetrixAioSerial(port.device, 115200,
                                                       telemetrix_aio_instance=self,
                                                       close_loop_on_error=self.close_loop_on_shutdown)
            except SerialException:
                continue

            # create a list of serial ports that we opened
            # make sure this is a pico board

            # display to the user
            print('\t' + port.device)

            # clear out the serial buffers
            await self.serial_port.reset_input_buffer()
            await self.serial_port.reset_output_buffer()

        if not self.serial_port:
            print('No serial port found - exiting...')
            sys.exit(0)


    async def _manual_open(self):
        """
        Com port was specified by the user - try to open up that port

        """
        # if port is not found, a serial exception will be thrown
        try:
            print(f'Opening {self.com_port}...')
            self.serial_port = TelemetrixAioSerial(self.com_port, 115200,
                                                   telemetrix_aio_instance=self,
                                                   close_loop_on_error=self.close_loop_on_shutdown)
        except KeyboardInterrupt:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('User Hit Control-C')

    async def _cpu_temp_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for cpu temperature messages.

        :param data: message data

        """

        temperature = struct.unpack('<f', bytes(data))
        temperature = round(temperature[0], 2)
        time_stamp = time.time()
        # self.digital_pins[pin].event_time = time_stamp
        if self.cpu_temp_callback:
            message = [PrivateConstants.CPU_TEMP_REPORT, temperature, time_stamp]
            await self.cpu_temp_callback(message)


    async def _get_firmware_version(self):
        """
        This method retrieves the Telemetrix4RPiPico firmware version

        :returns: Firmata firmware version
        """
        command = [PrivateConstants.GET_FIRMWARE_VERSION]
        await self._send_command(command)
        # provide time for the reply
        await asyncio.sleep(.1)

        return self.firmware_version

    async def get_cpu_temperature(self, threshold=1.0, polling_interval=1000,
                                callback=None):
        """
        Request the CPU temperature. This will continuously monitor the temperature
        and report it back in degrees Celsius. Call only once, unless you wish to
        modify the polling interval.

        :param threshold:    The threshold value is used to determine when a
        temperature report is generated. The current temperature is compared to
        plus and minus the threshold value and if the value is exceeded, a report
        will be generated. To receive continuous reports, set the threshold to 0.
        The maximum of 5.0 degrees.

        :param polling_interval: number of milliseconds between temperature reads.
                                 Maximum of 60 seconds (6000 ms.)

        :param callback: callback function

        callback returns a list:
        [CPU_TEMPERATURE_REPORT, degrees_celsius, raw_time_stamp]

        CPU_TEMPERATURE_REPORT = 20
        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('A callback must be specified')

        # convert the floating point threshold to bytes

        if 0.0 <= threshold < 30.0:
            if 0 <= polling_interval < 60000:
                thresh_list = list(struct.pack("f", threshold))
                polling_list = polling_interval.to_bytes(2, byteorder='big')
                self.cpu_temp_callback = callback

                self.cpu_temp_active = True

                command = [PrivateConstants.GET_CPU_TEMPERATURE, thresh_list[0],
                           thresh_list[1],
                           thresh_list[2], thresh_list[3], polling_list[0],
                           polling_list[1]]

                await self._send_command(command)
            else:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('get_cpu_temperature: polling interval out of range.')
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('get_cpu_temperature: threshold out of range.')

    async def _get_pico_id(self):
        """
        Retrieve pico-telemetrix pico id

        """
        command = [PrivateConstants.RETRIEVE_PICO_UNIQUE_ID]
        await self._send_command(command)
        # provide time for the reply
        await asyncio.sleep(.1)

        print(f'Pico Unique ID: {self.reported_pico_id}')

        if self.pico_instance_id:
            if self.reported_pico_id != self.pico_instance_id:
                print(f'Incorrect pico ID Specified {self.pico_instance_id} - correct ID '
                      f':{self.reported_pico_id}')

                sys.exit(0)
            else:
                print('Valid pico ID Found.')

    async def pwm_range(self, range_pwm):
        """
        Set the duty cycle range.
        The range of values is 16 to 65535

        :param range_pwm: range value
        """

        if 16 <= range_pwm <= 65535:
            data = range_pwm.to_bytes(4, byteorder='big')
            self.maximum_pwm_duty_cycle = range_pwm

            command = [PrivateConstants.SET_PWM_RANGE, data[0], data[1],
                       data[2], data[3]]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('pwm_range is out of range')

    async def digital_write(self, pin, value):
        """
        Set the specified pin to the specified value.

        :param pin: pico GPIO pin number

        :param value: pin value (1 or 0)

        """
        if self.pico_pins[pin] != PrivateConstants.AT_OUTPUT:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('digital_write: You must set the pin mode before '
                               'performing '
                               'a digital write.')
        command = [PrivateConstants.DIGITAL_WRITE, pin, value]
        await self._send_command(command)

    async def disable_all_reporting(self):
        """
        Disable reporting for all digital and analog input pins
        """
        command = [PrivateConstants.MODIFY_REPORTING,
                   PrivateConstants.REPORTING_DISABLE_ALL, 0]
        await self._send_command(command)

    async def disable_analog_reporting(self, pin):
        """
        Disables analog reporting for a single analog pin.

        :param pin: Analog pin number. For example for ADC, the number is 0.

        """
        command = [PrivateConstants.MODIFY_REPORTING,
                   PrivateConstants.REPORTING_ANALOG_DISABLE, pin]
        await self._send_command(command)

    async def disable_digital_reporting(self, pin):
        """
        Disables digital reporting for a single digital input.

        :param pin: GPIO Pin number.

        """
        command = [PrivateConstants.MODIFY_REPORTING,
                   PrivateConstants.REPORTING_DIGITAL_DISABLE, pin]
        await self._send_command(command)

    async def enable_analog_reporting(self, pin):
        """
        Enables analog reporting for the specified pin.

        :param pin: Analog pin number. For example for ADC0, the number is 0.


        """
        command = [PrivateConstants.MODIFY_REPORTING,
                   PrivateConstants.REPORTING_ANALOG_ENABLE, pin]
        await self._send_command(command)

    async def enable_digital_reporting(self, pin):
        """
        Enable reporting on the specified digital pin.

        :param pin: GPIO Pin number.
        """

        command = [PrivateConstants.MODIFY_REPORTING,
                   PrivateConstants.REPORTING_DIGITAL_ENABLE, pin]
        await self._send_command(command)

    async def get_pico_pins(self):
        """
        This method returns the pico_pins dictionary

        Pin Modes MAP:

            DIGITAL_INPUT = 0

            DIGITAL_OUTPUT = 1

            PWM_OUTPUT = 2

            DIGITAL_INPUT_PULLUP = 3

            DIGITAL_INPUT_PULL_DOWN = 4

            ANALOG_INPUT = 5

            SERVO = 6

            SONAR = 7

            DHT = 8

            I2C = 9

            NEO_PIXEL = 10

            AT_MODE_NOT_SET = 255

        :return: pico_pins
        """
        return self.pico_pins

    async def loop_back(self, start_character, callback=None):
        """
        This is a debugging method to send a character to the
        pico device, and have the device loop it back.

        :param start_character: The character to loop back. It should be
                                an integer.

        :param callback: Looped back character will appear in the callback method

        """
        command = [PrivateConstants.LOOP_COMMAND, ord(start_character)]
        self.loop_back_callback = callback
        await self._send_command(command)

    async def pwm_write(self, pin, duty_cycle=0):
        """
        Set the specified pin to the specified value.
        This is a PWM write.

        :param pin: pico GPIO pin number

        :param duty_cycle: output value - This is dependent upon
                           the PWM range. Default is 20000, but it
                           may be modified by calling pwm_range


        """
        if self.pico_pins[pin] != PrivateConstants.AT_PWM_OUTPUT \
                and self.pico_pins[pin] != PrivateConstants.AT_SERVO:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('pwm_write: You must set the pin mode before '
                               'performing an pwm write.')

        if not (0 <= duty_cycle <= self.maximum_pwm_duty_cycle):
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Raw PWM duty cycle out of range')

        value = duty_cycle.to_bytes(2, byteorder='big')

        command = [PrivateConstants.ANALOG_WRITE, pin, value[0], value[1]]
        await self._send_command(command)

    async def i2c_read(self, address, register, number_of_bytes,
                       callback=None, i2c_port=0, no_stop=False):
        """
        Read the specified number of bytes from the specified register for
        the i2c device.


        :param address: i2c device address

        :param register: i2c register (or None if no register selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Required callback function to report i2c data as a
                   result of read command

       :param i2c_port: 0 = port 0, 1 = port 1

       :param no_stop: If true, master retains control of the bus at the end of the
                       transfer (no Stop is issued), and the next transfer will
                       begin with a Restart rather than a Start.


        callback returns a data list:
        [I2C_READ_REPORT, i2c_port, i2c_device_address, count of data bytes,
        data bytes,
        time-stamp]

        I2C_READ_REPORT = 10

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('I2C Read: A callback function must be specified.')

        # i2c_port = 0 for port 0
        if i2c_port == 0:
            if not self.i2c_0_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'I2C Write: set_pin_mode_i2c never called for i2c port 0.')
            else:
                self.i2c_callback = callback

        else:
            if not i2c_port == 1:
                if not self.i2c_0_active:
                    if self.shutdown_on_exception:
                        await self.shutdown()
                    raise RuntimeError(
                        'I2C Write: set_pin_mode_i2c never called for i2c port 1.')
                else:
                    self.i2c_callback2 = callback

        command = [PrivateConstants.I2C_READ, i2c_port, address, register,
                   number_of_bytes, no_stop]

        # no register specified
        if not register:
            command[3] = PrivateConstants.I2C_NO_REGISTER

        await self._send_command(command)

    async def i2c_write(self, address, args, i2c_port=0, no_stop=False):
        """
        Write data to an i2c device.

        :param address: i2c device address

        :param args: A variable number of bytes to be sent to the device
                     passed in as a list.
                     NOTE: THIS MUST BE IN THE FORM OF A LIST.

        :param i2c_port: 0= port 0, 1 = port 1

        :param no_stop: If true, master retains control of the bus at the end of the
                       transfer (no Stop is issued), and the next transfer will
                       begin with a Restart rather than a Start.

        """
        if not i2c_port:
            if not self.i2c_0_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'I2C Write: set_pin_mode i2c never called for i2c port 0.')

        elif i2c_port:
            if not self.i2c_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'I2C Write: set_pin_mode i2c never called for i2c port 2.')

        command = [PrivateConstants.I2C_WRITE, i2c_port, address, len(args), no_stop]

        for item in args:
            command.append(item)

        await self._send_command(command)

    async def neo_pixel_set_value(self, pixel_number, r=0, g=0, b=0, auto_show=False):
        """
        Set the selected pixel in the pixel array on the Pico to
        the value provided.

        :param pixel_number: pixel number

        :param r: red value 0-255

        :param g: green value 0-255

        :param b: blue value 0-255

        :param auto_show: call show automatically

        """
        if not self.neopixels_initiated:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('You must call set_pin_mode_neopixel first')

        if not 0 <= pixel_number < self.number_of_pixels:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Pixel number is out of legal range')

        for color in [r, g, b]:
            if not 0 <= color <= 255:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('RGB values must be in the range of 0-255')

        command = [PrivateConstants.SET_NEOPIXEL, pixel_number, r, g, b, auto_show]
        await self._send_command(command)

        if auto_show:
            await self.neopixel_show()

    async def neopixel_clear(self, auto_show=True):
        """
        Clear all pixels

        :param auto_show: call show automatically

        """
        if not self.neopixels_initiated:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('You must call set_pin_mode_neopixel first')
        command = [PrivateConstants.CLEAR_NEOPIXELS, auto_show]
        await self._send_command(command)
        if auto_show:
            await self.neopixel_show()

    async def neopixel_fill(self, r=0, g=0, b=0, auto_show=True):
        """
        Fill all pixels with specified value

        :param r: 0-255

        :param g: 0-255

        :param b: 0-255

        :param auto_show: call show automatically
        """
        if not self.neopixels_initiated:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('You must call set_pin_mode_neopixel first')
        for color in [r, g, b]:
            if not 0 <= color <= 255:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('RGB values must be in the range of 0-255')
        command = [PrivateConstants.FILL_NEOPIXELS, r, g, b, auto_show]
        await self._send_command(command)

        if auto_show:
            await self.neopixel_show()

    async def neopixel_show(self):
        """
        Write the NeoPixel buffer stored in the Pico to the NeoPixel strip.

        """
        if not self.neopixels_initiated:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('You must call set_pin_mode_neopixel first')
        command = [PrivateConstants.SHOW_NEOPIXELS]
        await self._send_command(command)

    async def set_pin_mode_analog_input(self, adc_number, differential=0, callback=None):
        """
        Set a pin as an analog input.

        :param adc_number: ADC Number 0-4

                           ADC numbers are mapped as following:
                           ADC0 = GPIO 26 (Physical Pin 31)
                           ADC1 = GPIO 27 (Physical Pin 32)
                           ADC2 = GPIO 28 (Physical Pin 34)

                           Internal Mapping
                           ADC3 = GPIO 29 (Physical Pin 35) ADC Reference Voltage
                           ADC4 = GPIO 30 (No Physical pin - mapped internally)
                                          CPU temperature

        :param differential: difference in previous to current value before
                             report will be generated

        :param callback: callback function


        callback returns a data list:

        [ANALOG_REPORT, pin_number, pin_value, raw_time_stamp]

        The ANALOG_REPORT  = 3

        """
        # make sure adc number is in range
        if not 0 <= adc_number < 5:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Invalid ADC Number')
        await self._set_pin_mode(adc_number, PrivateConstants.AT_ANALOG, differential,
                                 callback=callback)

    async def set_pin_mode_digital_input(self, pin_number, callback=None):
        """
        Set a pin as a digital input.

        :param pin_number: pico GPIO pin number

        :param callback: callback function


        callback returns a data list:

        [DIGITAL_REPORT, pin_number, pin_value, raw_time_stamp]

        DIGITAL_REPORT = 2

        """
        await self._set_pin_mode(pin_number, PrivateConstants.AT_INPUT, callback=callback)

    async def set_pin_mode_digital_input_pullup(self, pin_number, callback=None):
        """
        Set a pin as a digital input with pullup enabled.

        :param pin_number: pico GPIO pin number

        :param callback: callback function


        callback returns a data list:

        [DIGITAL_REPORT, pin_number, pin_value, raw_time_stamp]

        The DIGITAL_REPORT = 2

        """
        await self._set_pin_mode(pin_number, PrivateConstants.AT_INPUT_PULLUP,
                                 callback=callback)

    async def set_pin_mode_digital_input_pull_down(self, pin_number, callback=None):
        """
        Set a pin as a digital input with pull down enabled.

        :param pin_number: pico GPIO pin number

        :param callback: callback function


        callback returns a data list:

        [DIGITAL_REPORT, pin_number, pin_value, raw_time_stamp]

        DIGITAL_REPORT= 2

        """
        await self._set_pin_mode(pin_number, PrivateConstants.AT_INPUT_PULL_DOWN,
                                 callback=callback)

    async def set_pin_mode_digital_output(self, pin_number):
        """
        Set a pin as a digital output pin.

        :param pin_number: pico GPIO pin number
        """

        await self._set_pin_mode(pin_number, PrivateConstants.AT_OUTPUT)

    async def set_pin_mode_neopixel(self, pin_number=28, num_pixels=8,
                                    fill_r=0, fill_g=0, fill_b=0):
        """
        Initialize the pico for NeoPixel control. Fill with rgb values specified.

        Default: Set all the pixels to off.

        :param pin_number: neopixel GPIO control pin

        :param num_pixels: number of pixels in the strip

        :param fill_r: initial red fill value 0-255

        :param fill_g: initial green fill value 0-255

        :param fill_b: initial blue fill value 0-255


        """
        for color in [fill_r, fill_g, fill_b]:
            if not 0 <= color <= 255:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('RGB values must be in the range of 0-255')

        self.number_of_pixels = num_pixels

        command = [PrivateConstants.INIT_NEOPIXELS, pin_number,
                   self.number_of_pixels, fill_r, fill_g, fill_b]

        await self._send_command(command)

        self.pico_pins[pin_number] = PrivateConstants.AT_NEO_PIXEL

        self.neopixels_initiated = True

    async def set_pin_mode_pwm_output(self, pin_number):
        """
        Enable a pin as a PWM pin. Maximum number of PWMs is 16.
        The frequency is fixed at 50 hz.

        Note: There are up to 16 pins that can be assigned as
        PWM. Servo pins share the 16 PWM pins.


        :param pin_number: pico GPIO pin number

        """

        if pin_number in self.pico_pins:
            self.pico_pins[pin_number] = PrivateConstants.AT_PWM_OUTPUT
            if self.pwm_active_count >= 15:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'pwm or servo set mode: number of active PWM pins is at maximum')

            self.pwm_active_count += 1

            await self._set_pin_mode(pin_number, PrivateConstants.AT_PWM_OUTPUT)
        else:
            if not 0 <= pixel_number < self.number_of_pixels:
                if self.shutdown_on_exception:
                    await self.shutdown()
            raise RuntimeError('Gpio Pin Number is invalid')

    async def set_pin_mode_i2c(self, i2c_port=0, sda_gpio=4, scl_gpio=5):
        """
        Establish the standard pico i2c pins for i2c utilization.

        :param i2c_port: 0 = i2c0, 1 = i2c1

        :param sda_gpio: gpio pin assigned to SDA

        :param scl_gpio: gpio pin assigned to SCL


        NOTES:
               1. THIS METHOD MUST BE CALLED BEFORE ANY I2C REQUEST IS MADE <br>
               2. Callbacks are set within the individual i2c read methods of this
              API.

              See i2c_read, and i2c_write

        """
        # determine if the i2c port is specified correctly
        if i2c_port not in [0, 1]:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('i2c port must be either a 0 or 1')
        # determine if the sda and scl gpio's are valid
        if sda_gpio not in self.i2c_sda_pins:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'GPIO {sda_gpio} is an invalid i2c SDA GPIO')
        if scl_gpio not in self.i2c_scl_pins:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'GPIO {scl_gpio} is an invalid i2c SCL GPIO')

        # are both GPIOs available?
        if not self.i2c_sda_pins[sda_gpio] == 255:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'GPIO SDA pin {sda_gpio} is already in use.')
        if not self.i2c_scl_pins[scl_gpio] == 255:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'GPIO SCL pin {scl_gpio} is already in use.')
        # both pins available - mark the sda and scl dictionaries appropriately
        self.i2c_sda_pins[sda_gpio] = self.i2c_scl_pins[scl_gpio] = i2c_port

        # now mark the pico_pins dictionary for these pins
        self.pico_pins[sda_gpio] = self.pico_pins[scl_gpio] = PrivateConstants.AT_I2C

        # determine if the specified sda or scl pin has already been
        # assigned.

        # test for i2c port 0
        if not i2c_port:
            self.i2c_0_active = True
        # port 1
        else:
            self.i2c_1_active = True

        command = [PrivateConstants.I2C_BEGIN, i2c_port, sda_gpio, scl_gpio]
        await self._send_command(command)

    async def set_pin_mode_dht(self, pin, callback=None):
        """

      :param pin: connection pin

      :param callback: callback function

      callback returns a data list:

        DHT REPORT, DHT_DATA=1, PIN, Humidity,  Temperature (c),Time]

        DHT_REPORT =  12

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_dht: A Callback must be specified')

        if self.dht_count < PrivateConstants.MAX_DHTS:
            self.dht_callbacks[pin] = callback
            self.dht_count += 1
            self.pico_pins[pin] = PrivateConstants.AT_DHT
            command = [PrivateConstants.DHT_NEW, pin]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(
                f'Maximum Number Of DHTs Exceeded - set_pin_mode_dht fails for pin {pin}')

    # noinspection PyRedundantParentheses
    async def set_pin_mode_servo(self, pin_number, min_pulse=1000, max_pulse=2000):
        """

        Attach a pin to a servo motor

        Servo mode is a specialized version of PWM Output mode.
        There are 16 PWM pins shared between the Servo and PWM Output modes.

        :param pin_number: pin

        :param min_pulse: minimum pulse width in microseconds

        :param max_pulse: maximum pulse width in microseconds

        """

        await self._set_pin_mode(pin_number, PrivateConstants.AT_SERVO, min_pulse,
                                 max_pulse)
        self.pico_pins[pin_number] = PrivateConstants.AT_SERVO

    async def set_pin_mode_spi(self, spi_port=0, chip_select=None, speed_maximum=500000,
                         data_order=1, data_mode=0):

        """
        Specify the SPI port. The SPI port is configured as a "master".
        Optionally specify the chip select pin.

        This command also specifies the SPISettings for the selected SPI port.

        This method sets the SPISettings structure based on parameter values
        provided.

        SPI support is provided as an abstraction. It is intended that
        only a single device is connected to an SPI port.

        :param spi_port: 0 = spi0, 1 = spi1

        :param chip_select:  spi0 = 17  spi1 = 13 or select another pin

        :param speed_maximum: The maximum speed of communication. Maximum is 50000000

        :param data_order: 1=MSBFIRST,  0=LSBFIRST,

        :param data_mode: 0=MODE0, 1=MODE1, 2=MODE2 3=MODE3

        miso: SPI data receive pin  spi0 = 16  spi1 = 12

        mosi: SPI data transmit pi  spi0 = 19  spi1 = 15

        clock_pin: clock pin        spi0 = 18  spi1 = 14


        command message: [command, spi, chip_select, speed, data_order, data_mode]
        """
        # determine if the spi port is specified correctly
        if spi_port not in [0, 1]:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('spi port must be either a 0 or 1')

        if not (0 < speed_maximum < 50000000):
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('spi port speed maximum is out of range')

        if data_order not in [0, 1]:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('spi data order must be 0 or 1')

        if data_mode not in [0, 1, 2, 3]:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('spi data data mode must be 0, 1, 3 or 3')

        if spi_port == 0:
            self.spi_0_active = True
            miso = 16
            mosi = 19
            if chip_select:
                self.spi0_chip_select = chip_select
            else:
                chip_select = 17
            clock_pin = 18

        else:
            self.spi_1_active = True
            miso = 12
            mosi = 15
            if chip_select:
                self.spi1_chip_select = chip_select
            else:
                chip_select = 13
            clock_pin = 14

        freq_bytes = speed_maximum.to_bytes(4, byteorder='big')

        self.pico_pins[mosi] = PrivateConstants.AT_SPI
        self.pico_pins[miso] = PrivateConstants.AT_SPI
        self.pico_pins[clock_pin] = PrivateConstants.AT_SPI
        self.pico_pins[chip_select] = PrivateConstants.AT_SPI

        command = [PrivateConstants.SPI_INIT, spi_port, chip_select, freq_bytes[0],
                   freq_bytes[1], freq_bytes[2], freq_bytes[3], data_order, data_mode]
        await self._send_command(command)

    async def servo_write(self, pin_number, value):
        """
        Write the value to the specified servo

        :param pin_number: GPIO pin number

        :param value: value between 0 and 180

        """

        if self.pico_pins[pin_number] != PrivateConstants.AT_SERVO:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('You must call set_pin_mode_servo before trying to '
                               'write a value to a servo or servo was detached.')

        # get the min and max for the servo and calculate the duty-cycle
        min_duty = self.servo_ranges[pin_number][PrivateConstants.MIN_SERVO_DUTY_CYCLE]
        max_duty = self.servo_ranges[pin_number][PrivateConstants.MAX_SERVO_DUTY_CYCLE]

        servo_range = max_duty - min_duty

        duty_cycle = int(value / 180 * servo_range) + min_duty

        # use a raw pwm write from the calculated values
        await self.pwm_write(pin_number, duty_cycle, True)

    async def spi_cs_control(self, chip_select_pin, select):
        """
        Control an SPI chip select line
        :param chip_select_pin: pin connected to CS

        :param select: 0=select, 1=deselect
        """

        if self.pico_pins[chip_select_pin] != PrivateConstants.AT_SPI:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError(f'spi_read_blocking: Invalid chip select pin'
                               f' {chip_select_pin}.')
        command = [PrivateConstants.SPI_CS_CONTROL, chip_select_pin, select]
        await self._send_command(command)

    async def spi_read_blocking(self, register, number_of_bytes, spi_port=0,
                              call_back=None):
        """
        Read the specified number of bytes from the specified SPI port and
        call the callback function with the reported data.

        On the server side, this command incorporates SPI.beginTransaction
        and chip select control.

        :param register: Register to be selected

        :param number_of_bytes: Number of bytes to read

        :param spi_port: SPI port 0 or 1

        :param call_back: Required callback function to report spi data as a
                   result of read command

        callback returns a data list:
        [SPI_READ_REPORT, spi_port, count of data bytes, data bytes, time-stamp]

        SPI_READ_REPORT = 13

        """
        if spi_port == 0:
            if not self.spi_0_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_read_blocking: set_pin_mode_spi never called for spi port 0.')

        elif spi_port == 1:
            if not self.spi_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_read_blocking: set_pin_mode_spi never called for spi port 1.')

        if not call_back:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('spi_read_blocking: A Callback must be specified')
        if spi_port == 0:
            self.spi_callback = call_back
        else:
            self.spi_callback2 = call_back

        command = [PrivateConstants.SPI_READ_BLOCKING, spi_port, register,
                   number_of_bytes]
        await self._send_command(command)

    async def spi_set_format(self, spi_port=0, data_bits=8, spi_polarity=0, spi_phase=0):
        """
        Configure how the SPI serializes and de-serializes data on the wire.

        :param spi_port: SPI port 0 or 1

        :param data_bits: Number of data bits per transfer. Valid range = 4-16

        :param spi_polarity: clock polarity. 0 or 1.

        :param spi_phase: clock phase. 0 or 1.
        """
        if not spi_port:
            if not self.spi_0_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_set_format: set_pin_mode_spi never called for spi port 0.')

        elif spi_port:
            if not self.spi_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_set_format: set_pin_mode_spi never called for spi port 1.')
        command = [PrivateConstants.SPI_SET_FORMAT, spi_port, data_bits,
                   spi_polarity, spi_phase]
        await self._send_command(command)

    async def spi_write_blocking(self, bytes_to_write, spi_port=0):
        """
        Write a list of bytes to the SPI device.

        :param bytes_to_write: A list of bytes to write. This must be in the form of a
        list.

        :param spi_port: SPI port 0 or 1

        """
        if not spi_port:
            if not self.spi_0_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_write_blocking: set_pin_mode_spi never called for spi port 0.')

        elif spi_port:
            if not self.spi_1_active:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError(
                    'spi_write_blocking: set_pin_mode_spi never called for spi port 1.')
        command = [PrivateConstants.SPI_WRITE_BLOCKING, spi_port,
                   len(bytes_to_write)]

        for data in bytes_to_write:
            command.append(data)

        await self._send_command(command)

    async def set_pin_mode_sonar(self, trigger_pin, echo_pin, callback=None):
        """
        :param trigger_pin:  Sensor trigger gpio pin

        :param echo_pin: Sensor echo gpio pin

        :param callback: callback

       callback returns a data list:

       [ SONAR_DISTANCE, trigger_pin, distance_value, time_stamp]

       SONAR_DISTANCE =  11

        """

        if not callback:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('set_pin_mode_sonar: A Callback must be specified')

        if self.sonar_count < PrivateConstants.MAX_SONARS:
            self.sonar_callbacks[trigger_pin] = callback
            self.sonar_count += 1
            self.pico_pins[trigger_pin] = self.pico_pins[echo_pin] = \
                PrivateConstants.AT_SONAR

            command = [PrivateConstants.SONAR_NEW, trigger_pin, echo_pin]
            await self._send_command(command)
        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Maximum number of supported sonar devices exceeded.')

    async def _set_pin_mode(self, pin_number, pin_state, differential=0, value_range=0,
                            callback=None):

        """
        A private method to set the various pin modes.

        :param pin_number: pico pin number

        :param pin_state: INPUT/OUTPUT/ANALOG/PWM/PULLUP

        :param differential: for analog inputs - threshold
                             value to be achieved for report to
                             be generated

                           : for servo we overload this variable to mean the minimum
                             duty cycle

        :param value_range: for servo this is the maximum duty cycle

        :param callback: A reference to a call back function to be
                         called when pin data value changes

        """
        # Map ADC to GPIO pin numbers
        if pin_state == PrivateConstants.AT_ANALOG:
            self.pico_pins[26 + pin_number] = PrivateConstants.AT_ANALOG
        else:
            if pin_number in self.pico_pins:
                self.pico_pins[pin_number] = pin_state
            else:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('Gpio Pin Number is invalid')

        if callback:
            if pin_state == PrivateConstants.AT_INPUT:
                self.digital_callbacks[pin_number] = callback
            elif pin_state == PrivateConstants.AT_INPUT_PULLUP:
                self.digital_callbacks[pin_number] = callback
            elif pin_state == PrivateConstants.AT_INPUT_PULL_DOWN:
                self.digital_callbacks[pin_number] = callback
            elif pin_state == PrivateConstants.AT_ANALOG:
                self.analog_callbacks[pin_number] = callback

            else:
                print('{} {}'.format('set_pin_mode: callback ignored for '
                                     'pin state:', pin_state))

        if pin_state == PrivateConstants.AT_INPUT:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_INPUT, 1]

        elif pin_state == PrivateConstants.AT_INPUT_PULLUP:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_INPUT_PULLUP, 1]

        elif pin_state == PrivateConstants.AT_INPUT_PULL_DOWN:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_INPUT_PULL_DOWN, 1]

        elif pin_state == PrivateConstants.AT_OUTPUT:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_OUTPUT]

        elif pin_state == PrivateConstants.AT_ANALOG:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_ANALOG,
                       differential >> 8, differential & 0xff, 1]

        elif pin_state == PrivateConstants.AT_PWM_OUTPUT:
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_PWM_OUTPUT]

        elif pin_state == PrivateConstants.AT_SERVO:
            # we reuse the PWM_OUTPUT command
            command = [PrivateConstants.SET_PIN_MODE, pin_number,
                       PrivateConstants.AT_PWM_OUTPUT]
            self.servo_ranges[pin_number] = [differential, value_range]

        else:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Unknown pin state')

        if pin_state == PrivateConstants.AT_ANALOG:
            if pin_number == 0:
                self.pico_pins[26] = PrivateConstants.AT_ANALOG
            elif pin_number == 1:
                self.pico_pins[27] = PrivateConstants.AT_ANALOG
            elif pin_number == 13:
                self.pico_pins[28] = PrivateConstants.AT_ANALOG

        else:
            self.pico_pins[pin_number] = pin_state

        if command:
            await self._send_command(command)

    async def shutdown(self):
        """
        This method attempts an orderly shutdown
        If any exceptions are thrown, they are ignored.

        """
        self.shutdown_flag = True
        # stop all reporting - both analog and digital
        try:
            command = [PrivateConstants.STOP_ALL_REPORTS]
            await self._send_command(command)

            await asyncio.sleep(.5)

            if self.reset_on_shutdown:
                command = [PrivateConstants.RESET_BOARD]
                await self._send_command(command)
                await asyncio.sleep(.2)

            # await self.serial_port.reset_input_buffer()
            await self.serial_port.close()
            if self.close_loop_on_shutdown:
                self.loop.stop()
        except (RuntimeError, SerialException):
            pass

    async def _spi_report(self, report):
        """
        Execute callback for spi reads.

        :param report: [spi_port, number of bytes read, data]

        """

        cb_list = [PrivateConstants.SPI_REPORT, report[0], report[1]] + report[2:]

        cb_list.append(time.time())

        if cb_list[1]:
            await self.spi_callback2(cb_list)
        else:
            await self.spi_callback(cb_list)

    '''
    report message handlers
    '''

    async def reset_board(self):
        """
        Send a command to the Pico to perform a hardware reset
        """
        command = [PrivateConstants.RESET_BOARD]
        await self._send_command(command)
        await asyncio.sleep(.2)

    async def _pico_report_dispatcher(self):
        """
        This is a private method.
        It continually accepts and interprets data coming from Telemetrix4RPiPico,and then
        dispatches the correct handler to process the data.

        It first receives the length of the packet, and then reads in the rest of the
        packet. A packet consists of a length, report identifier and then the report data.
        Using the report identifier, the report handler is fetched from report_dispatch.

        :returns: This method never returns
        """

        while True:
            if self.shutdown_flag:
                break
            try:
                packet_length = await self.serial_port.read()
            except TypeError:
                continue
            except OSError:
                break

            # get the rest of the packet
            try:
                packet = await self.serial_port.read(packet_length)
            except TypeError:
                continue
            except OSError:
                break

            report = packet[0]

            # handle all other messages by looking them up in the
            # command dictionary

            # noinspection PyArgumentList
            await self.report_dispatch[report](packet[1:])

            await asyncio.sleep(self.sleep_tune)

    async def _analog_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for analog messages.

        :param data: message data

        """
        pin = data[0]
        value = (data[1] << 8) + data[2]
        # set the current value in the pin structure
        time_stamp = time.time()
        if self.analog_callbacks[pin]:
            message = [PrivateConstants.ANALOG_REPORT, pin, value, time_stamp]
            await self.analog_callbacks[pin](message)

    async def _dht_report(self, report):
        """
        This is the dht report handler method.

        :param report:

                    This is the dht report handler method.

        :param report:
               data[0] = report error return
                                No Errors = 0

                                Checksum Error = 1

                                Timeout Error = 2

                                Invalid Value = 999

               data[1] = pin number

               data[2] = humidity positivity flag

               data[3] = temperature positivity value

               data[4] = humidity integer

               data[5] = humidity fractional value

               data[6] = temperature integer

               data[7] = temperature fractional value


        """
        if report[0] != 0:  # DHT_ERROR
            # error report
            # data[0] = report sub type, data[1] = pin, data[2] = error message
            if self.dht_callbacks[report[1]]:
                # Callback 0=DHT REPORT, DHT_ERROR, PIN, Time
                message = [PrivateConstants.DHT_REPORT, report[0], report[1],
                           time.time()]
                self.dht_callbacks[report[1]](message)
        else:
            # got valid data DHT_DATA
            f_humidity = float(report[4] + report[5] / 100)
            if report[2]:
                f_humidity *= -1.0
            f_temperature = float(report[6] + report[7] / 100)
            if report[3]:
                f_temperature *= -1.0
            message = [PrivateConstants.DHT_REPORT, report[0], report[1],
                       f_humidity, f_temperature, time.time()]

            try:
                await self.dht_callbacks[report[1]](message)
                await asyncio.sleep(.8)
            except KeyError:
                pass

        """
        cb = self.dht_callbacks[data[0]]

        cb_list = [PrivateConstants.DHT_REPORT, data[0],
                   (data[1] + (data[2] / 100)), (data[3] + (data[4] / 100)), time.time()]
        await cb(cb_list)
        """

    async def _digital_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for Digital Messages.

        :param data: digital message

        """
        try:
            pin = data[0]
            value = data[1]
        except IndexError:
            return

        time_stamp = time.time()
        if self.digital_callbacks[pin]:
            message = [PrivateConstants.DIGITAL_REPORT, pin, value, time_stamp]
            await self.digital_callbacks[pin](message)

    async def _i2c_read_report(self, data):
        """
        Execute callback for i2c reads.

        :param data: [I2C_READ_REPORT, i2c_port, i2c_address,
        register, number of bytes read, bytes read..., time-stamp]
        """

        cb_list = [PrivateConstants.I2C_READ_REPORT, data[0], data[1]] + data[2:]

        cb_list.append(time.time())

        if cb_list[1]:
            await self.i2c_callback2(cb_list)
        else:
            await self.i2c_callback(cb_list)

    async def _i2c_too_few_bytes_received(self, data):
        """
        I2c write attempt failed

        :param data: data[0] = i2c_device
        """
        print(f'i2c Too few bytes received for I2C port {data[0]}')
        if self.shutdown_on_exception:
            await self.shutdown()

    async def _i2c_too_many_bytes_received(self, data):
        """
        I2c read failed

        :param data: data[0] = i2c device
        """
        print(f'i2c Too few bytes received for I2C port {data[0]}')
        if self.shutdown_on_exception:
            await self.shutdown()

    async def _report_loop_data(self, data):
        """
        Print data that was looped back
        :param data: byte of loop back data
        :return:
        """
        if self.loop_back_callback:
            await self.loop_back_callback(data)

    async def _report_unique_id(self, data):
        """
        Reply to are_u_there message
        :param data: pico id
        """

        for i in range(len(data)):
            self.reported_pico_id.append(data[i])

    async def _report_firmware_version(self, data):
        """
        Reply to are_u_there message
        :param data: pico id
        """

        for i in range(len(data)):
            self.firmware_version.append(data[i])

    async def _report_debug_data(self, data):
        """
        Print debug data sent from pico
        :param data: data[0] is a byte followed by 2
                     bytes that comprise an integer
        :return:
        """
        value = (data[1] << 8) + data[2]
        print(f'DEBUG ID: {data[0]} Value: {value}')

    async def _send_command(self, command):
        """
        This is a private utility method.

        :param command:  command data in the form of a list

        :returns: number of bytes sent
        """
        # the length of the list is added at the head
        command.insert(0, len(command))
        # print(command)
        try:
            send_message = bytes(command)
        except ValueError:
            print('a')
        if self.serial_port is None:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Is your USB cable plugged in?')
        try:
            await self.serial_port.write(send_message)
        except AttributeError:
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError('Is your USB cable plugged in?')

    async def _servo_unavailable(self, report):
        """
        Message if no servos are available for use.
        :param report: pin number
        """
        if self.shutdown_on_exception:
            await self.shutdown()
        raise RuntimeError(
            f'Servo Attach For Pin {report[0]} Failed: No Available Servos')

    async def _sonar_distance_report(self, report):
        """

        :param report: data[0] = trigger pin, data[1] and data[2] = distance

        callback report format: [PrivateConstants.SONAR_DISTANCE, trigger_pin,
        distance  in centimeters, time_stamp]
        """

        # get callback from pin number
        cb = self.sonar_callbacks[report[0]]

        # build report data
        if report[1] == 0 and report[2] == 0:
            cb_list = [PrivateConstants.SONAR_DISTANCE, report[0],
                       0, time.time()]
        else:
            cb_list = [PrivateConstants.SONAR_DISTANCE, report[0],
                       (report[1] + (report[2] / 100)), time.time()]

        await cb(cb_list)
