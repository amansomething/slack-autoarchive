# -*- coding: utf-8 -*-

import sys
import logging
from os import environ
from messages import *
from datetime import datetime, timedelta

needed_env_vars = [
    'API_TOKEN',
    'DRY_RUN',
]
optional_env_vars = {
    'DAYS_INACTIVE': 90,  # Not inclusive
    'DEFAULT_NOTIFICATION_CHANNEL': 'general',  # "#" is optional
    'JOIN_CHANNELS': True,  # Can set to False if script was recently run to save time.
    'MIN_MEMBERS': 0,  # Skip channels with more members than this. 0 = no skipping
    'RESULTS_FILE': 'results.csv',
}


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


def check_vars() -> None:
    """
    Checks the following:
        - Is API_TOKEN set?
        - Is DRY_RUN set?
        If both are not set, raises an exception.

        If both are set, checks to see if any options vars are set.
        If they are, overrides the defaults.

        Checks to see if optional variables are of the correct type.
        It not, raises and exception. This part can likely be improved a lot.

    :return: None
    """
    errors = False

    env_vars = environ.keys()
    sorted_env_vars = sorted(list(env_vars))

    if all(var in env_vars for var in needed_env_vars):
        print('API_TOKEN and DRY_RUN env vars are set. Continuing...\n')

        dry = environ.get('DRY_RUN').strip().lower()
        dry_test = ['true', 'false']
        if dry not in dry_test:
            print(f'DRY_RUN must be True or False. Current value: {dry}')
            errors = True
    else:
        print('Missing a required environmental variable. Currently set vars:')
        for var in sorted_env_vars:
            print(var)
        raise ValueError('API_TOKEN and DRY_RUN must be set.')

    for var in sorted_env_vars:
        if var in optional_env_vars.keys():
            optional_env_vars[var] = environ[var]

    if type(optional_env_vars['DAYS_INACTIVE']) != int:
        days = optional_env_vars['DAYS_INACTIVE']
        try:
            optional_env_vars['DAYS_INACTIVE'] = int(days)
        except ValueError:
            print(f'Issue converting DAYS_INACTIVE to an int. Current value: {days}')
            errors = True

    if type(optional_env_vars['MIN_MEMBERS']) != int:
        min_members = optional_env_vars['MIN_MEMBERS']
        try:
            optional_env_vars['MIN_MEMBERS'] = int(min_members)
        except ValueError:
            print(f'Issue converting MIN_MEMBERS to an int. Current value: {min_members}')
            errors = True

    if type(optional_env_vars['JOIN_CHANNELS']) != bool:
        try:
            join_channels = str(optional_env_vars['JOIN_CHANNELS']).lower()

            if join_channels == 'true':
                optional_env_vars['JOIN_CHANNELS'] = True
            elif join_channels == 'false':
                optional_env_vars['JOIN_CHANNELS'] = False
            else:
                print(f'JOIN_CHANNELS must be True or False. Current value: {join_channels}')
                errors = True
        except ValueError:
            print(f'Issue converting JOIN_CHANNELS to a bool.')
            print('Current value: {optional_env_vars["JOIN_CHANNELS"]}')
            errors = True

    if errors:
        raise ValueError('Issue(s) with optional variables.')

    return None


logging.info(f'Starting new log\n{stars}')
check_vars()

API_TOKEN = environ.get('API_TOKEN')
if environ.get('DRY_RUN').strip().lower() == 'true':  # Env vars can only be str
    DRY_RUN = True
else:
    DRY_RUN = False

RESULTS_FILE = optional_env_vars['RESULTS_FILE']
DAYS_INACTIVE = optional_env_vars['DAYS_INACTIVE']
DEFAULT_NOTIFICATION_CHANNEL = optional_env_vars['DEFAULT_NOTIFICATION_CHANNEL']
JOIN_CHANNELS = optional_env_vars['JOIN_CHANNELS']
MIN_MEMBERS = optional_env_vars['MIN_MEMBERS']
TOO_OLD_DATE = (datetime.now() - timedelta(days=optional_env_vars['DAYS_INACTIVE'])).date()
