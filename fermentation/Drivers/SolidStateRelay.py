import time
import RPi.GPIO as GPIO


class SolidStateRelay:
    """
    Simple class representing a solid state relay output.
    """

    def __init__(self, pin, active_high=True, initial_state=False):
        self._pin = pin
        self._active_high = active_high
        GPIO.setup(self._pin, GPIO.OUT)
        self.set_state(initial_state)


    def on(self):
        """
        Sets the relay in the on state
        """
        self.set_state(True)


    def off(self):
        """
        Sets the relay in the off state
        """
        self.set_state(False)


    def set_state(self, state):
        """
        Sets the output state of the relay to active or inactive.
        :param state: True => active, False = inactive
        """
        if state:
            GPIO.output(self._pin, GPIO.HIGH if self._active_high else GPIO.LOW)

        else:
            GPIO.output(self._pin, GPIO.LOW if self._active_high else GPIO.HIGH)

        self._timestamp = time.time()


    def state(self):
        """
        Return the output state of the relay given the active low/high setting
        """
        state = GPIO.input(self._pin)
        return state if self._active_high else not state


    def toggle(self):
        """
        Toggle the output relay
        """
        self.set_state(not GPIO.input(self._pin))


    def elapsed_time(self):
        """
        Returns the time in seconds the relay has been in it's current state.
        """
        return time.time() - self._timestamp
