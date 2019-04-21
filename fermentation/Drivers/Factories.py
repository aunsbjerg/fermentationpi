import logging
from Drivers.SolidStateRelay import SolidStateRelay
from Drivers.MAX31865 import MAX31865
from Drivers.Tilt.Tilt import Tilt


logger = logging.getLogger(__name__)


def temperature_factory(config):
    """
    Factory method to create a temperature sensor given a configuration containing type and
    necessary configuration variables for that type
    """
    sensor = None

    if config['type'] == 'max31865':
        sensor = MAX31865(cs_pin=config['pins']['cs'], miso_pin=config['pins']['miso'],
            mosi_pin=config['pins']['mosi'], clk_pin=config['pins']['clk'])
        logger.info('MAX31865 temperature sensor created')

    elif config['type'] == 'tilt':
        sensor = Tilt(tilt_colour=config['colour'])
        logger.info('Tilt temperature sensor created')

    else:
        raise Exception(f'Unknown temperature sensor type, {config["type"]}')

    return sensor


def relay_factory(config):
    """
    Factory method to create a relay given a configuration containing relay type and necessary
    configuration variables for that type
    """
    relay = None

    if config['type'] == 'ssr':
        relay = SolidStateRelay(pin=config['pin'], active_high=config['active_high'], initial_state=False)
        logger.info('Solid state relay created')

    else:
        raise Exception(f'Unknown relay type, {config["type"]}')

    return relay


def cleanup_drivers(drivers):
    """
    Cleans up drivers depending on their object type.
    Expects a dictionary of drivers
    """
    for name, driver in drivers.items():
        if isinstance(driver, SolidStateRelay):
            logger.debug(f"cleaning {name}: setting to off")
            driver.off()

        elif isinstance(driver, Tilt):
            logger.debug(f"cleaning {name}: destroying")
            driver.destroy()

        else:
            logger.debug(f"cleaning {name}: nothing to do")
