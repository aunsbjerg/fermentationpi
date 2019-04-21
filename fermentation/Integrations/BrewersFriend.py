import json
import logging
import time
import requests


logger = logging.getLogger(__name__)


class BrewersFriend:
    """
    Implements part of the brewers friend api necessary for pushing
    fermentation stats to BF.

    See: https://docs.brewersfriend.com/api
    """

    def __init__(self, api_key, session_id):
        """
        Stores configuration variables and sets last update time 14 minutes in past to
        allow for quick update when starting fermentation.
        """
        self._api_key = api_key
        self._session_id = session_id
        self._last_update = time.time() - (14 * 60)


    def update(self, beer_temp, fridge_temp, gravity):
        """
        Update interval must be greater than 15 minutes

        tbd: exact integration api not determined, just
        for testing out
        """
        if self._update_allowed():
            url = '{}/{}'.format('https://log.brewersfriend.com/fermentation/import', self._session_id)

            headers = {
                'Content-Type': 'application/json',
                'X-API-KEY': self._api_key
            }

            data = {
                'name': 'fermentation-rpi',
                'temp': beer_temp,
                'temp_unit': 'C',
                'gravity': gravity,
                'gravity_unit': 'G',
                'ambient': fridge_temp,
            }

            req = requests.post(url, headers=headers, data=json.dumps(data))
            logger.debug(f"request: {url}, {headers}, {data}")

            if req.status_code == 200:
                logger.info(f"succesfully updated brewers friend with {beer_temp:2.f}°C and {gravity}")

            elif req.status_code == 429:
                logger.debug("not enough time passed since last update")

            elif req.status_code == 400 or req.status_code == 401:
                msg = req.json()
                logger.error(f"error while updating brewers friend, {msg['detail']}")

            else:
                logger.warning(f"could not access brewers friend, status code {req.status_code}")
                logger.debug(req.content)

        else:
            logger.warning(f"not enough time passed since last update attempt")


    def _update_allowed(self):
        """
        Returns true if more than 15 minutes passed since last update attempt.
        Returns false otherwise.
        """
        return int((time.time() - self._last_update) / 60) >= 15
