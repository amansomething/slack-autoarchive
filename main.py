# -*- coding: utf-8 -*-

import csv
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
    charset: str = 'charset=utf-8',
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
    :param charset: Specifies the charset to use. utf-8 by default
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
        'Content-type': f'{content_type}; {charset}',
        'Authorization': 'Bearer ' + api_token
    }

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
                print('Call successful.')
                logging.debug(data)
                if full_response:
                    return response
                return response.json()
            else:
                print(api_error)
                logging.critical(f'Error: {response.content}')
                logging.critical(log_end)
                sys.exit(1)
        else:
            print(api_error)
            logging.critical(f'Error: {response.status_code} - {response.reason}')
            logging.critical(response)
            logging.critical(log_end)
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.critical(f'Error: {e}')
        logging.info(log_end)
        print(api_error)
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

    :param channels: List of channel objects
    :return: None
    """
    if not JOIN_CHANNELS:  # Set in config.py
        return None

    endpoint = 'conversations.join'

    for channel in channels:
        is_channel = channel['is_channel']  # As opposed to a DM, group, etc.
        channel_name = channel['name']

        if is_channel:
            channel_id = channel['id']
            print(f'Attempting to join: {channel_name}...')
            logging.info(f'Attempting to join: {channel_name}...')

            response = api_call(
                method='POST',
                endpoint=endpoint,
                json_data={"channel": channel_id}
            )
            if response['warning']:
                warnings = response['warning'].split(',')
                if 'already_in_channel' in warnings:
                    print(f'Already a member of: {channel_name}\n')
                    logging.info(f'Already a member of: {channel_name}\n')
                else:
                    print(f'Warning(s): {warnings}')
                    logging.warning(f'Warning(s): {warnings}')
            else:
                print(f'Successfully joined: {channel_name}')
                logging.info(f'Successfully joined: {channel_name}')
        else:
            print(f'Skipping joining: {channel_name}')
            logging.info(f'Skipping joining: {channel_name}')

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
    # TODO: Have a local list of channels. If that last was recently generated, return that
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


def is_channel_exempt(channel: Dict) -> bool:
    """
    Checks to see if the given channel object is exempt from being archived.

    :param channel: Channel object
    :return: bool: True if exempt, False if it should be archived
    """
    exempt_channels = [x.strip() for x in EXEMPT_CHANNELS_RAW.splitlines() if x]

    channel_name = channel['name'].strip()
    if channel_name in exempt_channels:
        logging.info(f'{channel_name} is exempt via allow list.')
        return True

    channel_topic = channel['topic']['value']
    exempt_keywords = [x.strip() for x in ALLOWLIST_KEYWORDS_RAW.splitlines() if x]
    exempt_topic = any(word in channel_topic for word in exempt_keywords)
    if channel_topic and exempt_topic:
        logging.info(f'{channel_name} is exempt via channel topic.')
        return True

    return False


def is_channel_active(channel_id: str) -> bool:
    # TODO: Make this work
    return True


def get_channel_members(channel_id: str) -> list:
    """
    Returns a list of the member names of the given channel ID.

    :param channel_id: Channel ID to get members from.
    :return: results: List of member names.
    """
    # TODO: Have a local list of members. If that last was recently generated, return that
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
    # TODO: Would be better to use blocks instead of just text
    endpoint = 'chat.postMessage'
    payload = {
        "channel": channel,
        "text": msg
    }

    api_call(endpoint, json_data=payload, method='POST')

    return None


def archive_channels(channels: list) -> bool:
    """
    Archives the specified channel and returns True if successful.
    Returns False otherwise.

    :param channels: Channel objects
    :return: bool
    """
    results = []
    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['name']
        is_channel = channel['is_channel']  # As opposed to a DM, group, etc.

        if is_channel and not is_channel_exempt(channel):  # Add check to see if valid channel
            print(f'\nGetting member list for: {channel_name}...')
            logging.info(f'\nGetting member list for: {channel_name}...')

            result = {
                'id': channel_id,
                'name': channel_name
            }

            users = get_channel_members(channel_id)
            if users:
                logging.info(
                    users_logging_template.format(
                        channel_name=channel_name,
                        users='\t\n'.join(users)
                    )
                )
                result['users'] = users
            else:
                print(f'No members in: {channel_name}')
                logging.info(f'No members in: {channel_name}')
                result['users'] = []

            endpoint = 'conversations.archive'
            if not DRY_RUN:
                response = api_call(
                    method='POST',
                    endpoint=endpoint,
                    json_data={"channel": channel_id}
                )

                if response['error']:
                    print(f'ERROR archiving: {channel_name}')
                    print(response['error'])
                    logging.warning(channel_name + response['error'])
                    result['archived'] = False
                else:
                    result['archived'] = True
            else:
                print(f'DRY RUN: Would have archived: {channel_name}')
                result['archived'] = True

            results.append(result)
        else:
            print(f'Skipping: {channel_name}')

    try:
        with open(
                RESULTS_FILE, mode='w', encoding='utf-8', newline=''
        ) as csvfile:
            # TODO: Add unarchive link
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            headers = ['Channel', 'Users', 'Successfully Archived?']
            writer.writerow(headers)

            for result in results:
                channel_users = '\n'.join(result['users'])
                if result['archived']:
                    archived = 'Yes'
                else:
                    archived = 'No'

                row = [
                    result['name'],
                    channel_users,
                    archived
                ]

                writer.writerow(row)
    except OSError:
        print(f'Error opening: {RESULTS_FILE}')
        print('Continuing script. Data will be in the log file.')

        for result in results:
            logging.critical(f"Channel: {result['name']}")
            channel_users = '\n'.join(result['users'])
            logging.critical(channel_users)
            logging.critical(dashes)

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
    if DRY_RUN:
        print('This is only a dry run. No channels will be archived.')
    else:
        print('This IS NOT a dry run. Channels will be archived.')
        if input('Continue ("y/n")?: ').lower() != 'y':
            print('Quitting program.')
            logging.info(log_end)
            sys.exit(1)

    if not test_call():
        logging.info(log_end)
        raise Exception(
            'Issue making a test API call. Check log for details.'
        )

    # get_channel_members('C03NYT9Q25A')
    all_channels = get_channels()
    join_channels(all_channels)
    archive_channels(all_channels)

    logging.info('Script completed successfully.')
    logging.info(log_end)
