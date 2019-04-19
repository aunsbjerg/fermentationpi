"""
Todo:
    - integrate with tilt device (see: tiltpi implementation)
    - async implementation using twisted/tornado
    - add web based ui
    - integrate with brewersfriend api
"""
import logging
import time
import click
import RPi.GPIO as GPIO
from Configuration import import_configuration, default_configuration
from TemperatureControl import TemperatureControl
from Drivers.Factories import relay_factory, temperature_factory


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%d-%m-%y %H:%M:%S', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def cleanup():
    """
    Simple routine to call after exceptions or on program halt to make sure that relays are in off position
    and that gpio has been deinitialized.
    """
    try:
        compressor_relay.off()

    except:
        pass

    GPIO.cleanup()


@click.command()
@click.option('--configpath', type=click.Path(), help='configuration file location')
@click.option('--setpoint', default=18.0, show_default=True, help='temperature setpoint in °C')
def main(configpath, setpoint):
    """
    _tbd_
    """
    logger.info('starting application')

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        config = import_configuration(configpath) if configpath else default_configuration()

        beer_temp = temperature_factory(config['beer_temperature'])
        fridge_temp = temperature_factory(config['fridge_temperature'])
        compressor_relay = relay_factory(config['compressor_relay'])

        temp_control = TemperatureControl(fridge_temp, beer_temp, compressor_relay)
        temp_control.set_temperature_setpoint(setpoint)
        temp_control.start()

        while True:
            time.sleep(1.0)
            temp_control.control_loop()

    except KeyboardInterrupt:
        logger.warning('CTRL+C detected, stopping')

    except Exception:
        logger.error('Exception occured', exc_info=True)

    cleanup()


if __name__ == '__main__':
    main()
