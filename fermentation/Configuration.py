"""
sensor calibration
setpoint
temperature profile
beer name / log file
tilt id?
sensor and relay pin numbers
"""

import logging
import yaml
from copy import deepcopy


logger = logging.getLogger(__name__)


_default_config = {
    'fridge_temperature': {
        'type': 'max31865',
        'offset': 0.0,
        'pins': {
            'cs': 8,
            'miso': 9,
            'mosi': 10,
            'clk': 11
        }
    },
    'beer_temperature': {
        'type': 'tilt',
    },
    'compressor_relay': {
        'type': 'ssr',
        'pin': 18,
        'active_high': True
    },
    'heater_relay': {
        'type': 'ssr',
        'pin': 20,
        'active_high': True
    }
}


def import_configuration(filepath):
    """
    Attempts to load a configuration from the provided filepath.
    Returns the loaded configuration as a dictionary
    """
    logger.info(f'loading configuration from {filepath}')
    config = dict()

    with open(filepath, 'r') as yamlfile:
        config = yaml.load(yamlfile)

    return config


def default_configuration():
    """
    Return a dictionary containing the default configuration.
    """
    logger.info('loading default configuration')
    return deepcopy(_default_config)
