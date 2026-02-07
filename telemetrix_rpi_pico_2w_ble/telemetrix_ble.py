"""
 Copyright (c) 2026 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import asyncio
import threading

from bleak import BleakClient, BleakScanner

# UUIDs for the Nordic UART Service

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"

# Characteristics
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


class TelemetrixBle:
    """
    This class encapsulates management of a BLE UART connection that communicates
    with a Raspberry Pi Pico 2W using synchronous methods backed by asyncio.
    
    This implementation is compatible with Jupyter notebooks without requiring nest_asyncio.
    """

    def __init__(self, ble_device_name: str, receive_notification_callback):
        """
        :param ble_device_name: Advertised Device Name.

        :param receive_notification_callback: Callback to process received
                                              transport data.
        """
        self.ble_device_name = ble_device_name
        self.receive_notification_callback = receive_notification_callback
        self.ble_device = None
        self.bleak_client = None
        
        # Event loop management for thread-based execution
        self._loop = None
        self._loop_thread = None
        self._loop_ready = threading.Event()
        
        # Start the event loop in a separate thread
        self._start_event_loop()

    def _start_event_loop(self):
        """Start an event loop in a separate thread."""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop_ready.set()
            self._loop.run_forever()
        
        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        self._loop_ready.wait()

    def _run_coroutine(self, coro):
        """
        Run a coroutine in the background event loop and return the result.
        This works even when called from within another event loop (like Jupyter).
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def connect(self):
        """
        This method connects to a device matching the ble_device_name
        """
        return self._run_coroutine(self._connect_async())

    async def _connect_async(self):
        """Async implementation of connect."""
        print(f'Scanning for BLE device {self.ble_device_name}.  Please wait...')

        self.ble_device = await BleakScanner.find_device_by_name(self.ble_device_name)
        if self.ble_device is None:
            raise RuntimeError('Did not find the BLE device. Please check name.')
        print(f'Found  {self.ble_device_name}  address: {self.ble_device.address}')
        
        self.bleak_client = BleakClient(self.ble_device.address)
        await self.bleak_client.connect()
        if not self.bleak_client.is_connected:
            raise RuntimeError('Failed to connect to BLE device')
        
        # Enable received data notification
        await self.bleak_client.start_notify(UART_TX_CHAR_UUID,
                                             self.receive_notification_callback)

    def write(self, data: bytes):
        """
        This method writes data to the BLE device
        :param data: Data to write
        """
        return self._run_coroutine(self._write_async(data))

    async def _write_async(self, data: bytes):
        """Async implementation of write."""
        await self.bleak_client.write_gatt_char(UART_RX_CHAR_UUID, data)

    def disconnect(self):
        """
        This method disconnects from the BLE device
        """
        result = self._run_coroutine(self._disconnect_async())
        # Stop the event loop thread
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)
        return result

    async def _disconnect_async(self):
        """Async implementation of disconnect."""
        if self.bleak_client is not None:
            await self.bleak_client.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
