#!/usr/bin/python
# -*- coding: utf-8; python-indent-offset: 4; -*-

# The MIT License (MIT)
#
# Copyright (c) 2015 Stephen P. Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
import math
import RPi.GPIO as GPIO


def resistance_to_celsius(resistance, rtd_nominal=100.0):
    """
    Converts a resistance value to temperature in celsius, given a nominal RTD value.
    http://www.analog.com/media/en/technical-documentation/application-notes/AN709_0.pdf
    """
    RTD_A = 3.9083e-3
    RTD_B = -5.775e-7

    Z1 = -RTD_A
    Z2 = RTD_A * RTD_A - (4 * RTD_B)
    Z3 = (4 * RTD_B) / rtd_nominal
    Z4 = 2 * RTD_B
    temp = Z2 + (Z3 * resistance)
    temp = (math.sqrt(temp) + Z1) / Z4

    if temp >= 0:
        return temp

    rpoly = resistance
    temp = -242.02
    temp += 2.2228 * rpoly
    rpoly *= resistance  # square
    temp += 2.5859e-3 * rpoly
    rpoly *= resistance  # ^3
    temp -= 4.8260e-6 * rpoly
    rpoly *= resistance  # ^4
    temp -= 2.8183e-8 * rpoly
    rpoly *= resistance  # ^5
    temp += 1.5243e-10 * rpoly

    return temp


