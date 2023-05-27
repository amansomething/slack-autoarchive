# -*- coding: utf-8 -*-

archived_message = '''This channel has been archived due to inactivity for more than {days} days.
To un-archive, navigate to: {channel_link}
See <https://slack.com/help/articles/213185307-Archive-or-delete-a-channel> for details.
'''

api_error = 'Error making an API call. See log for details.'

stars = "*" * 80  # Used for logging and printing to separate sections
dashes = "-" * 80  # Used for logging and printing to separate sections

users_logging_template = '''

Members of: {channel_name}:
-----------------------------
{users}
-----------------------------
'''

log_end = f'End of run.\n{stars}\n'
