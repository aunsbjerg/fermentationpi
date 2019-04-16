import unittest
import platform
import sys
from unittest.mock import MagicMock, patch

if platform.system() == 'Windows':
    sys.modules['RPi'] = MagicMock()
    sys.modules['RPi.GPIO'] = MagicMock()

import RPi.GPIO
from fermentation.Drivers.SolidStateRelay import SolidStateRelay


class TestSolidStateRelay(unittest.TestCase):

    @patch('RPi.GPIO.output')
    @patch('RPi.GPIO.setup')
    def test_setup(self, output, setup):
        ssr = SolidStateRelay(10)
        RPi.GPIO.setup.assert_called_once_with(10, RPi.GPIO.OUT)
        RPi.GPIO.output.assert_called_once_with(10, RPi.GPIO.LOW)

    @patch('RPi.GPIO.output')
    def test_setup_initial_high(self, output):
        ssr = SolidStateRelay(10, initial_state=True)
        RPi.GPIO.output.assert_called_once_with(10, RPi.GPIO.HIGH)

    @patch('RPi.GPIO.output')
    def test_setup_active_low(self, output):
        ssr = SolidStateRelay(10, active_high=False, initial_state=True)
        RPi.GPIO.output.assert_called_once_with(10, RPi.GPIO.LOW)

    @patch('RPi.GPIO.output')
    def test_on(self, output):
        ssr = SolidStateRelay(10, initial_state=False)
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.LOW)
        ssr.on()
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.HIGH)

    @patch('RPi.GPIO.output')
    def test_off(self, output):
        ssr = SolidStateRelay(10)
        ssr.on()
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.HIGH)
        ssr.off()
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.LOW)

    @patch('RPi.GPIO.input', return_value=True)
    @patch('RPi.GPIO.output')
    def test_toggle(self, input, output):
        ssr = SolidStateRelay(10)
        ssr.on()
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.HIGH)
        ssr.toggle()
        RPi.GPIO.input.assert_called_with(10)
        RPi.GPIO.output.assert_called_with(10, RPi.GPIO.LOW)


if __name__ == '__main__':
    unittest.main()
