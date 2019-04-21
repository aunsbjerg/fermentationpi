import logging
from Integrations.BrewersFriend import BrewersFriend


logger = logging.getLogger(__name__)


def integration_factory(config):
    """
    Factory method to create a single integration object based on a dictionary containing configuration
    values for a single integration instance.
    """
    integration = None

    if config['type'] == 'brewers_friend':
        integration = BrewersFriend(api_key=config['x_api_key'], session_id=config['brew_session_id'])
        logger.info("Brewers friend integration created")

    else:
        raise Exception(f"unknown integration type, {config['type']}")

    return integration