class MAX31865:
    """
    Reading Temperature from the MAX31865 with GPIO using the Raspberry Pi.
    Any 4 pins can be used to establish software based SPI to MAX31865.

    Adapted from: https://github.com/hackenbergstefan/MAX31865
    """

    REGISTERS = {
        'config': 0,
        'rtd_msb': 1,
        'rtd_lsb': 2,
        'high_fault_threshold_msb': 3,
        'high_fault_threshold_lsb': 4,
        'low_fault_threshold_msb': 5,
        'low_fault_threshold_lsb': 6,
        'fault_status': 7,
    }
    """
    Definition of register addresses. (https://datasheets.maximintegrated.com/en/ds/MAX31865.pdf)

    Name                     ReadAddress WriteAddress PorState Access
    Configuration            00h         80h          00h      R/W
    RTD MSBs                 01h         —            00h      R
    RTD LSBs                 02h         —            00h      R
    High Fault Threshold MSB 03h         83h          FFh      R/W
    High Fault Threshold LSB 04h         84h          FFh      R/W
    Low Fault Threshold MSB  05h         85h          00h      R/W
    Low Fault Threshold LSB  06h         86h          00h      R/W
    Fault Status             07h         —            00h      R
    """

    REGISTERS_WRITE_MASK = 0x80
    """Mask to be ORed to register addresses when writing."""

    REGISTER_CONFIGURATION_ONE_SHOT = 0b10100010
    """
    Configuration 0b10110010 == 0xB2:
    bit 7: Vbias -> 1 (ON)
    bit 6: Conversion Mode -> 0 (MANUAL)
    bit 5: 1-shot -> 1 (ON)
    bit 4: 3-wire select -> 0 (2 or 4 wire config)
    bit 3-2: fault detection cycle -> 0 (none)
    bit 1: fault status clear -> 1 (clear any fault)
    bit 0: 50/60 Hz filter select -> 0 (60Hz)
    """

    REGISTER_CONFIGURATION_ONE_SHOT_3_WIRE = REGISTER_CONFIGURATION_ONE_SHOT | 0b00010000
    """
    Configuration 0b10110010 == 0xB2:
    bit 7: Vbias -> 1 (ON)
    bit 6: Conversion Mode -> 0 (MANUAL)
    bit 5: 1-shot -> 1 (ON)
    bit 4: 3-wire select -> 1 (3 wire config)
    bit 3-2: fault detection cycle -> 0 (none)
    bit 1: fault status clear -> 1 (clear any fault)
    bit 0: 50/60 Hz filter select -> 0 (60Hz)
    """

    def __init__(self, cs_pin, miso_pin, mosi_pin, clk_pin, ref_resistor=430.0, rtd_nominal=100.0, number_of_wires=2):
        assert(number_of_wires >= 2 and number_of_wires <= 4)
        self._cs_pin = cs_pin
        self._miso_pin = miso_pin
        self._mosi_pin = mosi_pin
        self._clk_pin = clk_pin
        self._ref_resistor = ref_resistor
        self._rtd_nominal = rtd_nominal
        self._number_of_wires = number_of_wires
        self._setup_GPIO()


    def _setup_GPIO(self):
        """
        Setup GPIOs for SPI connection:
        CS: Chip Select (also called SS)
        CLK: Serial Clock
        MISO: Master In Slave Out (SDO at slave)
        MOSI: Master Out Slave In (SDI at slave)
        """
        GPIO.setup(self._cs_pin, GPIO.OUT)
        GPIO.setup(self._miso_pin, GPIO.IN)
        GPIO.setup(self._mosi_pin, GPIO.OUT)
        GPIO.setup(self._clk_pin, GPIO.OUT)
        GPIO.output(self._cs_pin, GPIO.HIGH)
        GPIO.output(self._clk_pin, GPIO.LOW)
        GPIO.output(self._mosi_pin, GPIO.LOW)


    def __enter__(self):
        return self


    def __exit__(self, *k):
        pass


    def temperature(self):
        """
        Read out temperature. Conversion to °C included.
        """
        rtd = self._read_rtd()
        resistance = self._read_resistance(rtd)
        return resistance_to_celsius(resistance, rtd_nominal=self._rtd_nominal)


    def _write_register(self, register, data):
        """
        Write data to register.

        :param register: Either name or address of register.
        :param data: Single byte to be written.
        """
        GPIO.output(self._cs_pin, GPIO.LOW)

        if isinstance(register, str):
            register = self.REGISTERS[register]

        register |= self.REGISTERS_WRITE_MASK

        self._send(register)
        self._send(data)

        GPIO.output(self._cs_pin, GPIO.HIGH)


    def _read_register(self, register):
        """
        Read data from register.

        :param register: Either name or address of register.
        :return: One byte of data.
        """
        GPIO.output(self._cs_pin, GPIO.LOW)

        if isinstance(register, str):
            register = self.REGISTERS[register]

        self._send(register)
        data = self._recv()
        GPIO.output(self._cs_pin, GPIO.HIGH)
        return data


    def _read_registers(self):
        """
        Read all registers.

        :return: List of 8 bytes data.
        """
        # NOTE: Reusage of self.read_register is slower but more clean.
        data = [self._read_register(r) for r in range(len(self.REGISTERS))]
        return data


    def _read_rtd(self):
        """
        Read RTD from sensor board
        """
        if self._number_of_wires == 3:
            self._write_register('config', MAX31865.REGISTER_CONFIGURATION_ONE_SHOT_3_WIRE)

        else:
            self._write_register('config', MAX31865.REGISTER_CONFIGURATION_ONE_SHOT)

        # Sleep to wait for conversion (Conversion time is less than 100ms)
        time.sleep(0.1)

        temp = self._read_register('rtd_msb')
        temp = (temp << 8) | self._read_register('rtd_lsb')

        # Check if error bit was set
        if temp & 0x01:
            raise MAX31865FaultError(self)

        return temp >> 1


    def _read_resistance(self, rtd):
        resistance = rtd / 32768
        return resistance * self._ref_resistor


    def _send(self, byte):
        """
        Send one byte via configured SPI.
        """
        for bit in range(8):
            GPIO.output(self._clk_pin, GPIO.HIGH)

            if (byte & 0x80):
                GPIO.output(self._mosi_pin, GPIO.HIGH)

            else:
                GPIO.output(self._mosi_pin, GPIO.LOW)

            byte <<= 1
            GPIO.output(self._clk_pin, GPIO.LOW)


    def _recv(self):
        """
        Receive one byte via configured SPI.
        """
        byte = 0x00
        for bit in range(8):
            GPIO.output(self._clk_pin, GPIO.HIGH)
            byte <<= 1

            if GPIO.input(self._miso_pin):
                byte |= 0x1

            GPIO.output(self._clk_pin, GPIO.LOW)

        return byte


class MAX31865FaultError(Exception):
    """
    Fault handling of MAX31865.
    MAX31865 includes onchip fault detection.

    TODO: Improve fault detection. Currently only status register is read.
    """

    def __init__(self, max31865):
        self.max31865 = max31865
        super(MAX31865FaultError, self).__init__(self.status_message())

    def status_message(self):
        """
        10 Mohm resistor is on breakout board to help
        detect cable faults
        bit 7: RTD High Threshold / cable fault open
        bit 6: RTD Low Threshold / cable fault short
        bit 5: REFIN- > 0.85 x VBias -> must be requested
        bit 4: REFIN- < 0.85 x VBias (FORCE- open) -> must be requested
        bit 3: RTDIN- < 0.85 x VBias (FORCE- open) -> must be requested
        bit 2: Overvoltage / undervoltage fault
        bits 1,0 don't care
        """
        status = self.max31865._read_register('fault_status')

        if status & 0x80:
            return "High threshold limit (Cable fault/open)"

        if status & 0x40:
            return "Low threshold limit (Cable fault/short)"

        if status & 0x04:
            return "Overvoltage or Undervoltage Error"

