# -*- coding: utf-8 -*-

import requests
import pprint
from config import *
from messages import *
from typing import Dict


def api_call(
    endpoint: str,
    payload: Dict = None,
    content_type: str = 'application/json',
    method: str = 'GET',
):
    """
    Makes a Slack API call to the given endpoint.
    Returns a json object of the results if successful.
    Returns [] otherwise

    :param content_type: Specifies the content type to send with header.
    :param endpoint: The API endpoint to call.
    :param payload: Any optional parameters.
    :param method: Type of call to make. Ex. "Get", "POST", etc.
    :return: list data: JSON data resulting from the call.
    """
    # TODO: Add rate limiting https://api.slack.com/docs/rate-limits#tier_t2
    base_url = 'https://slack.com/api'

    if endpoint[0] == '/':
        url = base_url + endpoint
    else:
        url = base_url + '/' + endpoint

    print(f'Making API call to: {url}...')
    logging.debug(f'Making API call to: {url}...')

    headers = {
        'Content-type': content_type,
        'Authorization': 'Bearer ' + api_token
    }

    # Make the API call and handle the response
    response = requests.request(
        method, url, headers=headers, params=payload
    )
    try:
        if response.status_code == 200:
            data = response.json()

            if data['ok']:
                print('Call successful.\n')
                logging.debug(data)
                return response.json()
            else:
                logging.warning(data)
                return []
        else:
            print(response.text)
            logging.critical(f'Error: {response.status_code} - {response.reason}')
            logging.critical(response)
            logging.critical(log_end)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.critical(f'Error: {e}')
        logging.info(log_end)
        raise SystemExit(e)


def test_call() -> bool:
    """
    Tries making a test api call to see if it is successful.
    If so, returns True. Returns False otherwise.
    :return: bool
    """
    endpoint = '/auth.test'

    if api_call(endpoint):
        return True

    return False


def join_channel(channel: str) -> None:
    return None


def get_channels(include_private: bool = False) -> Dict:
    """
    Gets a list of all channels in the org.
    Only checks for public channels unless specified otherwise.
    :return: All channels
    """
    endpoint = 'conversations.list'
    content = 'application/x-www-form-urlencoded'
    if include_private:
        types = 'public_channel,private_channel'
    else:
        types = 'public_channel'

    payload = {
        'types': types
    }

    results = api_call(endpoint, content_type=content, payload=payload)

    return results


def is_channel_exempt(channel_id: str) -> bool:
    allowed_channels = ''

    return True


def is_channel_active(channel_id: str) -> bool:
    return True


def get_channel_members(channel_id: str) -> list:
    pass


def send_message(msg, channel_name=DEFAULT_NOTIFICATION_CHANNEL) -> None:
    """
    Helper function used to send the given message to the given channel.

    :param msg: The message to send.
    :param channel_name: The channel to send to.
    :return:
    """
    pass


def archive_channel(channel_id: str) -> bool:
    """
    Archives the specified channel and returns True if successful.
    Returns False otherwise.

    :param channel_id: The ID of the channel to be archived
    :return: bool
    """
    return True


def send_admin_report(channel_name: str = DEFAULT_NOTIFICATION_CHANNEL) -> None:
    """
    Sends an admin report to the specified channel.
    In a dry run, it sends a list of the channels that would be archived.
    In a non-dry run, it sends a list of the channels that were archived.

    :return: None
    """
    pass


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if not test_call():
        logging.info(log_end)
        raise Exception(
            'Issue making a test API call. Check log for details.'
        )

    channels = get_channels()
    print(type(channels))
    pprint.pprint(channels)

    logging.info('Script completed successfully.')
    logging.info(log_end)
