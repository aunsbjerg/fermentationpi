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
from Drivers.Factories import relay_factory, temperature_factory, cleanup_drivers


def configure_logger(logpath, loglevel=logging.DEBUG):
    """
    Configure the logging system.
    If a logpath is provided, entries will also be written to that logfile.
    """
    handlers = [logging.StreamHandler()]

    if logpath:
        handlers.append(logging.FileHandler(logpath))

    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%d-%m-%y %H:%M:%S', level=loglevel, handlers=handlers)


logger = logging.getLogger(__name__)


@click.command()
@click.option('--configpath', type=click.Path(), help='configuration file location')
@click.option('--logpath', type=click.Path(), help='log output file location')
@click.option('--setpoint', default=18.0, show_default=True, help='temperature setpoint in °C')
def main(configpath, logpath, setpoint):
    """
    _tbd_
    """
    configure_logger(logpath)
    logger.info('starting application')

    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        config = import_configuration(configpath) if configpath else default_configuration()

        drivers = dict()
        drivers['beer_temp'] = temperature_factory(config['beer_temperature'])
        drivers['fridge_temp'] = temperature_factory(config['fridge_temperature'])
        drivers['compressor_relay'] = relay_factory(config['compressor_relay'])

        temp_control = TemperatureControl(drivers['fridge_temp'], drivers['beer_temp'], drivers['compressor_relay'])
        temp_control.set_temperature_setpoint(setpoint)
        temp_control.start()

        while True:
            time.sleep(1.0)
            temp_control.control_loop()

    except KeyboardInterrupt:
        logger.warning('CTRL+C detected, stopping')

    except Exception:
        logger.error('Exception occured', exc_info=True)

    cleanup_drivers(drivers)
    GPIO.cleanup()


if __name__ == '__main__':
    main()
