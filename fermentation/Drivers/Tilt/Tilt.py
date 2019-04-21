
import logging
import time
from threading import Thread, Event
from Drivers.Tilt.blescan import create_blescan_socket, parse_events


logger = logging.getLogger(__name__)


TILTS = {
    'red':    'a495bb10c5b14b44b5121370f02d74de',
    'green':  'a495bb20c5b14b44b5121370f02d74de',
    'black':  'a495bb30c5b14b44b5121370f02d74de',
    'purple': 'a495bb40c5b14b44b5121370f02d74de',
    'orange': 'a495bb50c5b14b44b5121370f02d74de',
    'blue':   'a495bb60c5b14b44b5121370f02d74de',
    'yellow': 'a495bb70c5b14b44b5121370f02d74de',
    'pink':   'a495bb80c5b14b44b5121370f02d74de',
}


def _fahrenheit_to_celsius(temperature):
    """
    Converts a fahrenheit temperature to celsius
    """
    return round((temperature - 32.0) / 1.8, ndigits=2)


class Tilt:
    """
    Implements logic for retrieving temperature and gravity beacons from a tilt device.
    Tilt devices are identified by their colour, which is mapped to their bluetooth uuid.

    Inspired by on https://github.com/JustinFuhrmeister-Clarke/pytilt

    Notes:
    if more than one Tilt should be supported, blescan must be implemented in a single separate
    thread, otherwise each tilt object will have it's own blescan which probably wont work
    """

    def __init__(self, tilt_colour, timeout=120):
        """
        Initializes resources used by Tilt driver.
        The thread is started as a daemon because we don't want it to keep the program alive
        after the main thread is killed. A graceful shutdown is attempted in destroy()
        """
        logger.info(f"creating {tilt_colour} tilt device")
        self._colour = tilt_colour
        self._timeout = timeout
        self._temperature = 0.0
        self._gravity = 0.0
        self._stop_flag = Event()
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()


    def temperature(self):
        """
        Returns the latest received Tilt temperature reading in celsius
        """
        return self._temperature


    def gravity(self):
        """
        Returns the latest received Tilt gravity reading
        """
        return self._gravity


    def destroy(self):
        """
        Stops the beacon sc an thread safely
        """
        self._stop_flag.set()
        self._thread.join(timeout=10)


    def _loop(self):
        """
        Internal beacon scan loop that continuously scans for tilt beacons.
        Beacons are sent roughly every 30 seconds from the Tilt.
        If time interval between beacons gets too big, a warning is issued.
        """
        last_beacon_time = time.time()
        socket = create_blescan_socket()

        while not self._stop_flag.is_set():
            beacons = parse_events(socket, 10)

            for beacon in beacons:
                if beacon['uuid'] == TILTS[self._colour]:
                    self._temperature = _fahrenheit_to_celsius(beacon['major'])
                    self._gravity = beacon['minor']
                    last_beacon_time = time.time()
                    logger.debug(f"beacon received, {beacon['major']} {beacon['minor']}")

            if time.time() - last_beacon_time > self._timeout:
                logger.warning(f"tilt beacon not received in {time.time() - last_beacon_time}s")

            # don't block too long when stopping
            for i in range(10):
                if not self._stop_flag.is_set():
                    time.sleep(1)
