# -*- coding: utf-8 -*-
import logging
import time
import requests
from config import *
from messages import *
from typing import Dict


def api_call(
    endpoint: str,
    payload: Dict = None,
    json_data: Dict = None,
    content_type: str = 'application/json',
    method: str = 'GET',
    full_response: bool = False
):
    """
    Makes a Slack API call to the given endpoint.
    Returns a json object of the results if successful.
    Returns [] otherwise

    :param content_type: Specifies the content type to send with header.
    :param endpoint: The API endpoint to call.
    :param payload: Any optional parameters.
    :param json_data: Any option json data to send.
    :param method: Type of call to make. Ex. "Get", "POST", etc.
    :param full_response: If true returns full response. If false, returns response.json()
    :return: list data: JSON data resulting from the call.
    """
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
    if json_data:
        response = requests.request(
            method, url, headers=headers, json=json_data
        )
    else:
        response = requests.request(
            method, url, headers=headers, params=payload
        )
    try:
        if response.status_code == 429:  # Rate limit reached
            retry_after = int(response.headers.get('retry-after', '1'))

            print('Rate limit reached.')
            print(f'Retrying after {retry_after} seconds...')
            logging.warning(f'Rate limit reached. Retry time: {retry_after}\n')

            time.sleep(retry_after)
            print('Back to work...')
        elif response.status_code == 200:
            data = response.json()

            if data['ok']:
                print('Call successful.\n')
                logging.debug(data)
                if full_response:
                    return response
                return response.json()
            else:
                logging.critical(f'Error: {response.content}')
                logging.critical(log_end)
                sys.exit(1)
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


def join_channels(channels: list) -> None:
    """
    Joins the specified channels. Channels must be public.

    :param channels: List of channel IDs
    :return: None
    """

    endpoint = 'conversations.join'

    for channel in channels:
        pass

    return None


def get_channels(
        include_private: bool = False,
        exclude_archived: bool = True
) -> list:
    """
    Gets a list of all channels in the org.
    Only checks for public, unarchived channels unless specified otherwise.

    :param: include_private: Set to True if private channels should be included
    :param: exclude_archived: Set to False if archived channel should be included
    :return: results: A list of channel objects
    """
    endpoint = 'conversations.list'
    content = 'application/x-www-form-urlencoded'
    results = []

    if include_private:
        types = 'public_channel,private_channel'
    else:
        types = 'public_channel'

    cursor = None
    while True:
        payload = {
            'cursor': cursor,
            'exclude_archived': exclude_archived,
            'types': types,
            'limit': 200  # Actual max = 1,000 but Slack docs recommend 200 max
        }

        response = api_call(
            endpoint, content_type=content, payload=payload
        )

        results.extend(response['channels'])

        if not response["response_metadata"].get("next_cursor"):
            break
        cursor = response["response_metadata"]["next_cursor"]

    return results


def is_channel_exempt(channel_id: str) -> bool:
    allowed_channels = ''

    return True


def is_channel_active(channel_id: str) -> bool:
    return True


def get_channel_members(channel_id: str) -> list:
    """
    Returns a list of the member names of the given channel ID.

    :param channel_id: Channel ID to get members from.
    :return: results: List of member names.
    """
    members_endpoint = 'conversations.members'  # Returns member IDs
    users_endpoint = 'users.info'  # Returns all user info including name

    members = []  # All member IDs
    results = []  # Just the member names parsed from "members"

    cursor = None
    while True:
        members_payload = {
            'channel': channel_id,
            'cursor': cursor,
            'limit': 200  # Actual max = 1,000 but Slack docs recommend 200 max
        }
        response = api_call(
            members_endpoint,
            payload=members_payload,
            content_type='application/x-www-form-urlencoded',
        )
        members.extend(response['members'])

        if not response['response_metadata'].get('next_cursor'):
            break

        cursor = response['response_metadata']['next_cursor']

    for member in members:
        users_payload = {'user': member}
        user_info = api_call(users_endpoint, payload=users_payload)

        profile = user_info['user']['profile']
        name = profile['real_name']

        results.append(name)

    return results


def send_message(
        msg: str,
        channel: str = DEFAULT_NOTIFICATION_CHANNEL,
) -> None:
    """
    Helper function used to send the given message to the given channel.

    :param msg: The message to send.
    :param channel: The channel to send to. Can be a channel name or ID.
    :return: None
    """
    # Would be better to use blocks instead of just text
    endpoint = 'chat.postMessage'
    payload = {
        "channel": channel,
        "text": msg
    }

    api_call(endpoint, json_data=payload, method='POST')

    return None


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

    # get_channel_members('C03NYT9Q25A')
    get_channels()

    logging.info('Script completed successfully.')
    logging.info(log_end)
