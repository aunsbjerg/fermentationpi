"""
liberally stolen from 
https://github.com/adafruit/Adafruit_CircuitPython_MAX31865/blob/master/adafruit_max31865.py
"""

import math
import time
from gpiozero import AnalogInputDevice

_MAX31865_CONFIG_REG       = 0x00
_MAX31865_CONFIG_BIAS      = 0x80
_MAX31865_CONFIG_MODEAUTO  = 0x40
_MAX31865_CONFIG_MODEOFF   = 0x00
_MAX31865_CONFIG_1SHOT     = 0x20
_MAX31865_CONFIG_3WIRE     = 0x10
_MAX31865_CONFIG_24WIRE    = 0x00
_MAX31865_CONFIG_FAULTSTAT = 0x02
_MAX31865_CONFIG_FILT50HZ  = 0x01
_MAX31865_CONFIG_FILT60HZ  = 0x00
_MAX31865_RTDMSB_REG       = 0x01
_MAX31865_RTDLSB_REG       = 0x02
_MAX31865_HFAULTMSB_REG    = 0x03
_MAX31865_HFAULTLSB_REG    = 0x04
_MAX31865_LFAULTMSB_REG    = 0x05
_MAX31865_LFAULTLSB_REG    = 0x06
_MAX31865_FAULTSTAT_REG    = 0x07
_MAX31865_FAULT_HIGHTHRESH = 0x80
_MAX31865_FAULT_LOWTHRESH  = 0x40
_MAX31865_FAULT_REFINLOW   = 0x20
_MAX31865_FAULT_REFINHIGH  = 0x10
_MAX31865_FAULT_RTDINLOW   = 0x08
_MAX31865_FAULT_OVUV       = 0x04
_RTD_A                     = 3.9083e-3
_RTD_B                     = -5.775e-7

class MAX31865(AnalogInputDevice):
    """
    Must be implemented from scratch. 
    Can look to existing MCPxxxx drivers for inspiration.
    Consider making a PR for gpiozero if implementation is decent, so it can
    get added to gpiozero baseline.
    """
    
    def __init__(self, wires=2, bias=True, ref_resistor=430.0, rtd_nominal=100, **spi_args):
        """
        wires: 2, 3, 4
        """
        super().__init__(bits=15, max_voltage=3.3, **spi_args)
        self._spi.clock_mode = 1 # CPOL = false, CPHA = true
        self._ref_resistor = ref_resistor
        self._rtd_nominal = rtd_nominal
        self.wires = wires
        self.bias = bias
        self.auto_convert = False
        self.filter = 60

    @property
    def wires(self):
        return self._wires

    @wires.setter
    def wires(self, value):
        config = self._read_config()

        if value == 2 or value == 4:
            config &= ~_MAX31865_CONFIG_3WIRE

        elif value == 3:
            config |= _MAX31865_CONFIG_3WIRE

        else:
            raise Exception('MAX31865: number of wires must be 2, 3 or 4 but was {}'.format(value))

        self._write_config(config)
        self._wires = values

    @property
    def bias(self):
        return bool(self._read_byte(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_BIAS)

    @bias.setter
    def bias(self, value):
        config = self._read_config()

        if value:
            config |= _MAX31865_CONFIG_BIAS # enable

        else:
            config &= ~_MAX31865_CONFIG_BIAS # disable

        self._write_config(config)

    @property
    def auto_convert(self):
        return bool(self._read_byte(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_MODEAUTO)

    @auto_convert.setter
    def auto_convert(self, value):
        config = self._read_config()

        if value:
            config |= _MAX31865_CONFIG_MODEAUTO # enable

        else:
            config &= ~_MAX31865_CONFIG_MODEAUTO # disable

        self._write_config(config)

    @property
    def filter(self):
        return 50 if self._read_byte(_MAX31865_CONFIG_REG) & _MAX31865_CONFIG_FILT50HZ else 60

    @filter.setter
    def filter(self, value):
        config = self._read_config()

        if value == 50:
            config |= _MAX31865_CONFIG_FILT50HZ

        elif value == 60:
            config &= ~_MAX31865_CONFIG_FILT50HZ

        else:
            raise Exception('Invalid filter chosen, 50 and 60 are valid values, not {}'.format(value))

        self._write_config(config)

    @property
    def fault(self):
        pass

    def clear_faults(self):
        pass

    @property
    def temperature(self):
        """
        http://www.analog.com/media/en/technical-documentation/application-notes/AN709_0.pdf
        """
        resistance = self.resistance
        Z1 = -_RTD_A
        Z2 = _RTD_A * _RTD_A - (4 * _RTD_B)
        Z3 = (4 * _RTD_B) / self.rtd_nominal
        Z4 = 2 * _RTD_B
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

    def _read_rtd(self):
        """
        _tbd_ this should actually handle auto/1-shot conversion setting and bias better
        """
        self.clear_faults()
        self.bias = True # why even property when always true?
        time.sleep(0.01)
        config = self._read_config()
        config |= _MAX31865_CONFIG_1SHOT
        self._write_config(config)
        time.sleep(0.065)
        rtd = self._read_byte(_MAX31865_RTDLSB_REG)
        rtd = rtd | (self._read_byte(_MAX31865_RTDMSB_REG) << 8)
        return rtd >> 1

    def _read_resistance(self):
        resistance = self._read_rtd()
        resistance /= 32768
        return resistance * self._ref_resistor

    def _read_byte(self, address):
        return self._spi.transfer(self._int_to_words(address & 0x7F))[0]

    def _write_byte(self, address, value):
        self._spi.transfer(self._int_to_words((address | 0x80) | (value << 8)))

    def _read_config(self):
        return self._read_byte(_MAX31865_CONFIG_REG)        

    def _write_config(self, value):
        self._write_byte(_MAX31865_CONFIG_REG, config)
