# -*- coding: utf-8 -*-

dry_run_message = 'DRY RUN ONLY'

exempt_keyword = ''

archive_message = '''This channel is scheduled to be archived on {date} due to inactivity.
To exempt this channel from being, add {exempt_keyword} to the channel's description.
An archived channel can be un-archived at any time.
'''

archived_message = '''This channel has been archived. To un-archive:'''

api_error = 'Error making an API call. See error for details.'

stars = "*" * 80  # Used for logging and printing to separate sections
dashes = "-" * 80  # Used for logging and printing to separate sections

log_end = f'End of run.\n{stars}\n'
