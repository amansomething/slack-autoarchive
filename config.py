# -*- coding: utf-8 -*-

import logging
from os import environ
from messages import *
from datetime import datetime, timedelta

optional_env_vars = {
    'DRY_RUN': False,  # Only archives channels when set to True
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


def check_if_int(var: str) -> bool:
    """
    Checks to see if the given string exists as an environmental variable.
    If so, checks if the value of that variable is an int.
    If not, tries to convert to an int and update optional_env_vars.

    :param var: Name of the env var to check.
    :return: bool
        True if var value is an int or can be converted to int.
        False otherwise.
    """
    if type(optional_env_vars[var]) == int:
        return True

    val = optional_env_vars[var]
    try:
        optional_env_vars[var] = int(val)
        return True
    except ValueError:
        print(f'Issue converting {var} to an int. Current value: {val}')
        return False


def check_if_bool(var: str) -> bool:
    """
    Checks to see if the given string exists as an environmental variable.
    If so, checks if the value of that variable is true or false.
    If not, tries to convert to a bool and update optional_env_vars.

    :param var: Name of the env var to check.
    :return: bool
        True if var value is a bool or can be converted to a bool.
        False otherwise.
    """
    if type(optional_env_vars[var]) == bool:
        return True

    val = optional_env_vars[var].lower()
    try:
        if val == 'true':
            optional_env_vars[var] = True
            return True
        elif val == 'false':
            optional_env_vars[var] = False
            return True
        else:
            print(f'{var} must be True or False. Current value: {val}')
            return False
    except ValueError:
        print(f'Issue converting {var} to a bool.')
        print(f'Current value: {val}')
        return False


def check_vars() -> None:
    """
    Checks the following:
        - Is API_TOKEN set?
        If not, raises an exception.

        If set, checks to see if any optional vars are set.
        If they are, overrides the defaults.

        Checks to see if optional variables are of the correct type.
        It not, raises an exception. (This part can likely be coded better.)

    :return: None
    """
    env_vars = [x for x in sorted(list(environ.keys())) if x in optional_env_vars.keys()]
    sorted_env_vars = sorted(list(env_vars))

    if environ.get('API_TOKEN'):
        print('API_TOKEN is set. Continuing...\n')
    else:
        raise ValueError('API_TOKEN must be set.')

    if env_vars:
        for var in sorted_env_vars:
            if var in optional_env_vars.keys():
                optional_env_vars[var] = environ[var]

    if not all([
        check_if_int('DAYS_INACTIVE'),
        check_if_int('MIN_MEMBERS'),
        check_if_bool('JOIN_CHANNELS'),
        check_if_bool('DRY_RUN'),
    ]):
        raise ValueError('Issue(s) with optional variables.')

    return None


logging.info(f'Starting new log\n{stars}')
check_vars()

API_TOKEN = environ.get('API_TOKEN')
DRY_RUN = optional_env_vars['DRY_RUN']
RESULTS_FILE = optional_env_vars['RESULTS_FILE']
DAYS_INACTIVE = optional_env_vars['DAYS_INACTIVE']
DEFAULT_NOTIFICATION_CHANNEL = optional_env_vars['DEFAULT_NOTIFICATION_CHANNEL']
JOIN_CHANNELS = optional_env_vars['JOIN_CHANNELS']
MIN_MEMBERS = optional_env_vars['MIN_MEMBERS']
TOO_OLD_DATE = (datetime.now() - timedelta(days=optional_env_vars['DAYS_INACTIVE'])).date()
