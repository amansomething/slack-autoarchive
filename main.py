# -*- coding: utf-8 -*-

from config import *
from messages import *
import csv
import sys
import time
import requests
from typing import Dict


def api_call(
    endpoint: str,
    payload: Dict = None,
    json_data: Dict = None,
    content_type: str = 'application/json',
    charset: str = 'utf-8',
    method: str = 'GET',
    full_response: bool = False,
    files: Dict = None
) -> requests.models.Response:
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
    :param files: Files object to upload

    :return: list data: JSON data resulting from the call.
    """
    base_url = 'https://slack.com/api'

    if endpoint[0] == '/':
        url = base_url + endpoint
    else:
        url = base_url + '/' + endpoint

    print(f'Making API call to: {url}...')
    logging.debug(f'API call: {url}...')

    if charset:
        headers = {
            'Content-type': f'{content_type}; charset={charset}',
        }
    else:
        headers = {
            'Content-type': f'{content_type}',
        }

    headers['Authorization'] = 'Bearer ' + API_TOKEN

    if json_data:
        response = requests.request(method, url, headers=headers, json=json_data)
    elif files:
        response = requests.request(method, url, data=payload, files=files)
    else:
        response = requests.request(method, url, headers=headers, params=payload)

    try:
        if response.status_code == 429:  # Rate limit reached
            retry_after = int(response.headers.get('retry-after', '0'))

            print('Rate limit reached.')
            print(f'Retrying after {retry_after} seconds...')
            logging.warning(f'Rate limit reached. Retry time: {retry_after}\n')

            time.sleep(retry_after)
            print('Back to work...')
        elif response.status_code == 200:
            data = response.json()

            if data['ok']:
                print('Call successful.')
                logging.debug(response)
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
            logging.debug(f'Attempting to join: {channel_name}...')

            response = api_call(
                method='POST', endpoint=endpoint,
                json_data={"channel": channel_id}
            )
            if response.get('warning'):
                warnings = response['warning'].split(',')
                if 'already_in_channel' in warnings:
                    print(f'Already a member of: {channel_name}\n')
                    logging.debug(f'Already a member of: {channel_name}\n')
                else:
                    print(f'Warning(s): {warnings}')
                    logging.warning(f'Warning(s): {warnings}')
            else:
                print(f'Successfully joined: {channel_name}')
                logging.debug(f'Successfully joined: {channel_name}')
        else:
            print(f'Skipping joining: {channel_name}')
            logging.debug(f'Skipping joining: {channel_name}')

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
    # Improvement idea: Have a local list of channels. If that last was recently generated, return that
    print('Getting a list of all channels...')

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

        response = api_call(endpoint, content_type=content, payload=payload)

        results.extend(response['channels'])

        if not response["response_metadata"].get("next_cursor"):
            break
        cursor = response["response_metadata"]["next_cursor"]

    logging.debug(f'Channels: {results}')
    print()

    return results


def is_channel_exempt(channel: Dict) -> bool:
    """
    Checks to see if the given channel object is exempt from being archived.
    A channel can be exempt due to one of the following reasons:
    - Has more than the MIN_MEMBERS (if MIN_MEMBERS > 0)
    - Channel name is listed in EXEMPT_CHANNELS_RAW
    - Channel topic has a keyword listed in ALLOWLIST_KEYWORDS_RAW
    - Channel is created recently (within the TOO_OLD_DATE date)

    :param channel: Channel object
    :return: bool: True if exempt, False if it should be archived
    """
    channel_name = channel['name'].strip()
    if MIN_MEMBERS and len(channel['members']) >= MIN_MEMBERS:
        logging.info(f'{channel_name} is exempt via number of members.')
        print(f'{channel_name} is exempt via number of members.')
        return True

    exempt_channels = [x.strip() for x in EXEMPT_CHANNELS_RAW.splitlines() if x]
    if channel_name in exempt_channels:
        logging.info(f'{channel_name} is exempt via allow list.')
        print(f'{channel_name} is exempt via allow list')
        return True

    channel_topic = channel['topic']['value']
    exempt_keywords = [x.strip() for x in ALLOWLIST_KEYWORDS_RAW.splitlines() if x]
    exempt_topic = any(word in channel_topic for word in exempt_keywords)
    if channel_topic and exempt_topic:
        logging.info(f'{channel_name} is exempt via channel topic.')
        print(f'{channel_name} is exempt via channel topic')
        return True

    creation_date = datetime.fromtimestamp(float(channel['created'])).date()
    if creation_date > TOO_OLD_DATE:
        logging.info(f'{channel_name} is exempt due to creation date ({creation_date}).')
        print(f'{channel_name} is exempt via creation date ({creation_date})')
        return True

    return False


def is_channel_active(channel_id: str) -> bool:
    """
    - Determines if any valid messages have been sent to the channel.
    - If so, any in the last "DAYS_INACTIVE" set in config.py?
    - If so, returns True. Returns False otherwise

    :param channel_id: Slack channel ID
    :return: bool
    """
    skip_subtypes = [x.strip() for x in EXEMPT_SUBTYPES_RAW.splitlines() if x]
    endpoint = 'conversations.history'
    content = 'application/x-www-form-urlencoded'

    payload = {
        'channel': channel_id,
        'count': 1,
        'inclusive': True
    }

    response = api_call(endpoint, content_type=content, payload=payload)
    logging.debug(response)

    if not response.get('messages'):
        # No messages in channel.
        # Newly created channels are already skipped via is_channel_exempt()
        return False

    message = response['messages'][0]
    if 'subtype' in message and message['subtype'] in skip_subtypes:
        # Not a message type that we care about
        return False

    message_date = datetime.fromtimestamp(float(message['ts'])).date()
    if message_date < TOO_OLD_DATE:
        # Message is too old
        return False

    return True


def get_channel_members(channel_id: str) -> list:
    """
    Returns a list of the member names of the given channel ID.

    :param channel_id: Channel ID to get members from.
    :return: results: List of member names.
    """
    # Improvement idea: Have a local list of members. If that last was recently generated, return that
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


def write_results(
    team_id: str,
    results: list
) -> None:
    """
    Takes in the results of the archive_channels function.
    Writes them out to RESULTS_FILE.

    :param team_id: Slack instance team ID.
    :param results: List of results from archive_channels().
    :return: None
    """
    try:
        with open(
                RESULTS_FILE, mode='w', encoding='utf-8', newline=''
        ) as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            headers = ['Channel ID', 'Channel Name', 'Users', 'Successfully Archived?', 'Channel Link']
            writer.writerow(headers)

            for result in results:
                channel_id = result['id']
                channel_name = result['name']
                channel_users = '\n'.join(result['users'])
                channel_link = f'https://app.slack.com/client/{team_id}/{channel_id}'

                if result['archived']:
                    archived = 'Yes'
                else:
                    archived = 'No'

                row = [
                    channel_id,
                    channel_name,
                    channel_users,
                    archived,
                    channel_link,
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

    return None


def archive_channels(channels: list) -> None:
    """
    - Takes in a list of channel objects.
    - Checks to see if they should be archived.
    - Archives them if appropriate.
    - Writes out the results to RESULTS_FILE

    :param channels: Channel objects
    :return: None
    """
    results = []
    team_id = api_call('/auth.test')['team_id']

    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['name']
        is_channel = channel['is_channel']  # As opposed to a DM, group, etc.

        if is_channel and not is_channel_exempt(channel):
            if is_channel_active(channel_id):
                continue
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
                try:
                    send_message(
                        channel=channel_name,
                        msg=archived_message.format(
                            days=DAYS_INACTIVE,
                            channel_link=f'https://app.slack.com/client/{team_id}/{channel_id}'
                        )
                    )
                except Exception as e:
                    print(f'Error sending message to {channel_name}.')
                    logging.warning(f'Error sending message to {channel_name}.')
                    logging.warning(e)

                response = api_call(
                    method='POST',
                    endpoint=endpoint,
                    json_data={"channel": channel_id}
                )

                if response.get('error'):
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

    team_id = api_call('/auth.test')['team_id']
    write_results(team_id, results)
    return None


def send_admin_report(
        channel_name: str = DEFAULT_NOTIFICATION_CHANNEL
) -> None:
    """
    Sends a message indicating if this was a dry run or not.
    Sends the RESULTS_FILE to the specified channel.

    :return: None
    """
    print('Sending admin report...')
    if DRY_RUN:
        send_message('DRY RUN Results:', channel_name)
    else:
        send_message('NOT a dry run. Results:')

    if "#" in channel_name:
        name = channel_name[1:]
    else:
        name = channel_name

    channels = get_channels()
    channel_id = ''

    for channel in channels:
        if channel['name'] == name:
            channel_id = channel['id']
            break

    if not channel_id:
        print('Error getting channel ID for specified channel.')
        print('See log for details.')
        print(f'Results file name: {RESULTS_FILE}')
        return None

    try:
        endpoint = '/files.upload'
        payload = {
            'token': API_TOKEN,
            'channels': channel_id,
            'title': 'Autoarchive Results',
            'filename': RESULTS_FILE,
            'filetype': 'csv',
        }
        with open(RESULTS_FILE, 'rb') as f:
            files = {'file': (RESULTS_FILE, f)}
            api_call(
                method='POST', endpoint=endpoint, charset='', files=files,
                content_type='multipart/form-data', payload=payload
            )
    except Exception as e:
        print('Error reading file. See log for details.')
        print(f'Results file name: {RESULTS_FILE}')
        logging.warning(e)

    return None


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

    all_channels = get_channels()
    join_channels(all_channels)
    archive_channels(all_channels)
    send_admin_report()

    logging.info('Script completed successfully.')
    logging.info(log_end)
