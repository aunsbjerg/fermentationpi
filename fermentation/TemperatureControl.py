import logging
import time
from transitions import Machine


COMPRESSOR_MIN_OFF_TIME_SEC = 300
COMPRESSOR_MIN_ON_TIME_SEC = 180


logger = logging.getLogger(__name__)
logging.getLogger('transitions').setLevel(logging.INFO)


class TemperatureControl:
    """
    This class implements a simple on/off based temperature control with cooler and heater relays
    based on temperature readings from beer and fridge.

    The control mechanism is based around a simple state machine.
    """

    states = ['stop', 'neutral', 'cooling', 'heating']


    def __init__(self, fridge_temp, beer_temp, comp_relay, heater_relay=None):
        """
        Initialises the state machine and sets a default setpoint and hysteresis value
        """
        self._machine = Machine(model=self, states=TemperatureControl.states, initial='stop', ignore_invalid_triggers=True)

        # add transitions            trigger    source     dest       conditions, action, etc
        self._machine.add_transition('start',   'stop',    'neutral')
        self._machine.add_transition('_update', 'neutral', 'cooling', conditions=['_cooling_needed', '_cooling_on_allowed'], before='_start_cooling')
        self._machine.add_transition('_update', 'neutral', 'heating', conditions=['_heating_needed', '_heating_on_allowed'], before='_start_heating')
        self._machine.add_transition('_update', 'cooling', 'neutral', conditions=['_cooling_off_allowed'], unless=['_cooling_needed'], before='_stop_cooling')
        self._machine.add_transition('_update', 'heating', 'neutral', conditions=['_heating_off_allowed'], unless=['_heating_needed'], before='_stop_heating')
        self._machine.add_transition('stop',    '*',       'stop',    before=['_stop_cooling', '_stop_heating'])

        self._fridge_temp = fridge_temp
        self._beer_temp = beer_temp
        self._comp_relay = comp_relay

        logger.info("initialized")

        self.set_temperature_setpoint(20.0)
        self.set_temperature_hysteresis(0.5)


    def set_temperature_setpoint(self, setpoint):
        """
        Sets the temperature setpoint in celsius
        """
        self._setpoint = setpoint
        logger.info(f"temperature setpoint changed to {setpoint:.2f}°C")


    def set_temperature_hysteresis(self, hysteresis):
        """
        Sets the temperature hysteresis in celsius.
        Hysteresis is the same going from neutral to cooling as going from cooling to neutral
        """
        self._hysteresis = hysteresis
        logger.info(f"temperature hysteresis changed to {hysteresis:.2f}°C")


    def control_loop(self):
        """
        Control looped function which updates the temperature readings and updates the state machine.
        Should be called at a fixed time interval
        """
        relay_state = "on" if self._comp_relay.state() else "off"
        fridge_temp = self._fridge_temp.temperature()
        beer_temp = self._beer_temp.temperature()

        logger.debug(f"{self.state} - {relay_state} - {self._comp_relay.elapsed_time():.1f}s - {beer_temp:.2f}°C - {fridge_temp:.2f}°C - {self._setpoint:.2f}°C")

        self._update(temperature=fridge_temp)


    def _cooling_needed(self, temperature, **kwargs):
        """
        Determines if cooling is needed by looking at state, temperature and hysteresis.
        """
        return temperature > (self._setpoint + self._hysteresis) if self.state == 'neutral' else \
               temperature > (self._setpoint - self._hysteresis) if self.state == 'cooling' else False


    def _cooling_on_allowed(self, **kwargs):
        """
        Determines if cooling is actually allowed based on how long the compressor has been turned _off_
        """
        return self._comp_relay.elapsed_time() > COMPRESSOR_MIN_OFF_TIME_SEC


    def _cooling_off_allowed(self, **kwargs):
        """
        Determines if the compressor has been turned _on_ long enough for it to safely be turned _off_
        """
        return self._comp_relay.elapsed_time() > COMPRESSOR_MIN_ON_TIME_SEC


    def _start_cooling(self, **kwargs):
        """
        Turn on the cooling compressor
        """
        self._comp_relay.on()
        logger.info("starting cooling")


    def _stop_cooling(self, **kwargs):
        """
        Turn of the cooling compressor
        """
        self._comp_relay.off()
        logger.info("stopping cooling")


    def _heating_needed(self, temperature, **kwargs):
        """
        _tbd_
        """
        return False # not implemented


    def _heating_on_allowed(self, **kwargs):
        """
        _tbd_
        """
        return False # not implemented


    def _heating_off_allowed(self, **kwargs):
        """
        _tbd_
        """
        return False # not implemented


    def _start_heating(self, **kwargs):
        """
        _tbd_
        """
        logger.info("starting heating")
        pass # not implemented


    def _stop_heating(self, **kwargs):
        """
        _tbd_
        """
        logger.info("stopping heating")
        pass # not implemented
