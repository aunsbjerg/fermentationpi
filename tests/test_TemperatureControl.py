import unittest
from unittest.mock import Mock
from fermentation.TemperatureControl import TemperatureControl, COMPRESSOR_MIN_OFF_TIME_SEC, COMPRESSOR_MIN_ON_TIME_SEC


class TestTemperatureControl(unittest.TestCase):

    def setUp(self):
        self.setpoint = 20.0
        self.hysteresis = 0.5

        self.mock_fridge_temp = Mock()
        self.mock_beer_temp = Mock()
        self.mock_relay = Mock()

        self.mock_fridge_temp.temperature.return_value = self.setpoint
        self.mock_beer_temp.temperature.return_value = self.setpoint
        self.mock_relay.elapsed_time.return_value = 0

        self.temp_control = TemperatureControl(fridge_temp=self.mock_fridge_temp,
            beer_temp=self.mock_beer_temp, comp_relay=self.mock_relay)

        self.temp_control.set_temperature_setpoint(self.setpoint)
        self.temp_control.set_temperature_hysteresis(self.hysteresis)


    def test_stop_to_neutral(self):
        self.assertEqual(self.temp_control.state, 'stop')
        self.temp_control.start()
        self.assertEqual(self.temp_control.state, 'neutral')


    def test_neutral_to_cooling(self):
        self._stop_to_neutral()

        # to cooling
        self.mock_fridge_temp.temperature.return_value = self.setpoint + self.hysteresis + 0.1
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_OFF_TIME_SEC + 1
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'cooling')
        self.mock_relay.on.assert_called_once()

        # to neutral
        self.mock_fridge_temp.temperature.return_value = self.setpoint - (self.hysteresis + 0.1)
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_ON_TIME_SEC + 1
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'neutral')
        self.mock_relay.off.assert_called_once()


    def test_neutral_to_cooling_hysteresis(self):
        self._stop_to_neutral()

        self.mock_fridge_temp.temperature.return_value = self.setpoint + self.hysteresis
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_OFF_TIME_SEC + 1
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'neutral')


    def test_neutral_to_cooling_off_timer(self):
        self._stop_to_neutral()

        self.mock_fridge_temp.temperature.return_value = self.setpoint + self.hysteresis + 0.1
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_OFF_TIME_SEC
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'neutral')


    def test_cooling_to_neutral_hysteresis(self):
        self._neutral_to_cooling()

        self.mock_fridge_temp.temperature.return_value = self.setpoint - (self.hysteresis - 0.1)
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_ON_TIME_SEC + 1
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'cooling')


    def test_cooling_to_neutral_on_timer(self):
        self._neutral_to_cooling()

        self.mock_fridge_temp.temperature.return_value = self.setpoint - self.hysteresis
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_ON_TIME_SEC
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'cooling')


    def test_neutral_to_stop(self):
        self._stop_to_neutral()
        self.temp_control.stop()
        self.assertEqual(self.temp_control.state, 'stop')
        self.mock_relay.off.assert_called_once()


    def test_cooling_to_stop(self):
        self._neutral_to_cooling()
        self.temp_control.stop()
        self.assertEqual(self.temp_control.state, 'stop')
        self.mock_relay.off.assert_called_once()


    def _stop_to_neutral(self):
        self.temp_control.start()
        self.assertEqual(self.temp_control.state, 'neutral')


    def _neutral_to_cooling(self):
        self._stop_to_neutral()
        self.mock_fridge_temp.temperature.return_value = self.setpoint + self.hysteresis + 0.1
        self.mock_relay.elapsed_time.return_value = COMPRESSOR_MIN_OFF_TIME_SEC + 1
        self.temp_control.control_loop()
        self.assertEqual(self.temp_control.state, 'cooling')


if __name__ == '__main__':
    unittest.main()
