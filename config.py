# -*- coding: utf-8 -*-

import sys
import logging
from os import environ
from messages import *

DRY_RUN = environ.get('DRY_RUN', True)
DAYS_INACTIVE = int(environ.get('DAYS_INACTIVE', 60))
DEFAULT_NOTIFICATION_CHANNEL = ''
JOIN_CHANNELS = False

logging.basicConfig(
    level=logging.DEBUG,
    filename='logs.log',
    datefmt='%Y-%m-%d %H:%M:%S',
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def get_env_var(var_str: str) -> str:
    """
    Helper function to try getting the specified environmental variable.
    Returns the value of the environmental variable if set.
    Returns an empty string otherwise.

    :param var_str: The environmental variable to check for.
    :return: result or ''
    """
    try:
        result = environ.get(var_str)
        if not result:
            logging.critical(f'"{var_str}" has not been set. Halting...')
        else:
            logging.info(f'"{var_str}" has been set. Continuing...')
            return result
    except ValueError as e:
        print(f'Error getting "{var_str}".')
        print(f'Error: {e}\n')

    return ''


def get_vars() -> tuple:
    """
    Checks the following:
        - Is API_TOKEN set?
        - Is SLACK_URL set?
    :return: token, url
    """
    token_str = 'API_TOKEN'
    url_str = 'SLACK_URL'

    token = get_env_var(token_str)
    url = get_env_var(url_str)

    checks = [token, url]

    if not any([checks]):
        print('Sanity check did not pass. Check log for details.')
        logging.info(log_end)
        sys.exit(1)

    logging.info('All sanity checks passed! Continuing...\n')
    return token, url


api_token, slack_url = get_vars()
