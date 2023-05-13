# -*- coding: utf-8 -*-

import sys
import logging
from os import environ
from messages import *
from datetime import datetime, timedelta

# TODO: User env vars or other files for setting the variables

DRY_RUN = environ.get('DRY_RUN', True)

# Skip channels with more members than this.
# 0 = do not skip any channels based on number of members
MIN_MEMBERS = int(environ.get('MIN_MEMBERS', 0))

DAYS_INACTIVE = int(environ.get('DAYS_INACTIVE', 3))  # Not inclusive
TOO_OLD_DATE = (datetime.now() - timedelta(days=DAYS_INACTIVE)).date()

DEFAULT_NOTIFICATION_CHANNEL = '#apis'  # "#" is optional
JOIN_CHANNELS = True  # Can set to False if script was recently run to save time.
RESULTS_FILE = 'results.csv'

# https://api.slack.com/events/message
# Channel messages with these subtypes do not count when checking if there is a recent message in the channel.
# A list item is generated from this automatically
EXEMPT_SUBTYPES_RAW = '''  
channel_join
channel_leave
'''

# Channels with any of these strings in their topic are skipped
# A list item is generated from this automatically
ALLOWLIST_KEYWORDS_RAW = '''
%noarchive
'''

# These channels are skipped
# A list item is generated from this automatically
EXEMPT_CHANNELS_RAW = '''
general
'''

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
            return ''
        else:
            logging.info(f'"{var_str}" has been set. Continuing...')
            return result
    except ValueError as e:
        print(f'Error getting "{var_str}".')
        print(f'Error: {e}\n')

    return ''


def get_vars() -> str:
    """
    Checks the following:
        - Is API_TOKEN set?

    :return: token
    """
    token_str = 'API_TOKEN'

    token = get_env_var(token_str)

    if not token:
        print('Sanity check did not pass. Check log for details.')
        logging.info(log_end)
        sys.exit(1)

    logging.info('All sanity checks passed! Continuing...\n')
    return token


logging.info(f'Starting new log\n{stars}')
api_token = get_vars()
